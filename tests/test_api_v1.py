import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from knowledge_assistant.api.app import create_app
from knowledge_assistant.api.container import Container
from knowledge_assistant.domain.models import GenerationOutput
from knowledge_assistant.security.auth import ApiKeyAuthenticator
from knowledge_assistant.services.chunking import TextChunker
from knowledge_assistant.services.knowledge import KnowledgeAssistant
from knowledge_assistant.storage.sqlite import SQLiteKnowledgeRepository
from tests.fakes import HashEmbeddingProvider, RecordingGenerator


class ApiV1Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        repository = SQLiteKnowledgeRepository(Path(self.temp_dir.name) / "api.db")
        self.generator = RecordingGenerator()
        self.assistant = KnowledgeAssistant(
            repository=repository,
            embeddings=HashEmbeddingProvider(),
            generator=self.generator,
            chunker=TextChunker(120, 20),
            minimum_relevance_score=0.05,
        )
        container = Container(
            repository=repository,
            assistant=self.assistant,
            authenticator=ApiKeyAuthenticator({"tenant-a": "key-a", "tenant-b": "key-b"}),
        )
        self.client_context = TestClient(create_app(container))
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_missing_api_key_is_rejected(self):
        response = self.client.get("/v1/documents")
        self.assertEqual(response.status_code, 401)

    def test_invalid_api_key_is_rejected(self):
        response = self.client.get("/v1/documents", headers={"X-API-Key": "wrong"})
        self.assertEqual(response.status_code, 401)

    def test_document_lifecycle_and_query_are_tenant_scoped(self):
        created = self.client.post(
            "/v1/documents",
            headers={"X-API-Key": "key-a"},
            json={
                "title": "Product guide",
                "source": "product.txt",
                "content": "TowerZ helps leaders prioritize business work.",
            },
        )
        self.assertEqual(created.status_code, 201)
        document_id = created.json()["document"]["id"]

        tenant_a = self.client.get("/v1/documents", headers={"X-API-Key": "key-a"})
        tenant_b = self.client.get("/v1/documents", headers={"X-API-Key": "key-b"})
        self.assertEqual(len(tenant_a.json()), 1)
        self.assertEqual(tenant_b.json(), [])

        answer = self.client.post(
            "/v1/query",
            headers={"X-API-Key": "key-a"},
            json={"question": "What does TowerZ prioritize?"},
        )
        self.assertEqual(answer.status_code, 200)
        self.assertEqual(answer.json()["citations"][0]["document_id"], document_id)

        forbidden_delete = self.client.delete(
            f"/v1/documents/{document_id}", headers={"X-API-Key": "key-b"}
        )
        self.assertEqual(forbidden_delete.status_code, 404)

    def test_duplicate_ingestion_is_reported_as_idempotent(self):
        payload = {"title": "Guide", "source": "guide.txt", "content": "Stable content."}
        first = self.client.post("/v1/documents", headers={"X-API-Key": "key-a"}, json=payload)
        second = self.client.post("/v1/documents", headers={"X-API-Key": "key-a"}, json=payload)

        self.assertTrue(first.json()["created"])
        self.assertFalse(second.json()["created"])
        self.assertEqual(first.json()["document"]["id"], second.json()["document"]["id"])

    def test_whitespace_only_fields_are_validation_errors(self):
        document = self.client.post(
            "/v1/documents",
            headers={"X-API-Key": "key-a"},
            json={"title": " ", "source": "source", "content": "content"},
        )
        query = self.client.post(
            "/v1/query",
            headers={"X-API-Key": "key-a"},
            json={"question": "   "},
        )

        self.assertEqual(document.status_code, 422)
        self.assertEqual(query.status_code, 422)

    def test_configured_top_k_limit_returns_validation_error(self):
        response = self.client.post(
            "/v1/query",
            headers={"X-API-Key": "key-a"},
            json={"question": "Valid question", "top_k": 21},
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("top_k", response.json()["detail"])

    def test_invalid_generated_citations_fail_closed(self):
        created = self.client.post(
            "/v1/documents",
            headers={"X-API-Key": "key-a"},
            json={"title": "Policy", "source": "policy.txt", "content": "Policy details."},
        )
        self.assertEqual(created.status_code, 201)
        self.generator.generate = lambda question, retrieved: GenerationOutput(
            text="Unsupported answer without citations.", model="test-model"
        )

        response = self.client.post(
            "/v1/query",
            headers={"X-API-Key": "key-a"},
            json={"question": "What are the policy details?"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertNotIn("citation", response.text.lower())
