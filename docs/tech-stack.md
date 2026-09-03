# Project tech stack

This is the default stack for the knowledge-assistant capstone. It adapts the
Automathing Applied AI Stack to this repository and distinguishes the durable
assets we own from replaceable infrastructure choices.

The rule is: start from the default, deviate for a measured requirement or client
constraint, and record the decision in an ADR. Versions belong in lock files and
model identifiers belong in configuration.

## Layer map

| Layer | Current implementation | Target default | Ownership |
|---|---|---|---|
| Model gateway | Direct OpenAI adapter | Self-hosted LiteLLM; client gateway when already standardized | Replaceable |
| Model routing | One configured generation model | Task-level cascade: deterministic → small model → frontier escalation | Ours |
| Orchestration | Plain typed Python | Plain code first; LangGraph only for durable pause/resume or complex loops | Replaceable |
| Retrieval | SQLite cosine + lexical overlap | PostgreSQL + pgvector, BM25, RRF, cross-encoder reranking | Replaceable adapter |
| Ingestion | Python, idempotent content hashes | Python pipeline: incremental, provenance-preserving, re-runnable, observable | Ours |
| Memory and state | No conversational memory yet | PostgreSQL with explicit tenant/user scope, retention, validation, and audit | Ours |
| Tools and integration | Not implemented | Narrow typed functions; MCP where reuse or external interoperability justifies it | Partly ours |
| Output contracts | Pydantic HTTP schemas | JSON Schema/constrained decoding + Pydantic, one repair attempt, then human routing | Ours |
| Guardrails | Tenant isolation, abstention, untrusted-source boundary | Deterministic checks first; classifier second; every decision logged | Ours |
| Evaluation | Python/unittest metrics + versioned JSONL | Repository-owned pytest harness, calibrated judges, CI quality gates | Ours |
| Observability | Request ID and structured access log | OpenTelemetry GenAI conventions viewed in Langfuse | Replaceable viewer |
| Model serving | Provider API | API through gateway; vLLM only when residency, latency, or economics require it | Replaceable |
| Application/API | Python FastAPI service | Python for the AI service; TypeScript/Node for a separate product UI when needed | Replaceable edge |
| Infrastructure | Local process and SQLite | Client cloud, containers, infrastructure as code, client CI and secrets manager | Replaceable |

## Non-negotiable architecture rules

1. Model and embedding identifiers live in configuration.
2. Production model calls go through a gateway; provider SDKs stay inside adapters.
3. Prompts, datasets, schemas, and evaluation logic are versioned in this repository.
4. Authorization is enforced server-side before retrieval or action execution.
5. Permission filtering is performed in the datastore query, never after retrieval.
6. Framework code stays in orchestration; domain policies and evaluations remain independent.
7. Instrument to OpenTelemetry conventions rather than directly to an observability vendor.
8. Every write tool supports an idempotency key, dry-run mode, and reversibility class.
9. Every deployed task has a second configured model that has passed the same eval suite.
10. Every dependency, model, prompt, index, and MCP server is inventoried and versioned.
11. Prefer deterministic code, embeddings, classification, or extraction over generation
    when they solve the task more cheaply and reliably.
12. Use browser/computer control only when no suitable API, export, or database view exists.

## Capability selection before stack selection

The first decision is which primitive solves the problem, not which model or
framework to install.

| Need | First candidate | Escalate when |
|---|---|---|
| Arithmetic, sorting, dates, aggregation | Deterministic code execution | The task first requires interpreting unstructured intent |
| Similarity, clustering, deduplication, lightweight routing | Embeddings | Labels or relations require semantic judgement beyond distance |
| Taxonomy assignment | Rules, embeddings, or a small classifier | Ambiguity remains after the taxonomy itself is repaired |
| Fields from documents | Schema-constrained extraction + deterministic validation | Layout or cross-document inference defeats the measured baseline |
| Answers over owned knowledge | Long context for a small stable corpus; otherwise RAG | Multi-hop retrieval is demonstrably required |
| Drafting and transformation | Generation with evidence and an editable artifact | A deterministic template meets the need |
| Business action | Deterministic workflow with one bounded model decision | Runtime planning measurably outperforms the workflow safely |

### Model adaptation ladder

