from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "Crypto Backtester"
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-prod")
    JWT_EXPIRE_MIN: int = int(os.getenv("JWT_EXPIRE_MIN", "30"))
    JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "14"))
    ACCESS_TOKEN_COOKIE_NAME: str = os.getenv("ACCESS_TOKEN_COOKIE_NAME", "access_token")
    REFRESH_TOKEN_COOKIE_NAME: str = os.getenv("REFRESH_TOKEN_COOKIE_NAME", "refresh_token")

    # Database & Cache
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@postgres:5432/postgres",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] | List[str] = [
        # For local docker by default
        "http://localhost:5173",
        "http://localhost:3000",
        "http://frontend:80",
        "http://frontend",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Data sources
    BINANCE_MARKET: str = os.getenv("BINANCE_MARKET", "spot")
    CCXT_RATE_LIMIT_MS: int = int(os.getenv("CCXT_RATE_LIMIT_MS", "500"))

    # Backtesting defaults
    DEFAULT_TIMEFRAME: str = os.getenv("DEFAULT_TIMEFRAME", "1h")
    MAX_LOOKBACK_YEARS: int = int(os.getenv("MAX_LOOKBACK_YEARS", "3"))


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


settings = get_settings()
