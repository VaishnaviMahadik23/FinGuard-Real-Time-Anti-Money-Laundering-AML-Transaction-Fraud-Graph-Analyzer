"""
Application configuration — loaded from environment / .env file.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # App
    APP_NAME: str = "FinGuard"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    API_V1_PREFIX: str = "/api/v1"

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "finguard_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # ML Models
    MODEL_DIR: str = "./ml_models"
    ISOLATION_FOREST_CONTAMINATION: float = 0.08
    AUTOENCODER_THRESHOLD: float = 0.42
    RETRAIN_INTERVAL_HOURS: int = 24

    # Risk thresholds
    RISK_HIGH_THRESHOLD: float = 0.65
    RISK_MEDIUM_THRESHOLD: float = 0.35
    ALERT_AMOUNT_USD: float = 10_000.0

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
