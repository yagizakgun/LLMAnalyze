from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Centralized application configuration. Loads from .env automatically."""

    # LLM Providers
    openai_api_key: str = ""
    gemini_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # News Providers
    newsapi_key: str = ""

    # Market Data
    alpha_vantage_key: str = ""

    # App Settings
    env: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Cache Settings
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    # Security
    secret_key: str = "your_secret_key_change_in_production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Returns a cached Settings instance."""
    return Settings()
