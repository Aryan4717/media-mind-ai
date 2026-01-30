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
    
    # AI/ML Services
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-ada-002"
    
    # Transcription Service
    whisper_model: str = "base"  # Options: tiny, base, small, medium, large
    use_openai_whisper_api: bool = False  # Use OpenAI API instead of local Whisper
    transcription_language: str = ""  # Auto-detect if empty, or specify language code (e.g., "en", "es")
    transcription_task: str = "transcribe"  # "transcribe" or "translate"
    
    # Document Processing
    chunk_size: int = 1000  # Characters per chunk
    chunk_overlap: int = 200  # Character overlap between chunks
    chunking_strategy: str = "fixed"  # "fixed" or "sentence" or "paragraph"
    
    # Vector Search
    faiss_index_path: str = "faiss_index"  # Path to store FAISS index
    search_top_k: int = 5  # Number of results to return in semantic search
    embedding_batch_size: int = 100  # Batch size for generating embeddings
    
    # LLM / Q&A
    llm_model: str = "gpt-4o-mini"  # LLM model for Q&A
    llm_temperature: float = 0.7  # Temperature for LLM generation
    rag_context_chunks: int = 5  # Number of chunks to use as context for RAG
    rag_max_context_length: int = 4000  # Maximum context length in tokens
    
    # File Storage
    max_file_size_mb: int = 100
    allowed_file_types: List[str] = [
        "pdf", "txt", "docx", "pptx", "xlsx",
        "jpg", "jpeg", "png", "gif", "mp4", "mp3", "wav"
    ]
    
    # Security
    secret_key: str = ""  # Must be set via SECRET_KEY environment variable
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

