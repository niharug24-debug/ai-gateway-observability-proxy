"""
Transparent Proxy Router for /v1/chat/completions.
Intercepts, sanitizes PII, checks Redis hash-cache, forwards to upstream,
and logs latency, cost, and token metrics.
"""

import time
import uuid
import logging
from typing import Dict, Any, List
import httpx
from fastapi import APIRouter, Request, Response, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db, AsyncSessionLocal
from app.core.pii_sanitizer import PIISanitizer
from app.core.cache_manager import cache_manager
from app.core.cost_calculator import CostCalculator
from app.models.api_log import APILog
from app.models.cost_metric import CostMetric
from app.schemas.openai_schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionMessage,
    UsageInfo
)

logger = logging.getLogger("ai_gateway.proxy")
proxy_router = APIRouter(prefix="/v1", tags=["LLM Proxy"])


async def record_audit_log(
    model: str,
    prompt_hash: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: float,
    cost_usd: float,
    cost_saved_usd: float,
    cache_status: str,
    pii_detected: bool,
    pii_types: List[str],
    status_code: int,
    client_ip: str,
    prompt_preview: str
) -> None:
    """
    Background worker that persists API interaction metrics into PostgreSQL.
    Runs asynchronously outside the critical request path to guarantee low latency.
    """
    try:
        async with AsyncSessionLocal() as session:
            log_entry = APILog(
                model=model,
                prompt_hash=prompt_hash,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                cost_saved_usd=cost_saved_usd,
                cache_status=cache_status,
                pii_detected=pii_detected,
                pii_types_found=pii_types,
                status_code=status_code,
                client_ip=client_ip,
                prompt_preview=prompt_preview[:200] if prompt_preview else ""
            )
            session.add(log_entry)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to record API audit log: {e}")