Climb this ladder in order and preserve the evaluation result that justified each
step: prompt and schema → static examples → dynamically retrieved examples →
retrieval/context → distillation → supervised fine-tuning (including LoRA/QLoRA) →
preference optimization → reinforcement fine-tuning against a verifiable reward.
The later rungs are not mandatory implementation targets. Knowing when evidence,
training data, volume, or a verifiable reward does *not* justify them is part of
the target competency.

## Layer decisions

### Model access and routing

Applications will target an internal model-gateway interface. LiteLLM is the
initial production default because it centralizes routing, per-tenant budgets,
rate limits, retries, fallbacks, caching, and cost attribution. A client's existing
gateway takes precedence when adding another control plane would increase their
operational burden.

Routing is per task. Deterministic logic should avoid a model call when possible;
a small model handles classification, extraction, and routing; a stronger model
is reserved for measured reasoning needs. Changes require evaluation, not trust in
provider benchmarks.

### Orchestration

Use ordinary typed application code while control flow is deterministic. Introduce
LangGraph only for durable checkpoints, cross-session approval pauses, complex
branches, or genuine model-directed loops. Framework choice must not own prompts,
retrieval, tools, or evaluation.

### Retrieval and ingestion

The target retrieval path is:

```text
structure-aware chunking
→ contextual enrichment
→ dense + BM25 indexes with permission metadata
→ server-side authorization and metadata filters
→ reciprocal-rank fusion
→ cross-encoder reranking
→ few high-quality chunks with resolvable citations
```

SQLite remains the transparent learning adapter for Milestones 1–2. PostgreSQL
with pgvector becomes the default before scale testing because it combines vector,
keyword, relational, and permission-aware queries in one operational system.

Late chunking, late-interaction retrieval, HyDE, multi-query expansion,
agentic retrieval, and graph augmentation are failure-driven candidates, not
default ingredients. Benchmark one when the baseline error taxonomy points to the
failure it is designed to solve.

The ingestion pipeline remains ours. It must be idempotent, incremental,
provenance-preserving, observable, and safely re-runnable end to end.

### Structured output and guardrails

Schemas are software contracts, not formatting hints. Use required fields, enums,
explicit nulls, evidence fields, and `needs_review` where downstream routing
depends on uncertainty. Validate outside the model, allow at most one schema-repair
attempt, then route to a human.

Prompt hardening is a mitigation, not a security control. Guardrails must execute
outside the model, be able to block or escalate, and emit an auditable decision.

### Evaluation and observability

The evaluation harness and datasets remain repository-owned so they run in CI and
survive a vendor change. Langfuse is the default interface for exploring traces,
prompt versions, production feedback, and evaluation scores—not the source of
truth for datasets or quality gates.

Instrumentation targets OpenTelemetry GenAI semantic conventions. Each request
should eventually capture tenant-safe trace context, model and prompt versions,
token counts, cost, latency by stage, retrieval chunk IDs and scores, tool calls,
guardrail decisions, retries, errors, and feedback. Sensitive content is excluded
or redacted according to policy.

### Serving and infrastructure

Do not self-host models by default. Evaluate vLLM only when data residency,
contractual constraints, sustained volume, or latency makes provider APIs
unsuitable. Benchmark with the real workload and count failed requests.

Deploy into the client's existing cloud and CI wherever possible. Containers,
infrastructure as code, managed secrets, reproducible environments, and tested
backup/restore are required before production readiness.

### Product interface contract

For human-facing flows, stream work that takes noticeable time, make citations
resolve only to sources the user may open, and prefer an editable artifact over a
chat surface when the output is a draft. Every AI surface needs an escape hatch
and designed empty, timeout, guardrail-block, and tool-failure states. Approval
screens must render the real source-system payload rather than the model's summary.

## Current deviations

| Layer | Default | Current choice | Reason | Resolution milestone |
|---|---|---|---|---|
| Gateway | LiteLLM | Direct OpenAI adapter | Keeps Milestone 1 locally understandable | Milestone 5 |
| Retrieval | PostgreSQL + pgvector | SQLite scan | Makes persistence and tenant filtering visible before infrastructure work | Milestone 3/7 |
| Evaluation | pytest harness | unittest foundation | Preserves the existing project while metric contracts form | Milestone 2 |
| Observability | OTel → Langfuse | Structured access log | Trace schema follows after eval event contracts stabilize | Milestone 5 |
| Application edge | TypeScript/Node | FastAPI only | This repository is currently the AI service, not a product UI | Revisit with UI scope |

Review this table at every milestone. A recurring deviation should become a new
default or be retired—not remain accidental architecture.
