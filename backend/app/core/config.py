from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-Agent Research Assistant"
    app_env: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = "/api/v1"
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )
    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    vector_store_path: Path = Path("data/vector_store.json")
    memory_db_path: Path = Path("data/memory.db")
    log_file_path: Path = Path("data/logs/app.log")
    search_provider: str = Field(
        default="arxiv,semantic_scholar,crossref",
        alias="SCHOLARLY_SEARCH_PROVIDERS",
    )
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")
    default_max_search_results: int = Field(default=5, alias="DEFAULT_MAX_SEARCH_RESULTS")
    retrieval_top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")
    max_research_iterations: int = Field(default=2, alias="MAX_RESEARCH_ITERATIONS")
    request_timeout_seconds: float = 10.0
    embedding_provider: str = Field(default="hash", alias="EMBEDDING_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    semantic_scholar_api_key: str | None = Field(default=None, alias="SEMANTIC_SCHOLAR_API_KEY")
    crossref_mailto: str | None = Field(default=None, alias="CROSSREF_MAILTO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def allowed_upload_suffixes(self) -> set[str]:
        return {".txt", ".md", ".json", ".csv", ".pdf"}

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def search_providers(self) -> list[str]:
        return [
            provider.strip().lower()
            for provider in self.search_provider.split(",")
            if provider.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
