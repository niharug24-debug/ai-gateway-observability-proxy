"""
Semantic Prompt Hash-Caching Layer using Redis (with graceful in-memory fallback).
Computes deterministic SHA-256 digests of prompts to provide sub-10ms cached answers
and track aggregate token savings.
"""

import hashlib
import json
import logging
import time
from typing import Optional, Dict, Any, List
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False
from app.config import settings

logger = logging.getLogger("ai_gateway.cache")


class CacheManager:
    """
    Manages prompt hash generation, Redis persistence, sub-10ms retrieval,
    and distributed atomic counters.
    """
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self._in_memory_cache: Dict[str, Dict[str, Any]] = {}
        self._in_memory_counters: Dict[str, int] = {
            "tokens_saved": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "pii_incidents": 0
        }
        self.is_connected: bool = False

    async def initialize(self) -> None:
        """Establishes connection to Redis pool with timeout protection."""
        if not REDIS_AVAILABLE:
            self.is_connected = False
            self.redis_client = None
            logger.info("Redis package not installed. Running in high-speed in-memory cache mode.")
            return

        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2.0
            )
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Connected to Redis cache successfully.")
        except Exception as e:
            self.is_connected = False
            self.redis_client = None
            logger.warning(
                f"Redis unavailable ({e}). Using high-speed in-memory cache fallback."
            )

    async def close(self) -> None:
        """Closes the Redis connection pool."""
        if self.redis_client:
            await self.redis_client.close()

    @staticmethod
    def generate_prompt_hash(
        model: str,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = 1.0,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Creates a deterministic SHA-256 signature for the request.
        Includes model name, temperature, and sanitized message history.
        """
        canonical_representation = {
            "model": model.lower().strip(),
            "temperature": round(float(temperature or 1.0), 2),
            "messages": [
                {
                    "role": m.get("role", "").strip(),
                    "content": m.get("content", "").strip() if isinstance(m.get("content"), str) else str(m.get("content"))
                }
                for m in messages
            ]
        }
        if extra_params:
            canonical_representation["extra"] = extra_params

        serialized = json.dumps(canonical_representation, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def get_cached_response(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached OpenAI completion if available.
        Target latency: < 10ms.
        """
        cache_key = f"cache:prompt:{prompt_hash}"
        
        # 1. Try Redis
        if self.is_connected and self.redis_client:
            try:
                cached_str = await self.redis_client.get(cache_key)
                if cached_str:
                    return json.loads(cached_str)
            except Exception as e:
                logger.error(f"Error fetching from Redis: {e}")

        # 2. In-Memory Fallback
        entry = self._in_memory_cache.get(cache_key)
        if entry:
            if entry["expires_at"] > time.time():
                return entry["data"]
            else:
                del self._in_memory_cache[cache_key]

        return None

    async def save_cached_response(
        self, prompt_hash: str, response_data: Dict[str, Any], ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Stores an LLM completion payload against the prompt hash with a TTL.
        """
        ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
        cache_key = f"cache:prompt:{prompt_hash}"
        serialized = json.dumps(response_data)

        # 1. Save to Redis
        if self.is_connected and self.redis_client:
            try:
                await self.redis_client.set(cache_key, serialized, ex=ttl)
                return
            except Exception as e:
                logger.error(f"Error writing to Redis: {e}")

        # 2. Save to In-Memory
        self._in_memory_cache[cache_key] = {
            "data": response_data,
            "expires_at": time.time() + ttl
        }

    async def increment_stats(
        self,
        is_hit: bool,
        tokens_saved: int = 0,
        pii_detected: bool = False
    ) -> None:
        """
        Atomically increments global observability counters.
        """
        if self.is_connected and self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr("stats:total_requests")
                if is_hit:
                    pipe.incr("stats:cache_hits")
                    if tokens_saved > 0:
                        pipe.incrby("stats:tokens_saved", tokens_saved)
                else:
                    pipe.incr("stats:cache_misses")
                if pii_detected:
                    pipe.incr("stats:pii_incidents")
                await pipe.execute()
                return
            except Exception as e:
                logger.error(f"Error incrementing Redis counters: {e}")

        # In-Memory counter fallback
        self._in_memory_counters["total_requests"] += 1
        if is_hit:
            self._in_memory_counters["cache_hits"] += 1
            self._in_memory_counters["tokens_saved"] += tokens_saved
        else:
            self._in_memory_counters["cache_misses"] += 1
        if pii_detected:
            self._in_memory_counters["pii_incidents"] += 1

    async def get_overview_stats(self) -> Dict[str, Any]:
        """
        Fetches current global metrics for the observability dashboard.
        """
        if self.is_connected and self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.get("stats:total_requests")
                pipe.get("stats:cache_hits")
                pipe.get("stats:cache_misses")
                pipe.get("stats:tokens_saved")
                pipe.get("stats:pii_incidents")
                results = await pipe.execute()

                total_req = int(results[0] or 0)
                hits = int(results[1] or 0)
                misses = int(results[2] or 0)
                saved_tokens = int(results[3] or 0)
                pii = int(results[4] or 0)

                hit_rate = (hits / total_req * 100.0) if total_req > 0 else 0.0

                return {
                    "total_requests": total_req,
                    "cache_hits": hits,
                    "cache_misses": misses,
                    "tokens_saved": saved_tokens,
                    "cache_hit_ratio": round(hit_rate, 2),
                    "pii_incidents_blocked": pii
                }
            except Exception as e:
                logger.error(f"Error fetching stats from Redis: {e}")

        # In-memory stats
        total = self._in_memory_counters["total_requests"]
        hits = self._in_memory_counters["cache_hits"]
        hit_rate = (hits / total * 100.0) if total > 0 else 0.0

        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_misses": self._in_memory_counters["cache_misses"],
            "tokens_saved": self._in_memory_counters["tokens_saved"],
            "cache_hit_ratio": round(hit_rate, 2),
            "pii_incidents_blocked": self._in_memory_counters["pii_incidents"]
        }


# Global singleton cache manager
cache_manager = CacheManager()
