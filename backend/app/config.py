"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/trading_platform"

    # Fyers API
    FYERS_CLIENT_ID: str = ""
    FYERS_SECRET: str = ""
    FYERS_REDIRECT_URI: str = "http://127.0.0.1:8000/api/auth/fyers/callback"

    # News
    NEWSAPI_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "change-me-in-production"

    # Application
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SCAN_INTERVAL_SECONDS: int = 60
    MARKET_OPEN_TIME: str = "09:15"
    MARKET_CLOSE_TIME: str = "15:30"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
