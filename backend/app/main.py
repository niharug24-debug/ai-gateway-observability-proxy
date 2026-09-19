"""
FastAPI Application Entrypoint.
Initializes lifespan events (Database & Redis), CORS middleware, and API routers.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.database import init_db
from app.core.cache_manager import cache_manager
from app.api.proxy import proxy_router
from app.api.metrics import metrics_router

# Configure root logger
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s : %(message)s"
)
logger = logging.getLogger("ai_gateway.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown procedures.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode...")
    
    # 1. Initialize Database Tables
    try:
        await init_db()
        logger.info("Persistent storage initialized.")
    except Exception as e:
        logger.error(f"Critical error during database initialization: {e}")

    # 2. Connect to In-Memory / Redis Cache Layer
    try:
        await cache_manager.initialize()
    except Exception as e:
        logger.warning(f"Cache initialization warning: {e}")

    yield

    # Shutdown
    logger.info("Shutting down AI Gateway...")
    await cache_manager.close()
    logger.info("Gateway shutdown complete.")


# Create FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Enterprise-grade AI Gateway, Semantic Prompt Hash-Caching, "
        "Automated PII Masking, and Real-Time Token Observability Proxy."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(proxy_router)
app.include_router(metrics_router)


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for container orchestrators and load balancers.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "cache_connected": cache_manager.is_connected,
        "pii_redaction_active": settings.PII_REDACTION_ENABLED
    }


@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint with service overview and quick navigation links.
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": "/docs",
        "proxy_endpoint": "/v1/chat/completions",
        "analytics_endpoint": "/v1/analytics/overview"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
