"""
Async Database Engine and Session Management using SQLAlchemy 2.0.
Supports PostgreSQL (via asyncpg) and SQLite (via aiosqlite).
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from app.config import settings

logger = logging.getLogger("ai_gateway.database")

# Create declarative base for all ORM models
Base = declarative_base()

# Configure the Async Engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an active async database session
    and guarantees proper commit/rollback and closure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session rolled back due to error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initializes database tables on application startup.
    Creates all tables defined in models if they don't already exist.
    """
    try:
        # Import models so Base metadata is populated
        from app.models.api_log import APILog # noqa
        from app.models.cost_metric import CostMetric # noqa

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified and initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise
