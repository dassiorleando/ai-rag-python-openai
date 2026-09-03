"""Document chunking policy."""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextChunker:
    """Split text at semantic boundaries before falling back to characters."""

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split(self, text: str) -> list[str]:
        return [chunk.strip() for chunk in self._splitter.split_text(text) if chunk.strip()]
