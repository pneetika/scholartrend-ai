from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.models.schemas import LLMProviderName


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="ScholarTrend AI", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    reports_dir: Path = Field(default=Path("data/reports"), alias="REPORTS_DIR")
    runs_db_path: Path = Field(default=Path("data/scholartrend.db"), alias="RUNS_DB_PATH")
    cache_db_path: Path = Field(default=Path("data/cache.db"), alias="CACHE_DB_PATH")
    log_file_path: Path = Field(default=Path("data/logs/scholartrend.log"), alias="LOG_FILE_PATH")

    llm_provider: LLMProviderName = Field(default=LLMProviderName.MOCK, alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen3:8b", alias="OLLAMA_MODEL")

    embedding_provider: str = Field(default="sentence_transformers", alias="EMBEDDING_PROVIDER")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    ollama_embedding_model: str = Field(default="embeddinggemma", alias="OLLAMA_EMBEDDING_MODEL")
    sentence_transformer_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="SENTENCE_TRANSFORMER_MODEL",
    )
    vector_backend: str = Field(default="chroma", alias="VECTOR_BACKEND")
    chroma_persist_dir: Path = Field(default=Path("data/chroma"), alias="CHROMA_PERSIST_DIR")

    request_timeout_seconds: int = Field(default=20, alias="REQUEST_TIMEOUT_SECONDS")
    max_results_per_source: int = Field(default=20, alias="MAX_RESULTS_PER_SOURCE")
    default_paper_limit: int = Field(default=12, alias="DEFAULT_PAPER_LIMIT")
    default_time_range: str = Field(default="1y", alias="DEFAULT_TIME_RANGE")
    mock_external_apis: bool = Field(default=False, alias="MOCK_EXTERNAL_APIS")

    semantic_scholar_api_key: Optional[str] = Field(default=None, alias="SEMANTIC_SCHOLAR_API_KEY")
    openalex_api_key: Optional[str] = Field(default=None, alias="OPENALEX_API_KEY")
    ncbi_api_key: Optional[str] = Field(default=None, alias="NCBI_API_KEY")
    crossref_mailto: Optional[str] = Field(default=None, alias="CROSSREF_MAILTO")
    streamlit_api_base_url: str = Field(
        default="http://127.0.0.1:8000/api/v1",
        alias="STREAMLIT_API_BASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled_sources(self) -> List[str]:
        return ["arxiv", "semantic_scholar", "crossref", "openalex", "pubmed", "papers_with_code"]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
