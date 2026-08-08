from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Configuration loaded from environment variables and an optional .env file."""

    app_name: str = "CodePilot AI API"
    app_env: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
    default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
)
    repository_storage_dir: Path = Path("./data/repositories")
    max_upload_size_mb: int = Field(default=100, ge=1, le=1024)
    max_extracted_size_mb: int = Field(default=500, ge=1, le=4096)
    max_archive_files: int = Field(default=10_000, ge=1, le=100_000)
    chroma_storage_dir: Path = Path("./data/chroma")
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for dependency injection."""

    return Settings()
