"""Ports that keep domain logic independent from infrastructure vendors."""

from __future__ import annotations

from typing import Protocol, Sequence

from knowledge_assistant.domain.models import (
    Chunk,
    Document,
    GenerationOutput,
    RetrievalHit,
)


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class AnswerGenerator(Protocol):
    def generate(
        self,
        question: str,
        retrieved_chunks: Sequence[RetrievalHit],
    ) -> GenerationOutput: ...


class KnowledgeRepository(Protocol):
    def initialize(self) -> None: ...

    def close(self) -> None: ...

    def find_document_by_hash(
        self, tenant_id: str, content_hash: str
    ) -> Document | None: ...

    def add_document(self, document: Document, chunks: Sequence[Chunk]) -> None: ...

    def list_documents(self, tenant_id: str) -> list[Document]: ...

    def delete_document(self, tenant_id: str, document_id: str) -> bool: ...

    def search(
        self,
        tenant_id: str,
        query: str,
        query_embedding: Sequence[float],
        top_k: int,
        semantic_weight: float,
    ) -> list[RetrievalHit]: ...
