"""Use cases for ingestion, retrieval, deletion, and grounded answering."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from uuid import uuid4

from knowledge_assistant.domain.errors import (
    DocumentAlreadyExistsError,
    InvalidGeneratedAnswerError,
    InvalidRequestError,
)
from knowledge_assistant.domain.models import (
    AnswerCitation,
    Chunk,
    Document,
    IngestionResult,
    QueryResult,
    RetrievalHit,
)
from knowledge_assistant.ports import AnswerGenerator, EmbeddingProvider, KnowledgeRepository
from knowledge_assistant.services.chunking import TextChunker


class DocumentTooLargeError(ValueError):
    pass


CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class KnowledgeAssistant:
    """Coordinates domain policies while enforcing a tenant on every operation."""

    def __init__(
        self,
        repository: KnowledgeRepository,
        embeddings: EmbeddingProvider,
        generator: AnswerGenerator,
        chunker: TextChunker,
        *,
        default_top_k: int = 5,
        maximum_top_k: int = 20,
        minimum_relevance_score: float = 0.20,
        semantic_weight: float = 0.75,
        maximum_document_characters: int = 1_000_000,
    ) -> None:
        self._repository = repository
        self._embeddings = embeddings
        self._generator = generator
        self._chunker = chunker
        self._default_top_k = default_top_k
        self._maximum_top_k = maximum_top_k
        self._minimum_relevance_score = minimum_relevance_score
        self._semantic_weight = semantic_weight
        self._maximum_document_characters = maximum_document_characters
        if default_top_k < 1 or maximum_top_k < 1:
            raise ValueError("top_k limits must be greater than zero")
        if default_top_k > maximum_top_k:
            raise ValueError("default_top_k cannot exceed maximum_top_k")

    def ingest(
        self,
        tenant_id: str,
        *,
        title: str,
        source: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        normalized_content = content.strip()
        normalized_title = title.strip()
        normalized_source = source.strip()
        if not normalized_title:
            raise InvalidRequestError("Document title cannot be empty")
        if not normalized_source:
            raise InvalidRequestError("Document source cannot be empty")
        if not normalized_content:
            raise InvalidRequestError("Document content cannot be empty")
        if len(normalized_content) > self._maximum_document_characters:
            raise DocumentTooLargeError(
                f"Document exceeds {self._maximum_document_characters} characters"
            )

        content_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
        existing = self._repository.find_document_by_hash(tenant_id, content_hash)
        if existing is not None:
            return IngestionResult(existing, chunk_count=0, created=False)

        document_id = str(uuid4())
        document = Document(
            id=document_id,
            tenant_id=tenant_id,
            title=normalized_title,
            source=normalized_source,
            content_hash=content_hash,
            metadata=metadata or {},
        )
        texts = self._chunker.split(normalized_content)
        vectors = self._embeddings.embed_documents(texts)
        if len(vectors) != len(texts):
            raise ValueError("Embedding provider returned an unexpected number of vectors")

        chunks = [
            Chunk(
                id=str(uuid4()),
                tenant_id=tenant_id,
                document_id=document_id,
                document_title=document.title,
                source=document.source,
                ordinal=ordinal,
                content=text,
                embedding=tuple(vector),
                metadata=document.metadata,
            )
            for ordinal, (text, vector) in enumerate(zip(texts, vectors, strict=True))
        ]
        try:
            self._repository.add_document(document, chunks)
        except DocumentAlreadyExistsError:
            # Another request may have inserted the same tenant/hash after our
            # initial lookup. Resolve the winner so ingestion stays idempotent.
            concurrent_winner = self._repository.find_document_by_hash(
                tenant_id, content_hash
            )
            if concurrent_winner is None:
                raise
            return IngestionResult(concurrent_winner, chunk_count=0, created=False)
        return IngestionResult(document, chunk_count=len(chunks), created=True)

    def retrieve(
        self, tenant_id: str, question: str, top_k: int | None = None
    ) -> list[RetrievalHit]:
        normalized_question = question.strip()
        if not normalized_question:
            raise InvalidRequestError("Question cannot be empty")
        requested_top_k = top_k if top_k is not None else self._default_top_k
        if requested_top_k < 1 or requested_top_k > self._maximum_top_k:
            raise InvalidRequestError(
                f"top_k must be between 1 and {self._maximum_top_k}"
            )
        query_vector = self._embeddings.embed_query(normalized_question)
        return self._repository.search(
            tenant_id,
            normalized_question,
            query_vector,
            requested_top_k,
            self._semantic_weight,
        )

    def query(
        self, tenant_id: str, question: str, top_k: int | None = None
    ) -> QueryResult:
        hits = self.retrieve(tenant_id, question, top_k)
        if self.should_abstain(hits):
            return QueryResult(
                answer="I don't know based on the documents available to this tenant.",
                citations=(),
                abstained=True,
                model=None,
            )

        generation = self._generator.generate(question.strip(), hits)
        if generation.abstained:
            return QueryResult(
                answer=generation.text,
                citations=(),
                abstained=True,
                model=generation.model,
                input_tokens=generation.input_tokens,
                output_tokens=generation.output_tokens,
            )

        cited_numbers = list(
            dict.fromkeys(int(value) for value in CITATION_PATTERN.findall(generation.text))
        )
        if not cited_numbers:
            raise InvalidGeneratedAnswerError(
                "Generated answer did not cite any retrieved source"
            )
        if any(number < 1 or number > len(hits) for number in cited_numbers):
            raise InvalidGeneratedAnswerError(
                "Generated answer cited a source that was not retrieved"
            )
        citations = tuple(
            AnswerCitation(
                number=number,
                document_id=hit.chunk.document_id,
                chunk_id=hit.chunk.id,
                title=hit.chunk.document_title,
                source=hit.chunk.source,
                excerpt=hit.chunk.content[:280],
                relevance_score=round(hit.score, 6),
            )
            for number in cited_numbers
            for hit in (hits[number - 1],)
        )
        return QueryResult(
            answer=generation.text,
            citations=citations,
            abstained=False,
            model=generation.model,
            input_tokens=generation.input_tokens,
            output_tokens=generation.output_tokens,
        )

    def should_abstain(self, hits: list[RetrievalHit]) -> bool:
        return not hits or hits[0].score < self._minimum_relevance_score

    def list_documents(self, tenant_id: str) -> list[Document]:
        return self._repository.list_documents(tenant_id)

    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        return self._repository.delete_document(tenant_id, document_id)
