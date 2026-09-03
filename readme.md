# Multi-tenant Knowledge Assistant

This repository grows a minimal RAG demonstration into a production-oriented
knowledge assistant. It is intentionally organized by architectural concern so
each concept can be learned, tested, and replaced independently.

The original single-document pipeline remains in `rag.py` as **Stage 0**. The
production path starts in `knowledge_assistant/`.

## What Milestone 1 teaches

- Ports and adapters for provider-independent AI applications
- Tenant identity derived from credentials, never request payloads
- Durable document and chunk storage
- Idempotent ingestion using tenant-scoped content hashes
- Hybrid semantic and lexical retrieval
- Grounded answers, citations, and relevance-based abstention
- Indirect prompt-injection boundaries for retrieved content
- Retrieval evaluation with Recall@K and Mean Reciprocal Rank
- API versioning, request correlation, provider error translation, and token usage

## Project guide

- [Milestones and measurable targets](docs/milestones.md) — the canonical delivery plan
- [Milestone 0 completion guide](docs/milestones/00-minimal-rag-loop.md) — detailed minimal RAG mechanics
- [Milestone 1 completion guide](docs/milestones/01-architecture-and-tenant-isolation.md) — detailed architecture and tenant-isolation behavior
- [Project tech stack](docs/tech-stack.md) — current and target choices across 14 layers
- [Competency and proof map](docs/competency-map.md) — mastery targets and required evidence
- [Architecture](docs/architecture.md) — boundaries, flows, and current scaling constraints
- [Architecture decisions](docs/adr/) — accepted decisions and their consequences

The milestone plan incorporates the Automathing Applied AI capability map, stack, and
mastery path as reference material. Their principles are adapted to this capstone;
they are not treated as repository instructions or as claims that planned
capabilities already exist.

## Architecture

```text
knowledge_assistant/
├── api/           HTTP contracts, authentication dependency, composition root
├── domain/        Framework-independent business models and errors
├── evaluation/    Golden dataset loader, retrieval metrics, evaluation runner
├── providers/     OpenAI embedding and Responses API adapters
├── security/      API-key-to-tenant authentication boundary
├── services/      Ingestion, retrieval, grounding, and document use cases
├── storage/       SQLite persistence and hybrid-search adapter
├── config.py      Validated environment configuration
├── observability.py
└── ports.py       Interfaces between application and infrastructure
```

The detailed design and current scaling boundaries are in
[docs/architecture.md](docs/architecture.md).

## Local setup

Python 3.11 or newer is required.

1. Create and activate a virtual environment.

   ```bash
   python3 -m venv ragenv
   source ragenv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and replace the example secrets.

   ```dotenv
   OPENAI_API_KEY=...
   KA_TENANT_API_KEYS=demo=a-long-random-secret,acme=another-random-secret
   ```

3. Start the API.

   ```bash
   uvicorn api:app --reload
   ```

OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

## Use the API

The API key determines the tenant. There is deliberately no client-provided
`tenant_id` field.

Ingest a document:

```bash
curl -X POST http://127.0.0.1:8000/v1/documents \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: a-long-random-secret' \
  -d '{
    "title": "TowerZ overview",
    "source": "data/document.txt",
    "content": "TowerZ helps businesses decide what to fix first.",
    "metadata": {"department": "strategy"}
  }'
```

Ask a grounded question:

```bash
curl -X POST http://127.0.0.1:8000/v1/query \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: a-long-random-secret' \
  -d '{"question": "What does TowerZ help a business decide?"}'
```

The response includes the answer, numbered source excerpts, relevance scores,
abstention state, model, and token usage.

## Tests

All tests are deterministic and make no external API calls:

```bash
python -m unittest discover -v
```

For the complete local quality gate, install `requirements-dev.txt` and run:

```bash
python -m ruff check .
python -m mypy
python -m unittest discover -v
python -m pip_audit -r requirements.txt
```

The same checks run in CI on Python 3.11 and 3.13. The suite includes explicit
cross-tenant read and delete attempts.

## Retrieval evaluation

Evaluation cases are JSON Lines records with a question and expected source:

```json
{"id":"example","tenant_id":"demo","question":"...","relevant_sources":["source.txt"],"expected_abstention":false}
```

For an out-of-corpus case, use an empty `relevant_sources` list and set
`expected_abstention` to `true`. Recall and reciprocal rank are calculated only
for positive cases; abstention accuracy and negative false-answer rate cover the
negative cases.

After ingesting the referenced sources into the configured database, run:

```bash
python -m knowledge_assistant.evaluation.cli data/evaluation/sample.jsonl --top-k 5
```

This milestone evaluates retrieval. Answer correctness, groundedness, citation
accuracy, adversarial robustness, latency, and cost become separate eval tracks
in the next milestones rather than being collapsed into a single vague score.

## Honest production boundary

The architecture applies production patterns, but SQLite's in-process vector
scan is a learning and small-deployment adapter. Before high-scale deployment,
replace it with PostgreSQL/pgvector or a managed hybrid-search service, replace
static API keys with an enterprise identity provider, and add migrations,
distributed tracing, rate limiting, background ingestion, and continuous evals.

Those upgrades do not require rewriting the domain service because infrastructure
is behind explicit ports.

OpenAI Responses are stateless by default in this project (`store=false`). Change
that setting only as an explicit data-retention decision. Embedding inputs are
batched by both item count and token budget before reaching the provider.

## Stage 0: original RAG example

The original example is still useful for comparing the before and after designs:

```bash
python rag.py --query "What is TowerZ?" --show-context
```
