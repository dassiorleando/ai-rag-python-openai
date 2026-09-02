from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.documents import Document

from rag import build_vector_store
from test_rag import KeywordEmbeddings


class ApiTests(unittest.TestCase):
    def test_query_returns_an_answer_and_the_retrieved_chunk(self):
        class FakeResponses:
            def create(self, **kwargs):
                return SimpleNamespace(output_text="TowerZ is a business system.")

        vector_store = build_vector_store(
            [Document(page_content="TowerZ is a business system.")],
            KeywordEmbeddings(),
        )
        fake_client = SimpleNamespace(responses=FakeResponses())

        with patch("api.build_rag_resources", return_value=(vector_store, fake_client)):
            from api import app

            with TestClient(app) as client:
                response = client.get("/query", params={"query": "What is TowerZ?"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "TowerZ is a business system.")
        self.assertEqual(response.json()["retrieved_chunks"], ["TowerZ is a business system."])


if __name__ == "__main__":
    unittest.main()
