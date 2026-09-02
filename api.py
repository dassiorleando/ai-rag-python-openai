"""FastAPI server for the single-document RAG example."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from openai import APIConnectionError, OpenAI

from rag import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_DOCUMENT_PATH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_TOP_K,
    answer_question,
    build_vector_store,
    load_document_chunks,
)


def build_rag_resources() -> tuple[FAISS, Any]:
    """Create the index once when the API starts, instead of for every request."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file.")

    chunks = load_document_chunks(DEFAULT_DOCUMENT_PATH)
    embeddings = OpenAIEmbeddings(api_key=api_key, model=DEFAULT_EMBEDDING_MODEL)
    return build_vector_store(chunks, embeddings), OpenAI(api_key=api_key)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.vector_store, app.state.openai_client = build_rag_resources()
    yield


app = FastAPI(title="Simple RAG API", lifespan=lifespan)


@app.get("/query")
def query_document(
    query: Annotated[str, Query(min_length=1, description="Question to ask the document")],
    top_k: Annotated[int, Query(ge=1, le=10)] = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """Answer a question using the most similar document chunks as context."""
    try:
        answer, retrieved_docs = answer_question(
            query=query,
            vector_store=app.state.vector_store,
            client=app.state.openai_client,
            model=DEFAULT_CHAT_MODEL,
            top_k=top_k,
        )
    except APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="OpenAI is unavailable.") from exc

    return {
        "query": query,
        "answer": answer,
        "retrieved_chunks": [doc.page_content for doc in retrieved_docs],
    }
