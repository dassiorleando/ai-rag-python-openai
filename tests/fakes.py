"""Deterministic test doubles for AI providers."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

from knowledge_assistant.domain.models import GenerationOutput, RetrievalHit


class HashEmbeddingProvider:
    """A stable bag-of-words embedding with no external API calls."""

    def __init__(self, dimensions: int = 64) -> None:
        self._dimensions = dimensions

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for token in re.findall(r"[\w'-]+", text.casefold()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % self._dimensions] += 1.0
        return vector


class RecordingGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Sequence[RetrievalHit]]] = []

    def generate(
        self, question: str, retrieved_chunks: Sequence[RetrievalHit]
    ) -> GenerationOutput:
        self.calls.append((question, retrieved_chunks))
        return GenerationOutput(
            text=f"Grounded answer from {retrieved_chunks[0].chunk.document_title}. [1]",
            model="test-model",
            input_tokens=20,
            output_tokens=8,
        )
