"""
SQLAlchemy ORM Model for Aggregated Cost and Usage Metrics.
Tracks daily rollups by model for fast dashboard time-series plotting.
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    Index,
    UniqueConstraint
)
from app.core.database import Base


class CostMetric(Base):
    """
    Daily aggregated metrics by model for fast dashboard trend analysis.
    """
    __tablename__ = "cost_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False, index=True)
    model = Column(String(64), nullable=False, index=True)
    
    # Request Counts
    total_requests = Column(Integer, default=0, nullable=False)
    cache_hits = Column(Integer, default=0, nullable=False)
    cache_misses = Column(Integer, default=0, nullable=False)
    
    # Token Metrics
    total_prompt_tokens = Column(Integer, default=0, nullable=False)
    total_completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens_saved = Column(Integer, default=0, nullable=False)
    
    # Financials
    total_cost_usd = Column(Float, default=0.0, nullable=False)
    total_saved_usd = Column(Float, default=0.0, nullable=False)
    
    # Security
    pii_redaction_events = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("metric_date", "model", name="uq_metric_date_model"),
        Index("ix_cost_metrics_date_model", "metric_date", "model"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "metric_date": self.metric_date.isoformat() if self.metric_date else None,
            "model": self.model,
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens_saved": self.total_tokens_saved,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "total_saved_usd": round(self.total_saved_usd, 4),
            "pii_redaction_events": self.pii_redaction_events
        }
