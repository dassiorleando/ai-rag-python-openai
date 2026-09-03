import unittest

from knowledge_assistant.evaluation.metrics import recall_at_k, reciprocal_rank
from knowledge_assistant.evaluation.runner import EvaluationCase, RetrievalEvaluator


class RetrievalMetricsTests(unittest.TestCase):
    def test_recall_at_k(self):
        score = recall_at_k(["a", "b", "c"], {"b", "d"}, 2)
        self.assertEqual(score, 0.5)

    def test_reciprocal_rank(self):
        self.assertEqual(reciprocal_rank(["a", "b", "c"], {"b"}), 0.5)
        self.assertEqual(reciprocal_rank(["a"], {"missing"}), 0.0)

    def test_empty_relevant_set_is_a_valid_negative_case(self):
        with self.assertRaisesRegex(ValueError, "undefined"):
            recall_at_k(["anything"], set(), 1)


class RetrievalEvaluatorTests(unittest.TestCase):
    def test_report_aggregates_case_metrics(self):
        hit = type(
            "Hit",
            (),
            {"chunk": type("Chunk", (), {"source": "handbook.txt"})()},
        )()
        assistant = type(
            "Assistant",
            (),
            {
                "retrieve": lambda self, tenant, question, top_k: [hit],
                "should_abstain": lambda self, hits: False,
            },
        )()
        case = EvaluationCase(
            id="case-1",
            tenant_id="tenant-a",
            question="Where is the policy?",
            relevant_sources=frozenset({"handbook.txt"}),
            expected_abstention=False,
        )

        report = RetrievalEvaluator(assistant).run([case], top_k=1)

        self.assertEqual(report.case_count, 1)
        self.assertEqual(report.mean_recall_at_k, 1.0)
        self.assertEqual(report.mean_reciprocal_rank, 1.0)
        self.assertEqual(report.abstention_accuracy, 1.0)

    def test_negative_case_measures_false_answer_instead_of_recall(self):
        hit = type(
            "Hit",
            (),
            {"chunk": type("Chunk", (), {"source": "irrelevant.txt"})()},
        )()
        assistant = type(
            "Assistant",
            (),
            {
                "retrieve": lambda self, tenant, question, top_k: [hit],
                "should_abstain": lambda self, hits: False,
            },
        )()
        case = EvaluationCase(
            id="negative-1",
            tenant_id="tenant-a",
            question="Unknown question",
            relevant_sources=frozenset(),
            expected_abstention=True,
        )

        report = RetrievalEvaluator(assistant).run([case], top_k=1)

        self.assertIsNone(report.mean_recall_at_k)
        self.assertIsNone(report.cases[0].recall_at_k)
        self.assertEqual(report.abstention_accuracy, 0.0)
        self.assertEqual(report.negative_false_answer_rate, 1.0)
