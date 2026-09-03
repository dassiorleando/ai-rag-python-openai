"""FastAPI application for the multi-tenant knowledge assistant."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status

from knowledge_assistant.api.container import Container, build_container
from knowledge_assistant.api.schemas import (
    CitationResponse,
    DocumentResponse,
    HealthResponse,
    IngestDocumentRequest,
    IngestDocumentResponse,
    QueryRequest,
    QueryResponse,
    UsageResponse,
)
from knowledge_assistant.domain.errors import (
    AIProviderInputError,
    AIProviderResponseError,
    AIProviderUnavailableError,
    InvalidGeneratedAnswerError,
    InvalidRequestError,
)
from knowledge_assistant.domain.models import Document
from knowledge_assistant.observability import RequestContextMiddleware
from knowledge_assistant.security.auth import TenantPrincipal
from knowledge_assistant.services.knowledge import DocumentTooLargeError


def create_app(container: Container | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        active_container = container or build_container()
        active_container.repository.initialize()
        application.state.container = active_container
        try:
            yield
        finally:
            active_container.repository.close()

    application = FastAPI(
        title="Multi-tenant Knowledge Assistant",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.add_middleware(RequestContextMiddleware)

    def get_container(request: Request) -> Container:
        return request.app.state.container

    def get_principal(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        active_container: Container = Depends(get_container),
    ) -> TenantPrincipal:
        principal = (
            active_container.authenticator.authenticate(x_api_key)
            if x_api_key is not None
            else None
        )
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        return principal

    @application.get("/health", response_model=HealthResponse, tags=["operations"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.post(
        "/v1/documents",
        response_model=IngestDocumentResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["documents"],
    )
    def ingest_document(
        payload: IngestDocumentRequest,
        principal: TenantPrincipal = Depends(get_principal),
        active_container: Container = Depends(get_container),
    ) -> IngestDocumentResponse:
        try:
            result = active_container.assistant.ingest(
                principal.tenant_id,
                title=payload.title,
                source=payload.source,
                content=payload.content,
                metadata=payload.metadata,
            )
        except DocumentTooLargeError as exc:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=str(exc),
            ) from exc
        except InvalidRequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        except AIProviderInputError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        except AIProviderUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI provider unavailable",
            ) from exc
        except AIProviderResponseError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI provider returned an invalid response",
            ) from exc
        return IngestDocumentResponse(
            document=_document_response(result.document),
            chunk_count=result.chunk_count,
            created=result.created,
        )

    @application.get(
        "/v1/documents",
        response_model=list[DocumentResponse],
        tags=["documents"],
    )
    def list_documents(
        principal: TenantPrincipal = Depends(get_principal),
        active_container: Container = Depends(get_container),
    ) -> list[DocumentResponse]:
        return [
            _document_response(document)
            for document in active_container.assistant.list_documents(principal.tenant_id)
        ]

    @application.delete(
        "/v1/documents/{document_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["documents"],
    )
    def delete_document(
        document_id: str,
        principal: TenantPrincipal = Depends(get_principal),
        active_container: Container = Depends(get_container),
    ) -> Response:
        deleted = active_container.assistant.delete_document(
            principal.tenant_id, document_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @application.post("/v1/query", response_model=QueryResponse, tags=["query"])
    def query(
        payload: QueryRequest,
        principal: TenantPrincipal = Depends(get_principal),
        active_container: Container = Depends(get_container),
    ) -> QueryResponse:
        try:
            result = active_container.assistant.query(
                principal.tenant_id, payload.question, payload.top_k
            )
        except InvalidRequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        except AIProviderInputError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        except AIProviderUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI provider unavailable",
            ) from exc
        except (AIProviderResponseError, InvalidGeneratedAnswerError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI provider returned an invalid response",
            ) from exc
        return QueryResponse(
            answer=result.answer,
            citations=[
                CitationResponse(
                    number=citation.number,
                    document_id=citation.document_id,
                    chunk_id=citation.chunk_id,
                    title=citation.title,
                    source=citation.source,
                    excerpt=citation.excerpt,
                    relevance_score=citation.relevance_score,
                )
                for citation in result.citations
            ],
            abstained=result.abstained,
            model=result.model,
            usage=UsageResponse(
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            ),
        )

    return application


def _document_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        title=document.title,
        source=document.source,
        metadata=document.metadata,
        created_at=document.created_at,
    )


app = create_app()
