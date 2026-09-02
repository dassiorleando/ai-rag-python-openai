"""A small, single-document RAG example using OpenAI embeddings and FAISS."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import APIConnectionError, OpenAI

DEFAULT_DOCUMENT_PATH = Path("data/document.txt")
DEFAULT_QUERY = "What is TowerZ?"
DEFAULT_CHAT_MODEL = "gpt-4.1-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_TOP_K = 3
INSTRUCTIONS = (
    "You are a retrieval-augmented assistant. Answer using only the provided "
    "context and be explicit when the context is insufficient."
)


def load_document_chunks(document_path: Path) -> list[Document]:
    """Read the source file and split it into chunks for retrieval."""
    if not document_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    document_text = document_path.read_text(encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    )
    return splitter.create_documents(
        texts=[document_text],
        metadatas=[{"source": str(document_path)}],
    )


def build_vector_store(documents: list[Document], embeddings: Embeddings) -> FAISS:
    """Embed document chunks and store them in a FAISS similarity index."""
    return FAISS.from_documents(documents, embeddings)


def retrieve_chunks(vector_store: FAISS, query: str, top_k: int) -> list[Document]:
    """Return the chunks whose embeddings are closest to the query embedding."""
    if top_k < 1:
        raise ValueError("top_k must be greater than 0.")
    return vector_store.similarity_search(query, k=top_k)


def build_prompt(query: str, retrieved_docs: list[Document]) -> str:
    """Put only the retrieved chunks, not the whole document, in the LLM prompt."""
    context = "\n\n".join(
        f"[Chunk {index}]\n{doc.page_content.strip()}"
        for index, doc in enumerate(retrieved_docs, start=1)
    )
    return (
        "Use the context below to answer the question.\n"
        "If the answer is not supported by the context, say you do not know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )


def answer_question(
    query: str,
    vector_store: FAISS,
    client: Any,
    model: str,
    top_k: int,
) -> tuple[str, list[Document]]:
    """Retrieve relevant chunks, add them to the prompt, and ask the LLM."""
    retrieved_docs = retrieve_chunks(vector_store, query, top_k)
    prompt = build_prompt(query, retrieved_docs)
    response = client.responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=prompt,
    )
    answer = response.output_text.strip()
    if not answer:
        raise ValueError("The model returned an empty answer.")
    return answer, retrieved_docs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple RAG lookup.")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--document", default=str(DEFAULT_DOCUMENT_PATH))
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--model", default=DEFAULT_CHAT_MODEL)
    parser.add_argument("--show-context", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is missing. Add it to your .env file.", file=sys.stderr)
        return 1

    try:
        chunks = load_document_chunks(Path(args.document))
        embeddings = OpenAIEmbeddings(api_key=api_key, model=DEFAULT_EMBEDDING_MODEL)
        vector_store = build_vector_store(chunks, embeddings)
        answer, retrieved_docs = answer_question(
            query=args.query,
            vector_store=vector_store,
            client=OpenAI(api_key=api_key),
            model=args.model,
            top_k=args.top_k,
        )
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except APIConnectionError:
        print("OpenAI connection failed. Check your internet connection and API access.", file=sys.stderr)
        return 1

    print(f"Query: {args.query}\n")
    if args.show_context:
        print("Retrieved document chunks:")
        for index, doc in enumerate(retrieved_docs, start=1):
            print(f"\n[{index}] {doc.page_content}")
        print()
    print("Answer:")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
