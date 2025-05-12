"""
Application configuration
"""

import secrets
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import (
    AnyHttpUrl,
    Field,
    field_validator,
)
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # API settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "aiplatform"
    DEBUG: bool = False

    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    ALLOWED_HOSTS: List[str] = ["*"]

    # Security settings
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_hex(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database settings
    DATABASE_URL: str = "postgresql://admin:admin@localhost:5432/aiplatform"
    SQL_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Cache settings
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 300  # 5 minutes

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Llama Parse Creds
    LLAMA_CLOUD_API_KEY: str = ""

    # Azure OpenAI settings
    AZURE_API_KEY: str = ""
    AZURE_MODEL: str = "gpt-4o-mini"
    AZURE_DEPLOYMENT: str = ""
    AZURE_ENDPOINT: str = ""
    AZURE_VERSION: str = "2025-01-01-preview"
    AZURE_EMBEDDING_API_KEY: str = ""
    AZURE_EMBEDDING_DEPLOYMENT: str = ""
    AZURE_EMBEDDING_ENDPOINT: str = ""
    AZURE_EMBEDDING_API_VERSION: str = "2025-01-01-preview"

    # Weaviate settings
    WEAVIATE_API_KEY: str = ""
    WEAVIATE_HTTP_HOST: str = ""
    WEAVIATE_GRPC_HOST: str = ""
    WEAVIATE_HTTP_PORT: int = 443

    # Pydantic v2 uses model_config instead of Config class
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings instance
    """
    return Settings()
