"""Framework-independent domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    tenant_id: str
    title: str
    source: str
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class Chunk:
    id: str
    tenant_id: str
    document_id: str
    document_title: str
    source: str
    ordinal: int
    content: str
    embedding: tuple[float, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    chunk: Chunk
    semantic_score: float
    lexical_score: float
    score: float


@dataclass(frozen=True, slots=True)
class GenerationOutput:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    abstained: bool = False


@dataclass(frozen=True, slots=True)
class AnswerCitation:
    number: int
    document_id: str
    chunk_id: str
    title: str
    source: str
    excerpt: str
    relevance_score: float


@dataclass(frozen=True, slots=True)
class QueryResult:
    answer: str
    citations: tuple[AnswerCitation, ...]
    abstained: bool
    model: str | None
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class IngestionResult:
    document: Document
    chunk_count: int
    created: bool
