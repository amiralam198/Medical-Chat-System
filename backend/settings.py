from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    ncbi_email: str = "your.email@example.com"
    pubmed_timeout_s: float = 50.0
    pubmed_retmax: int = 14
    max_context_sources: int = 6
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    api_version: str = "2.1.0"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("pubmed_retmax")
    @classmethod
    def clamp_retmax(cls, value: int) -> int:
        return max(1, min(int(value), 50))

    @field_validator("max_context_sources")
    @classmethod
    def clamp_context_sources(cls, value: int) -> int:
        return max(1, min(int(value), 8))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
