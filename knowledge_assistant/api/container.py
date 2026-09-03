"""Composition root: the only module that wires concrete adapters together."""

from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from knowledge_assistant.config import Settings
from knowledge_assistant.ports import KnowledgeRepository
from knowledge_assistant.providers.openai import OpenAIAnswerGenerator, OpenAIEmbeddingProvider
from knowledge_assistant.security.auth import ApiKeyAuthenticator
from knowledge_assistant.services.chunking import TextChunker
from knowledge_assistant.services.knowledge import KnowledgeAssistant
from knowledge_assistant.storage.sqlite import SQLiteKnowledgeRepository


@dataclass(slots=True)
class Container:
    repository: KnowledgeRepository
    assistant: KnowledgeAssistant
    authenticator: ApiKeyAuthenticator


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or Settings()
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is required")

    tenant_keys = settings.api_keys_by_tenant()
    if not tenant_keys:
        raise RuntimeError("KA_TENANT_API_KEYS is required")

    client = OpenAI(api_key=settings.openai_api_key.get_secret_value())
    repository = SQLiteKnowledgeRepository(settings.database_path)
    assistant = KnowledgeAssistant(
        repository=repository,
        embeddings=OpenAIEmbeddingProvider(
            client,
            settings.embedding_model,
            batch_size=settings.embedding_batch_size,
            max_batch_tokens=settings.embedding_batch_max_tokens,
        ),
        generator=OpenAIAnswerGenerator(
            client,
            settings.chat_model,
            store_responses=settings.openai_store_responses,
        ),
        chunker=TextChunker(settings.chunk_size, settings.chunk_overlap),
        default_top_k=settings.default_top_k,
        maximum_top_k=settings.maximum_top_k,
        minimum_relevance_score=settings.minimum_relevance_score,
        semantic_weight=settings.semantic_weight,
        maximum_document_characters=settings.maximum_document_characters,
    )
    return Container(repository, assistant, ApiKeyAuthenticator(tenant_keys))
