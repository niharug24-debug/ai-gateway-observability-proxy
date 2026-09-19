"""
SQLAlchemy ORM Model for API Request & Observability Logs.
Persists every interaction passing through the gateway.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    Text,
    Index
)
from app.core.database import Base


class APILog(Base):
    """
    Detailed audit log of every LLM completion request handled by the gateway.
    """
    __tablename__ = "api_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Model & Payload info
    model = Column(String(64), nullable=False, index=True)
    prompt_hash = Column(String(64), nullable=False, index=True)
    
    # Token Metrics
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Latency & Financial Metrics
    latency_ms = Column(Float, nullable=False)
    cost_usd = Column(Float, default=0.0, nullable=False)
    cost_saved_usd = Column(Float, default=0.0, nullable=False)
    
    # Gateway Flags
    cache_status = Column(String(16), nullable=False, index=True)  # HIT, MISS, BYPASS
    pii_detected = Column(Boolean, default=False, nullable=False, index=True)
    pii_types_found = Column(JSON, default=list, nullable=False)   # e.g. ["EMAIL", "CREDIT_CARD"]
    
    # HTTP Status & Metadata
    status_code = Column(Integer, default=200, nullable=False)
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    # Optional sanitized preview (first 200 chars for dashboard preview)
    prompt_preview = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_api_logs_time_cache", "timestamp", "cache_status"),
        Index("ix_api_logs_model_time", "model", "timestamp"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "model": self.model,
            "prompt_hash": self.prompt_hash,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "cost_usd": round(self.cost_usd, 6),
            "cost_saved_usd": round(self.cost_saved_usd, 6),
            "cache_status": self.cache_status,
            "pii_detected": self.pii_detected,
            "pii_types_found": self.pii_types_found,
            "status_code": self.status_code,
            "prompt_preview": self.prompt_preview
        }
