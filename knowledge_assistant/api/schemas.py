"""Versioned HTTP request and response contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IngestDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=300)
    source: str = Field(min_length=1, max_length=2_000)
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    id: str
    title: str
    source: str
    metadata: dict[str, Any]
    created_at: datetime


class IngestDocumentResponse(BaseModel):
    document: DocumentResponse
    chunk_count: int
    created: bool


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=10_000)
    top_k: int | None = Field(default=None, ge=1, le=100)


class CitationResponse(BaseModel):
    number: int
    document_id: str
    chunk_id: str
    title: str
    source: str
    excerpt: str
    relevance_score: float


class UsageResponse(BaseModel):
    input_tokens: int | None
    output_tokens: int | None


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    abstained: bool
    model: str | None
    usage: UsageResponse


class HealthResponse(BaseModel):
    status: str
