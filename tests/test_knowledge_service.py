import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from knowledge_assistant.domain.errors import InvalidGeneratedAnswerError
from knowledge_assistant.domain.models import GenerationOutput
from knowledge_assistant.services.chunking import TextChunker
from knowledge_assistant.services.knowledge import KnowledgeAssistant
from knowledge_assistant.storage.sqlite import SQLiteKnowledgeRepository
from tests.fakes import HashEmbeddingProvider, RecordingGenerator


class KnowledgeServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.repository = SQLiteKnowledgeRepository(Path(self.temp_dir.name) / "test.db")
        self.repository.initialize()
        self.generator = RecordingGenerator()
        self.assistant = KnowledgeAssistant(
            repository=self.repository,
            embeddings=HashEmbeddingProvider(),
            generator=self.generator,
            chunker=TextChunker(chunk_size=120, chunk_overlap=20),
            minimum_relevance_score=0.05,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ingestion_is_idempotent_within_a_tenant(self):
        first = self.assistant.ingest(
            "tenant-a", title="Guide", source="guide.txt", content="Revenue planning guide."
        )
        second = self.assistant.ingest(
            "tenant-a", title="Copy", source="copy.txt", content="Revenue planning guide."
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.document.id, second.document.id)
        self.assertEqual(len(self.assistant.list_documents("tenant-a")), 1)

    def test_ingestion_rejects_whitespace_only_title_and_source(self):
        with self.assertRaisesRegex(ValueError, "title"):
            self.assistant.ingest(
                "tenant-a", title="   ", source="guide.txt", content="Content"
            )
        with self.assertRaisesRegex(ValueError, "source"):
            self.assistant.ingest(
                "tenant-a", title="Guide", source="   ", content="Content"
            )

    def test_same_content_is_allowed_for_different_tenants(self):
        for tenant_id in ("tenant-a", "tenant-b"):
            self.assistant.ingest(
                tenant_id, title="Shared", source="shared.txt", content="Common handbook text."
            )

        self.assertEqual(len(self.assistant.list_documents("tenant-a")), 1)
        self.assertEqual(len(self.assistant.list_documents("tenant-b")), 1)

    def test_retrieval_never_returns_another_tenants_chunks(self):
        self.assistant.ingest(
            "tenant-a", title="Alpha", source="alpha.txt", content="Orchids are purple."
        )
        self.assistant.ingest(
            "tenant-b", title="Secret", source="secret.txt", content="Orchids are classified."
        )

        hits = self.assistant.retrieve("tenant-a", "What color are orchids?", top_k=10)

        self.assertTrue(hits)
        self.assertEqual({hit.chunk.tenant_id for hit in hits}, {"tenant-a"})
        self.assertNotIn("classified", " ".join(hit.chunk.content for hit in hits))

    def test_query_returns_citations_and_usage(self):
        document = self.assistant.ingest(
            "tenant-a", title="Product", source="product.txt", content="TowerZ prioritizes business work."
        ).document

        result = self.assistant.query("tenant-a", "What does TowerZ prioritize?")

        self.assertFalse(result.abstained)
        self.assertEqual(result.citations[0].document_id, document.id)
        self.assertEqual(result.citations[0].source, "product.txt")
        self.assertEqual(result.input_tokens, 20)

    def test_query_abstains_without_calling_generator_when_tenant_has_no_documents(self):
        result = self.assistant.query("empty-tenant", "What is the policy?")

        self.assertTrue(result.abstained)
        self.assertEqual(result.citations, ())
        self.assertEqual(self.generator.calls, [])

    def test_tenant_cannot_delete_another_tenants_document(self):
        document = self.assistant.ingest(
            "tenant-a", title="Private", source="private.txt", content="Private tenant information."
        ).document

        self.assertFalse(self.assistant.delete_document("tenant-b", document.id))
        self.assertTrue(self.assistant.delete_document("tenant-a", document.id))

    def test_only_sources_cited_by_the_answer_are_returned(self):
        self.assistant.ingest(
            "tenant-a", title="Alpha", source="alpha.txt", content="Alpha policy details."
        )
        self.assistant.ingest(
            "tenant-a", title="Beta", source="beta.txt", content="Beta policy details."
        )
        hits = self.assistant.retrieve("tenant-a", "policy details", top_k=2)
        cited_number = 2
        self.generator.generate = lambda question, retrieved: GenerationOutput(
            text=f"The selected policy applies. [{cited_number}]", model="test-model"
        )

        result = self.assistant.query("tenant-a", "policy details", top_k=2)

        self.assertEqual([citation.number for citation in result.citations], [cited_number])
        self.assertEqual(result.citations[0].chunk_id, hits[cited_number - 1].chunk.id)

    def test_unknown_or_missing_citations_are_rejected(self):
        self.assistant.ingest(
            "tenant-a", title="Policy", source="policy.txt", content="Policy details."
        )
        for answer in ("Unsupported answer.", "Unsupported answer. [99]"):
            with self.subTest(answer=answer):
                self.generator.generate = lambda question, retrieved, text=answer: GenerationOutput(
                    text=text, model="test-model"
                )
                with self.assertRaises(InvalidGeneratedAnswerError):
                    self.assistant.query("tenant-a", "Policy details?")

    def test_generator_abstention_returns_no_citations(self):
        self.assistant.ingest(
            "tenant-a", title="Policy", source="policy.txt", content="Policy details."
        )
        self.generator.generate = lambda question, retrieved: GenerationOutput(
            text="I don't know based on the available sources.",
            model="test-model",
            abstained=True,
        )

        result = self.assistant.query("tenant-a", "Policy details?")

        self.assertTrue(result.abstained)
        self.assertEqual(result.citations, ())

    def test_in_memory_repository_persists_across_operations(self):
        repository = SQLiteKnowledgeRepository(":memory:")
        repository.initialize()
        assistant = KnowledgeAssistant(
            repository=repository,
            embeddings=HashEmbeddingProvider(),
            generator=RecordingGenerator(),
            chunker=TextChunker(chunk_size=120, chunk_overlap=20),
            minimum_relevance_score=0.05,
        )

        assistant.ingest(
            "tenant-a", title="Memory", source="memory.txt", content="Persistent memory."
        )

        self.assertEqual(len(assistant.list_documents("tenant-a")), 1)
        repository.close()
