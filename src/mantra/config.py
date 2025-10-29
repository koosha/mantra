"""
Configuration management for Mantra using Pydantic Settings.
Centralizes all environment variables with validation and type checking.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional
from pathlib import Path


class MantraSettings(BaseSettings):
    """
    Centralized configuration for Mantra application.

    All settings can be configured via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # OpenAI Configuration
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key (required)"
    )

    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model for vector generation"
    )

    llm_model: str = Field(
        default="gpt-4o",
        description="OpenAI LLM model for response generation"
    )

    # FAISS Index Configuration
    faiss_index_path: Path = Field(
        default=Path("./faiss_index"),
        description="Path to FAISS index directory"
    )

    # Data Configuration
    data_dir: Path = Field(
        default=Path("./data/cases"),
        description="Directory containing case law data"
    )

    data_file: str = Field(
        default="delaware_cases.json",
        description="Name of the case law JSON file"
    )

    # External API Tokens (Optional)
    courtlistener_api_token: Optional[str] = Field(
        default=None,
        description="CourtListener API token for data extraction"
    )

    cap_api_token: Optional[str] = Field(
        default=None,
        description="Caselaw Access Project (CAP) API token"
    )

    # RAG Configuration
    default_retrieval_k: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Default number of documents to retrieve"
    )

    similarity_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for automatic answers"
    )

    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=2000,
        description="Target size for document chunks"
    )

    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=500,
        description="Overlap between document chunks"
    )

    # Server Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="FastAPI server host"
    )

    api_port: int = Field(
        default=8000,
        ge=1000,
        le=65535,
        description="FastAPI server port"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    @field_validator("faiss_index_path", "data_dir")
    @classmethod
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure directory paths exist or can be created."""
        v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @property
    def data_path(self) -> Path:
        """Get full path to data file."""
        return self.data_dir / self.data_file

    def __repr__(self) -> str:
        """String representation (hiding sensitive data)."""
        return (
            f"MantraSettings("
            f"embedding_model={self.embedding_model}, "
            f"llm_model={self.llm_model}, "
            f"faiss_index_path={self.faiss_index_path}, "
            f"data_dir={self.data_dir})"
        )


# Global settings instance
_settings: Optional[MantraSettings] = None


def get_settings() -> MantraSettings:
    """
    Get the global settings instance.
    Creates it if it doesn't exist (lazy initialization).

    Returns:
        MantraSettings instance
    """
    global _settings
    if _settings is None:
        _settings = MantraSettings()
    return _settings


def reload_settings() -> MantraSettings:
    """
    Force reload settings from environment.
    Useful for testing or when environment changes.

    Returns:
        New MantraSettings instance
    """
    global _settings
    _settings = MantraSettings()
    return _settings


# Convenience accessor
settings = get_settings()
