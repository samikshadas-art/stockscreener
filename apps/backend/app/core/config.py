from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "StockScreener API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stockscreener"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/stockscreener"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    SECRET_KEY: str = "changeme-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Supabase (optional)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # External Data APIs
    ALPHA_VANTAGE_KEY: str = ""
    TWELVE_DATA_KEY: str = ""
    POLYGON_KEY: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://yourdomain.com",
    ]

    # Cache TTLs (seconds)
    CACHE_TTL_LIVE_PRICE: int = 15
    CACHE_TTL_TECHNICALS: int = 3600
    CACHE_TTL_FUNDAMENTALS: int = 86400
    CACHE_TTL_SCREENER: int = 30
    CACHE_TTL_STOCK_OVERVIEW: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
