"""Run a golden retrieval dataset against the application service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from knowledge_assistant.evaluation.metrics import recall_at_k, reciprocal_rank
from knowledge_assistant.services.knowledge import KnowledgeAssistant


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    id: str
    tenant_id: str
    question: str
    relevant_sources: frozenset[str]
    expected_abstention: bool


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    retrieved_sources: tuple[str, ...]
    recall_at_k: float | None
    reciprocal_rank: float | None
    expected_abstention: bool
    abstained: bool
    abstention_correct: bool


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    case_count: int
    mean_recall_at_k: float | None
    mean_reciprocal_rank: float | None
    abstention_accuracy: float
    negative_false_answer_rate: float | None
    cases: tuple[CaseResult, ...]


def load_cases(path: Path) -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                relevant_sources = frozenset(item["relevant_sources"])
                expected_abstention = item.get(
                    "expected_abstention", not relevant_sources
                )
                if not isinstance(expected_abstention, bool):
                    raise TypeError("expected_abstention must be a boolean")
                cases.append(
                    EvaluationCase(
                        id=item["id"],
                        tenant_id=item["tenant_id"],
                        question=item["question"],
                        relevant_sources=relevant_sources,
                        expected_abstention=expected_abstention,
                    )
                )
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid evaluation case on line {line_number}") from exc
    return cases


class RetrievalEvaluator:
    def __init__(self, assistant: KnowledgeAssistant) -> None:
        self._assistant = assistant

    def run(self, cases: list[EvaluationCase], top_k: int = 5) -> EvaluationReport:
        results: list[CaseResult] = []
        for case in cases:
            hits = self._assistant.retrieve(case.tenant_id, case.question, top_k)
            sources = tuple(hit.chunk.source for hit in hits)
            abstained = self._assistant.should_abstain(hits)
            has_relevant_sources = bool(case.relevant_sources)
            results.append(
                CaseResult(
                    case_id=case.id,
                    retrieved_sources=sources,
                    recall_at_k=(
                        recall_at_k(sources, case.relevant_sources, top_k)
                        if has_relevant_sources
                        else None
                    ),
                    reciprocal_rank=(
                        reciprocal_rank(sources, case.relevant_sources)
                        if has_relevant_sources
                        else None
                    ),
                    expected_abstention=case.expected_abstention,
                    abstained=abstained,
                    abstention_correct=abstained == case.expected_abstention,
                )
            )

        count = len(results)
        positive_results = [item for item in results if item.recall_at_k is not None]
        negative_results = [item for item in results if item.expected_abstention]
        return EvaluationReport(
            case_count=count,
            mean_recall_at_k=(
                sum(item.recall_at_k for item in positive_results if item.recall_at_k is not None)
                / len(positive_results)
                if positive_results
                else None
            ),
            mean_reciprocal_rank=(
                sum(
                    item.reciprocal_rank
                    for item in positive_results
                    if item.reciprocal_rank is not None
                )
                / len(positive_results)
                if positive_results
                else None
            ),
            abstention_accuracy=(
                sum(item.abstention_correct for item in results) / count if count else 0.0
            ),
            negative_false_answer_rate=(
                sum(not item.abstained for item in negative_results)
                / len(negative_results)
                if negative_results
                else None
            ),
            cases=tuple(results),
        )
