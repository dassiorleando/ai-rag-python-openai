"""Durable SQLite adapter with tenant-scoped hybrid retrieval."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from threading import RLock

from knowledge_assistant.domain.errors import DocumentAlreadyExistsError
from knowledge_assistant.domain.models import Chunk, Document, RetrievalHit

TOKEN_PATTERN = re.compile(r"[\w'-]+", re.UNICODE)


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return max(0.0, dot_product / (left_norm * right_norm))


def _lexical_similarity(query: str, content: str) -> float:
    query_tokens = set(TOKEN_PATTERN.findall(query.casefold()))
    content_tokens = set(TOKEN_PATTERN.findall(content.casefold()))
    if not query_tokens or not content_tokens:
        return 0.0
    return len(query_tokens & content_tokens) / math.sqrt(
        len(query_tokens) * len(content_tokens)
    )


class SQLiteKnowledgeRepository:
    """Reference persistence adapter.

    It is intentionally transparent for learning and small deployments. Search is
    performed over tenant-filtered rows in process; replace this adapter with
    pgvector or a managed hybrid-search engine before operating at large scale.
    """

    def __init__(self, database_path: Path | str) -> None:
        self._database_path = str(database_path)
        self._connection_lock = RLock()
        self._closed = False
        self._memory_connection = (
            self._new_connection() if self._database_path == ":memory:" else None
        )

    def _new_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with self._connection_lock:
            if self._closed:
                raise RuntimeError("Repository is closed")
            connection = self._memory_connection or self._new_connection()
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                if self._memory_connection is None:
                    connection.close()

    def initialize(self) -> None:
        database_path = Path(self._database_path)
        if self._database_path != ":memory:":
            database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (tenant_id, content_hash)
                );

                CREATE INDEX IF NOT EXISTS documents_tenant_idx
                    ON documents (tenant_id, created_at);

                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    document_title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE (document_id, ordinal)
                );

                CREATE INDEX IF NOT EXISTS chunks_tenant_idx
                    ON chunks (tenant_id, document_id);
                """
            )

    def close(self) -> None:
        with self._connection_lock:
            if not self._closed and self._memory_connection is not None:
                self._memory_connection.close()
            self._closed = True

    def find_document_by_hash(
        self, tenant_id: str, content_hash: str
    ) -> Document | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, tenant_id, title, source, content_hash, metadata_json, created_at
                FROM documents
                WHERE tenant_id = ? AND content_hash = ?
                """,
                (tenant_id, content_hash),
            ).fetchone()
        return self._document_from_row(row) if row else None

    def add_document(self, document: Document, chunks: Sequence[Chunk]) -> None:
        if any(
            chunk.tenant_id != document.tenant_id or chunk.document_id != document.id
            for chunk in chunks
        ):
            raise ValueError("Every chunk must belong to the supplied document and tenant")
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO documents
                        (id, tenant_id, title, source, content_hash, metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document.id,
                        document.tenant_id,
                        document.title,
                        document.source,
                        document.content_hash,
                        json.dumps(document.metadata, sort_keys=True),
                        document.created_at.isoformat(),
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO chunks
                        (id, tenant_id, document_id, document_title, source, ordinal,
                         content, embedding_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            chunk.id,
                            chunk.tenant_id,
                            chunk.document_id,
                            chunk.document_title,
                            chunk.source,
                            chunk.ordinal,
                            chunk.content,
                            json.dumps(chunk.embedding),
                            json.dumps(chunk.metadata, sort_keys=True),
                        )
                        for chunk in chunks
                    ],
                )
        except sqlite3.IntegrityError as exc:
            if "documents.tenant_id, documents.content_hash" in str(exc):
                raise DocumentAlreadyExistsError from exc
            raise

    def list_documents(self, tenant_id: str) -> list[Document]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, tenant_id, title, source, content_hash, metadata_json, created_at
                FROM documents
                WHERE tenant_id = ?
                ORDER BY created_at DESC
                """,
                (tenant_id,),
            ).fetchall()
        return [self._document_from_row(row) for row in rows]

    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM documents WHERE tenant_id = ? AND id = ?",
                (tenant_id, document_id),
            )
        return cursor.rowcount > 0

    def search(
        self,
        tenant_id: str,
        query: str,
        query_embedding: Sequence[float],
        top_k: int,
        semantic_weight: float,
    ) -> list[RetrievalHit]:
        # Filtering happens in SQL before scoring. A caller can never retrieve
        # another tenant's chunks and then attempt to filter them afterward.
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, tenant_id, document_id, document_title, source, ordinal,
                       content, embedding_json, metadata_json
                FROM chunks
                WHERE tenant_id = ?
                """,
                (tenant_id,),
            ).fetchall()

        hits: list[RetrievalHit] = []
        for row in rows:
            embedding = tuple(json.loads(row["embedding_json"]))
            semantic_score = _cosine_similarity(query_embedding, embedding)
            lexical_score = _lexical_similarity(query, row["content"])
            score = (
                semantic_weight * semantic_score
                + (1.0 - semantic_weight) * lexical_score
            )
            chunk = Chunk(
                id=row["id"],
                tenant_id=row["tenant_id"],
                document_id=row["document_id"],
                document_title=row["document_title"],
                source=row["source"],
                ordinal=row["ordinal"],
                content=row["content"],
                embedding=embedding,
                metadata=json.loads(row["metadata_json"]),
            )
            hits.append(RetrievalHit(chunk, semantic_score, lexical_score, score))

        hits.sort(key=lambda hit: (-hit.score, hit.chunk.document_id, hit.chunk.ordinal))
        return hits[:top_k]

    @staticmethod
    def _document_from_row(row: sqlite3.Row) -> Document:
        return Document(
            id=row["id"],
            tenant_id=row["tenant_id"],
            title=row["title"],
            source=row["source"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
