"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated configuration for the production API.

    Environment variables use the ``KA_`` prefix except ``OPENAI_API_KEY``,
    which keeps the conventional OpenAI name.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="KA_",
        extra="ignore",
    )

    environment: str = "development"
    database_path: Path = Path("data/knowledge.db")
    tenant_api_keys: str = ""
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    chat_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = Field(default=800, ge=100)
    chunk_overlap: int = Field(default=100, ge=0)
    default_top_k: int = Field(default=5, ge=1, le=100)
    maximum_top_k: int = Field(default=20, ge=1, le=100)
    minimum_relevance_score: float = 0.20
    semantic_weight: float = 0.75
    maximum_document_characters: int = Field(default=1_000_000, ge=1)
    embedding_batch_size: int = Field(default=256, ge=1, le=2_048)
    embedding_batch_max_tokens: int = Field(default=250_000, ge=1, le=300_000)
    openai_store_responses: bool = False

    @field_validator("minimum_relevance_score", "semantic_weight")
    @classmethod
    def validate_ratio(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("value must be between 0 and 1")
        return value

    @model_validator(mode="after")
    def validate_cross_field_invariants(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.default_top_k > self.maximum_top_k:
            raise ValueError("default_top_k cannot exceed maximum_top_k")
        return self

    def api_keys_by_tenant(self) -> dict[str, str]:
        """Parse ``tenant=key`` pairs without accepting ambiguous entries."""
        parsed: dict[str, str] = {}
        for item in self.tenant_api_keys.split(","):
            item = item.strip()
            if not item:
                continue
            tenant_id, separator, api_key = item.partition("=")
            tenant_id = tenant_id.strip()
            api_key = api_key.strip()
            if separator != "=" or not tenant_id or not api_key:
                raise ValueError(
                    "KA_TENANT_API_KEYS must contain comma-separated tenant=key pairs"
                )
            if tenant_id in parsed:
                raise ValueError(
                    f"Duplicate API key configuration for tenant {tenant_id!r}"
                )
            parsed[tenant_id] = api_key
        return parsed
