"""CLI for running the offline retrieval evaluation dataset."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from knowledge_assistant.api.container import build_container
from knowledge_assistant.evaluation.runner import RetrievalEvaluator, load_cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval against a JSONL dataset")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    container = build_container()
    container.repository.initialize()
    report = RetrievalEvaluator(container.assistant).run(load_cases(args.dataset), args.top_k)
    print(json.dumps(asdict(report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