@proxy_router.post("/chat/completions")
async def chat_completions_proxy(
    payload: ChatCompletionRequest,
    raw_request: Request,
    response: Response,
    background_tasks: BackgroundTasks
):
    """
    Core transparent proxy endpoint.
    1. Intercepts incoming standard LLM requests.
    2. Runs PII sanitization pipeline.
    3. Computes SHA-256 prompt hash.
    4. Checks Redis cache (Sub-10ms HIT response).
    5. On MISS, forwards to upstream provider, caches response, and records metrics.
    """
    start_time = time.perf_counter()
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"

    # Step 1: PII Sanitization Pipeline
    raw_messages = [m.model_dump() for m in payload.messages]
    sanitized_messages = raw_messages
    pii_detected = False
    redaction_count = 0
    pii_types: List[str] = []

    if settings.PII_REDACTION_ENABLED:
        sanitized_messages, redaction_count, pii_types = PIISanitizer.sanitize_messages(raw_messages)
        if redaction_count > 0:
            pii_detected = True
            logger.info(f"PII intercepted: {redaction_count} items redacted. Types: {pii_types}")

    # Generate prompt preview for observability dashboard
    last_user_msg = next((m.get("content", "") for m in reversed(sanitized_messages) if m.get("role") == "user"), "")
    prompt_preview = str(last_user_msg)[:200]

    # Step 2: Compute Deterministic SHA-256 Hash
    prompt_hash = cache_manager.generate_prompt_hash(
        model=payload.model,
        messages=sanitized_messages,
        temperature=payload.temperature
    )

    # Step 3: Check Redis Cache (Target: Sub-10ms)
    cached_data = await cache_manager.get_cached_response(prompt_hash)
    if cached_data:
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        usage_dict = cached_data.get("usage", {})
        prompt_tokens = usage_dict.get("prompt_tokens", 0)
        completion_tokens = usage_dict.get("completion_tokens", 0)
        total_tokens = usage_dict.get("total_tokens", prompt_tokens + completion_tokens)

        cost_saved_usd = CostCalculator.calculate_cost(
            payload.model, prompt_tokens, completion_tokens
        )

        # Update Redis atomic metrics
        await cache_manager.increment_stats(
            is_hit=True,
            tokens_saved=total_tokens,
            pii_detected=pii_detected
        )

        # Asynchronously record to PostgreSQL database
        background_tasks.add_task(
            record_audit_log,
            model=payload.model,
            prompt_hash=prompt_hash,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=0.0,
            cost_saved_usd=cost_saved_usd,
            cache_status="HIT",
            pii_detected=pii_detected,
            pii_types=pii_types,
            status_code=200,
            client_ip=client_ip,
            prompt_preview=prompt_preview
        )

        # Set Gateway Observability Headers
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"
        response.headers["X-Tokens-Saved"] = str(total_tokens)
        response.headers["X-Cost-Saved-USD"] = f"{cost_saved_usd:.6f}"
        response.headers["X-PII-Redacted"] = str(pii_detected)

        return cached_data

    # Step 4: Cache MISS - Forward to Upstream LLM Provider
    upstream_payload = payload.model_dump()
    upstream_payload["messages"] = sanitized_messages

    response_data: Dict[str, Any] = {}
    upstream_api_key = settings.UPSTREAM_API_KEY

    # Check incoming client auth header as fallback
    incoming_auth = raw_request.headers.get("Authorization")
    auth_header = incoming_auth if incoming_auth else (f"Bearer {upstream_api_key}" if upstream_api_key else None)

    # Call real upstream provider if key is available
    if auth_header and not auth_header.endswith("your-openai-or-gemini-api-key-here"):
        try:
            async with httpx.AsyncClient(timeout=settings.UPSTREAM_TIMEOUT_SECONDS) as client:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": auth_header
                }
                upstream_res = await client.post(
                    f"{settings.UPSTREAM_OPENAI_BASE_URL}/chat/completions",
                    json=upstream_payload,
                    headers=headers
                )
                if upstream_res.status_code != 200:
                    logger.error(f"Upstream provider returned status {upstream_res.status_code}: {upstream_res.text}")
                    raise HTTPException(
                        status_code=upstream_res.status_code,
                        detail=f"Upstream Provider Error: {upstream_res.text}"
                    )
                response_data = upstream_res.json()
        except httpx.RequestError as e:
            logger.error(f"Network error contacting upstream provider: {e}")
            raise HTTPException(status_code=502, detail=f"Bad Gateway: Unable to reach upstream LLM provider: {str(e)}")
    else:
        # Step 4b: Offline Simulation Mode (Ensures zero-setup testing for developers)
        if settings.SIMULATE_UPSTREAM_IF_NO_KEY:
            logger.info("No upstream API key provided. Generating simulated completion for testing.")
            prompt_tokens_est = CostCalculator.estimate_tokens_from_messages(sanitized_messages)
            completion_text = (
                f"[AI Gateway Simulation] Processed sanitized prompt. "
                f"Your request was intercepted, validated for PII (detected: {pii_detected}), "
                f"and cached for future sub-10ms retrieval."
            )
            completion_tokens_est = CostCalculator.estimate_tokens_from_text(completion_text)
            
            response_data = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": payload.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": completion_text
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens_est,
                    "completion_tokens": completion_tokens_est,
                    "total_tokens": prompt_tokens_est + completion_tokens_est
                }
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="Missing UPSTREAM_API_KEY. Please set UPSTREAM_API_KEY in .env or pass Authorization header."
            )

    # Step 5: Calculate Observability & Financial Metrics
    latency_ms = (time.perf_counter() - start_time) * 1000.0
    usage_info = response_data.get("usage", {})
    prompt_tokens = usage_info.get("prompt_tokens", 0)
    completion_tokens = usage_info.get("completion_tokens", 0)
    total_tokens = usage_info.get("total_tokens", prompt_tokens + completion_tokens)

    cost_usd = CostCalculator.calculate_cost(payload.model, prompt_tokens, completion_tokens)

    # Step 6: Store in Redis Cache for future sub-10ms hits
    await cache_manager.save_cached_response(
        prompt_hash=prompt_hash,
        response_data=response_data,
        ttl_seconds=settings.CACHE_TTL_SECONDS
    )

    # Increment Redis stats
    await cache_manager.increment_stats(
        is_hit=False,
        tokens_saved=0,
        pii_detected=pii_detected
    )

    # Asynchronously record to PostgreSQL database
    background_tasks.add_task(
        record_audit_log,
        model=payload.model,
        prompt_hash=prompt_hash,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        cost_saved_usd=0.0,
        cache_status="MISS",
        pii_detected=pii_detected,
        pii_types=pii_types,
        status_code=200,
        client_ip=client_ip,
        prompt_preview=prompt_preview
    )

    # Set Response Headers
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"
    response.headers["X-Cost-USD"] = f"{cost_usd:.6f}"
    response.headers["X-PII-Redacted"] = str(pii_detected)

    return response_data
