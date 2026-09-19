"""
Analytics & Metrics Router for the Next.js Observability Dashboard.
Provides real-time KPIs, historical log feeds, and chart data.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.cache_manager import cache_manager
from app.models.api_log import APILog
from app.schemas.metrics_schema import (
    OverviewMetricsResponse,
    PaginatedLogsResponse,
    LogItemResponse,
    ChartDataResponse,
    ChartDataPoint
)

metrics_router = APIRouter(prefix="/v1/analytics", tags=["Analytics & Observability"])


@metrics_router.get("/overview", response_model=OverviewMetricsResponse)
async def get_overview_metrics(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated real-time metrics, combining Redis counters with DB totals.
    """
    # 1. Fetch live counters from Redis
    stats = await cache_manager.get_overview_stats()

    # 2. Query aggregate financial and latency stats from PostgreSQL
    stmt = select(
        func.count(APILog.id).label("total_records"),
        func.coalesce(func.sum(APILog.cost_usd), 0.0).label("total_spend"),
        func.coalesce(func.sum(APILog.cost_saved_usd), 0.0).label("total_saved"),
        func.coalesce(func.avg(APILog.latency_ms), 0.0).label("avg_latency")
    )
    result = await db.execute(stmt)
    db_metrics = result.first()

    total_records = db_metrics.total_records if db_metrics else 0
    total_spend = float(db_metrics.total_spend) if db_metrics else 0.0
    total_saved = float(db_metrics.total_saved) if db_metrics else 0.0
    avg_latency = float(db_metrics.avg_latency) if db_metrics else 0.0

    # Merge Redis and DB
    total_req = max(stats["total_requests"], total_records)

    return OverviewMetricsResponse(
        total_requests=total_req,
        cache_hits=stats["cache_hits"],
        cache_misses=stats["cache_misses"],
        tokens_saved=stats["tokens_saved"],
        cache_hit_ratio=stats["cache_hit_ratio"],
        pii_incidents_blocked=stats["pii_incidents_blocked"],
        total_spend_usd=round(total_spend, 4),
        total_savings_usd=round(total_saved, 4),
        avg_latency_ms=round(avg_latency, 2)
    )


@metrics_router.get("/logs", response_model=PaginatedLogsResponse)
async def get_api_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    cache_status: Optional[str] = None,
    pii_only: Optional[bool] = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns paginated API audit logs with optional filters for cache status and PII events.
    """
    query = select(APILog)
    count_query = select(func.count(APILog.id))

    if cache_status:
        query = query.where(APILog.cache_status == cache_status.upper())
        count_query = count_query.where(APILog.cache_status == cache_status.upper())

    if pii_only:
        query = query.where(APILog.pii_detected == True)
        count_query = count_query.where(APILog.pii_detected == True)

    # Get total count
    total_res = await db.execute(count_query)
    total_count = total_res.scalar_one()

    # Get paginated items
    offset = (page - 1) * page_size
    query = query.order_by(desc(APILog.timestamp)).offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = [
        LogItemResponse(
            id=log.id,
            timestamp=log.timestamp.isoformat() if log.timestamp else "",
            model=log.model,
            prompt_hash=log.prompt_hash,
            prompt_tokens=log.prompt_tokens,
            completion_tokens=log.completion_tokens,
            total_tokens=log.total_tokens,
            latency_ms=round(log.latency_ms, 2),
            cost_usd=round(log.cost_usd, 6),
            cost_saved_usd=round(log.cost_saved_usd, 6),
            cache_status=log.cache_status,
            pii_detected=log.pii_detected,
            pii_types_found=log.pii_types_found if isinstance(log.pii_types_found, list) else [],
            status_code=log.status_code,
            prompt_preview=log.prompt_preview
        )
        for log in logs
    ]

    return PaginatedLogsResponse(
        total=total_count,
        page=page,
        page_size=page_size,
        items=items
    )


@metrics_router.get("/chart-data", response_model=ChartDataResponse)
async def get_chart_data(db: AsyncSession = Depends(get_db)):
    """
    Provides data points for historical charts (latency trends, dollars saved vs. spent).
    """
    # Fetch latest 50 requests ordered by time
    stmt = (
        select(APILog)
        .order_by(desc(APILog.timestamp))
        .limit(50)
    )
    result = await db.execute(stmt)
    records = list(reversed(result.scalars().all()))

    points = []
    model_breakdown = {}

    for r in records:
        ts = r.timestamp.strftime("%H:%M:%S") if r.timestamp else "N/A"
        points.append(
            ChartDataPoint(
                timestamp=ts,
                requests=1,
                avg_latency_ms=round(r.latency_ms, 2),
                cost_usd=round(r.cost_usd, 6),
                saved_usd=round(r.cost_saved_usd, 6)
            )
        )
        model_breakdown[r.model] = model_breakdown.get(r.model, 0) + 1

    return ChartDataResponse(
        points=points,
        model_breakdown=model_breakdown
    )
