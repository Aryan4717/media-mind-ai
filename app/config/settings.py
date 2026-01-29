"""Application settings and configuration."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Media Mind AI"
    environment: str = "development"
    debug: bool = False
    api_version: str = "v1"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    database_url: str = ""  # Defaults to SQLite if empty
    
    # AI/ML Services (for future use)
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-ada-002"
    
    # File Storage
    max_file_size_mb: int = 100
    allowed_file_types: List[str] = [
        "pdf", "txt", "docx", "pptx", "xlsx",
        "jpg", "jpeg", "png", "gif", "mp4", "mp3", "wav"
    ]
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

