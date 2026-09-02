from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from rag import answer_question, build_prompt, build_vector_store, load_document_chunks, retrieve_chunks


class KeywordEmbeddings(Embeddings):
    """Deterministic embeddings so the retrieval test does not call OpenAI."""

    KEYWORDS = ("towerz", "strategy", "invoice")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        text_lower = text.lower()
        return [float(keyword in text_lower) for keyword in self.KEYWORDS]


class RagTests(unittest.TestCase):
    def test_document_is_split_into_chunks(self):
        with TemporaryDirectory() as temp_dir:
            document_path = Path(temp_dir) / "document.txt"
            document_path.write_text("TowerZ " * 300, encoding="utf-8")

            chunks = load_document_chunks(document_path)

        self.assertGreater(len(chunks), 1)

    def test_similarity_search_returns_relevant_chunk(self):
        documents = [
            Document(page_content="TowerZ helps businesses understand what to fix first."),
            Document(page_content="Invoices and payments are managed inside the system."),
        ]
        vector_store = build_vector_store(documents, KeywordEmbeddings())

        results = retrieve_chunks(vector_store, "What is TowerZ?", top_k=1)

        self.assertEqual(len(results), 1)
        self.assertIn("TowerZ helps businesses", results[0].page_content)

    def test_prompt_contains_only_retrieved_chunks(self):
        prompt = build_prompt(
            "What is TowerZ?",
            [Document(page_content="TowerZ gives business guidance.")],
        )

        self.assertIn("[Chunk 1]", prompt)
        self.assertIn("TowerZ gives business guidance.", prompt)
        self.assertIn("Question: What is TowerZ?", prompt)

    def test_answer_question_sends_retrieved_context_to_openai(self):
        class FakeResponses:
            def __init__(self):
                self.request = None

            def create(self, **kwargs):
                self.request = kwargs
                return SimpleNamespace(output_text="TowerZ is an AI-powered business system.")

        responses = FakeResponses()
        client = SimpleNamespace(responses=responses)
        vector_store = build_vector_store(
            [Document(page_content="TowerZ is an AI-powered business system.")],
            KeywordEmbeddings(),
        )

        answer, retrieved_docs = answer_question(
            "What is TowerZ?", vector_store, client, "gpt-test", top_k=1
        )

        self.assertEqual(answer, "TowerZ is an AI-powered business system.")
        self.assertEqual(len(retrieved_docs), 1)
        self.assertIn("TowerZ is an AI-powered business system.", responses.request["input"])


if __name__ == "__main__":
    unittest.main()
