"""
Pydantic Schemas for Observability Dashboard Analytics & Metrics.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OverviewMetricsResponse(BaseModel):
    total_requests: int
    cache_hits: int
    cache_misses: int
    tokens_saved: int
    cache_hit_ratio: float
    pii_incidents_blocked: int
    total_spend_usd: float
    total_savings_usd: float
    avg_latency_ms: float


class LogItemResponse(BaseModel):
    id: str
    timestamp: str
    model: str
    prompt_hash: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    cost_saved_usd: float
    cache_status: str
    pii_detected: bool
    pii_types_found: List[str]
    status_code: int
    prompt_preview: Optional[str] = None


class PaginatedLogsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[LogItemResponse]


class ChartDataPoint(BaseModel):
    timestamp: str
    requests: int
    avg_latency_ms: float
    cost_usd: float
    saved_usd: float


class ChartDataResponse(BaseModel):
    points: List[ChartDataPoint]
    model_breakdown: Dict[str, int]
