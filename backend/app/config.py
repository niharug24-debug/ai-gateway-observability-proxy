"""
Configuration management using Pydantic Settings.
Loads environment variables seamlessly from system environment or .env files.
"""

import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        # App Settings
        PROJECT_NAME: str = "AI Gateway & Token Observability Proxy"
        ENVIRONMENT: str = "development"
        DEBUG: bool = True
        PORT: int = 8000
        HOST: str = "0.0.0.0"

        # Database Configuration
        DATABASE_URL: str = "sqlite+aiosqlite:///./gateway.db"

        # Redis Configuration
        REDIS_URL: str = "redis://localhost:6379/0"
        CACHE_TTL_SECONDS: int = 86400

        # Upstream Provider Configuration
        UPSTREAM_OPENAI_BASE_URL: str = "https://api.openai.com/v1"
        UPSTREAM_API_KEY: Optional[str] = None
        UPSTREAM_TIMEOUT_SECONDS: float = 60.0
        SIMULATE_UPSTREAM_IF_NO_KEY: bool = True

        # Security & PII Redaction
        PII_REDACTION_ENABLED: bool = True

        # CORS
        CORS_ORIGINS: list[str] = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "*"
        ]

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )

    settings = Settings()

except ImportError:
    # Graceful fallback when running in lightweight mode without dependencies installed
    class StandaloneSettings:
        PROJECT_NAME: str = os.getenv("PROJECT_NAME", "AI Gateway & Token Observability Proxy")
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
        PORT: int = int(os.getenv("PORT", "8000"))
        HOST: str = os.getenv("HOST", "0.0.0.0")
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gateway.db")
        REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "86400"))
        UPSTREAM_OPENAI_BASE_URL: str = os.getenv("UPSTREAM_OPENAI_BASE_URL", "https://api.openai.com/v1")
        UPSTREAM_API_KEY: Optional[str] = os.getenv("UPSTREAM_API_KEY", None)
        UPSTREAM_TIMEOUT_SECONDS: float = float(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "60.0"))
        SIMULATE_UPSTREAM_IF_NO_KEY: bool = os.getenv("SIMULATE_UPSTREAM_IF_NO_KEY", "True").lower() in ("true", "1")
        PII_REDACTION_ENABLED: bool = os.getenv("PII_REDACTION_ENABLED", "True").lower() in ("true", "1")
        CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000", "*"]

    settings = StandaloneSettings()
