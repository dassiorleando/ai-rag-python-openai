# Milestones and measurable targets

This is the canonical delivery plan for turning the original RAG experiment into
a production-grade, multi-tenant knowledge assistant. It tracks both engineering
outcomes and the AI architecture concepts each milestone is intended to teach.

Target values are initial quality gates, not universal industry standards. Record
the dataset version, corpus size, hardware, model, prompt, and index version with
every result so comparisons remain meaningful.

The architectural defaults behind these targets are in [tech-stack.md](tech-stack.md).
The intended proficiency levels and required proof artifacts are mapped in
[competency-map.md](competency-map.md). This sequence is adapted to this capstone:
it develops one production system progressively rather than treating the reference
learning exercises as unrelated demos.

## Status overview

| Milestone | Outcome | Status |
|---|---|---|
| 0 | Understand the minimal RAG loop | Complete |
| 1 | Establish production-oriented application boundaries | Complete |
| 2 | Make quality measurable with continuous evaluations | Next |
| 3 | Build high-quality ingestion, retrieval, and context assembly | Planned |
| 4 | Enforce enterprise security and governance | Planned |
| 5 | Add LLMOps, reliability, and cost controls | Planned |
| 6 | Add one bounded agentic workflow | Planned |
| 7 | Prove scalability and deployment readiness | Planned |
| 8 | Run architecture experiments and publish findings | Planned |

## Completed milestone guides

Each completed milestone has a code-grounded guide explaining its runtime flow,
design decisions, failure behavior, tests, limitations, and learning exercises:

- [Milestone 0 — Minimal RAG loop](milestones/00-minimal-rag-loop.md)
- [Milestone 1 — Architecture and tenant isolation](milestones/01-architecture-and-tenant-isolation.md)

These guides describe what exists today. The sections below remain the canonical
checklist and sequencing plan for completed and future work.

When a future milestone is marked complete, add
`docs/milestones/NN-descriptive-name.md` in the same change. Its minimum contents
are the implemented flows, design decisions, configuration, failure behavior,
test and measurement evidence, known limitations, and practical learning
exercises.

## Global definition of done

A milestone is complete only when:

- Its deliverables are implemented and documented.
- Unit, integration, isolation, and relevant adversarial tests pass.
- Metrics are captured against a versioned dataset or load profile.
- Stochastic results include repeated runs and a measured noise floor.
- Architecture decisions and important trade-offs are recorded in an ADR.
- Configuration, operating instructions, and failure modes are documented.
- No unresolved critical security or cross-tenant data exposure exists.
- The evidence register in `competency-map.md` links to a reproducible artifact.
- New human-facing behavior has evidence, escape, empty, error, and human-review
  states appropriate to its risk.

## Milestone 0 — Minimal RAG loop

**Status:** Complete

**Detailed implementation guide:**
[Milestone 0 — Minimal RAG loop](milestones/00-minimal-rag-loop.md)

### Outcome

Understand the mechanics of loading, chunking, embedding, retrieving, prompting,
and generating an answer from one document.

### Learning targets

- Embeddings and vector similarity
- Chunk size, overlap, and top-k retrieval
- Context construction and grounded prompting
- Difference between retrieval and generation

### Deliverables

- [x] Single-document ingestion
- [x] FAISS similarity search
- [x] OpenAI answer generation
- [x] Basic command-line and API examples
- [x] Deterministic unit tests

### Exit criteria

- [x] A known question retrieves the expected chunk.
- [x] Only retrieved context is sent to the generator.
- [x] Unit tests make no external API calls.

## Milestone 1 — Architecture and tenant isolation

**Status:** Complete

**Detailed implementation guide:**
[Milestone 1 — Architecture and tenant isolation](milestones/01-architecture-and-tenant-isolation.md)

### Outcome

Create a durable, modular application in which tenant identity and business
policies are independent from model, database, and web-framework choices.

### Learning targets

- Ports-and-adapters architecture
- Domain models and application services
- Trust boundaries and tenant context propagation
- Idempotency and transactional persistence
- Hybrid semantic and lexical retrieval
- Grounded answers, citations, and abstention

### Deliverables

- [x] Separate domain, service, API, security, provider, storage, and evaluation packages
- [x] Credential-derived tenant principal
- [x] Tenant-scoped documents, chunks, retrieval, listing, and deletion
- [x] Durable SQLite reference adapter
- [x] Tenant-scoped content-hash idempotency
- [x] Hybrid semantic/lexical scoring
- [x] Relevance-based abstention before generation
- [x] Deterministic citation objects and token-usage reporting
- [x] Validation that generated citation numbers refer to retrieved sources
- [x] Embedding batches bounded by item count and token budget
- [x] Provider-neutral application errors and HTTP translation
- [x] Cross-field configuration validation
- [x] Untrusted-source serialization and grounding instructions
- [x] Retrieval metric primitives and JSONL dataset loader
- [x] Architecture documentation and ADRs

### Exit criteria

- [x] Cross-tenant retrieval returns no foreign chunks.
- [x] Cross-tenant deletion returns the same result as a missing document.
- [x] Duplicate ingestion within one tenant is idempotent.
- [x] The same content can exist independently in different tenants.
- [x] Empty-tenant queries abstain without calling the generator.
- [x] The complete deterministic suite passes.
- [x] Whitespace-only and configured-limit request errors return 422, not 500.
- [x] Large embedding workloads are split before reaching provider limits.

## Milestone 2 — Evaluation engineering

**Status:** Next

### Outcome

Replace anecdotal quality judgments with repeatable retrieval, answer, citation,
abstention, safety, latency, and cost measurements.

### Learning targets

- Golden datasets and representative sampling
- Recall@K, precision, MRR, nDCG, and ranking analysis
- Groundedness, correctness, completeness, and citation grading
- Deterministic versus model-based versus human grading
- Grader calibration and disagreement analysis
- Regression gates and metric slicing

### Deliverables

- [ ] At least 200 versioned end-to-end evaluation cases
- [ ] A 100-query retrieval slice containing at least 30 no-answer questions
- [ ] Positive, negative, ambiguous, multi-hop, temporal, and adversarial cases
- [ ] Expected source, answer facts, abstention, and tenant fields per case
- [ ] Retrieval and end-to-end evaluation runners
- [ ] Deterministic citation and abstention graders
- [ ] Calibrated model-based correctness and groundedness graders
- [ ] Human grading of at least 50 outputs and a grader agreement report
- [ ] Five unchanged runs to establish the evaluation noise floor
- [ ] Per-case latency, token, and estimated-cost capture
- [ ] CI regression report with failure slices

### Initial exit targets

- Recall@5: at least 0.90
- Mean Reciprocal Rank: at least 0.80
- Groundedness pass rate: at least 0.95
- Citation precision: at least 0.95
- Abstention F1: at least 0.90
- Cross-tenant leakage: exactly 0 cases
- Model-judge agreement with calibrated human labels: at least 0.85
- Claimed improvements exceed the measured noise floor
- Evaluation results reproducible from a committed dataset version

## Milestone 3 — Retrieval, ingestion, and context quality

**Status:** Planned

### Outcome

Reliably ingest real enterprise content and retrieve the smallest sufficient set
of authoritative passages.

### Learning targets

- Parsing, OCR, normalization, provenance, and document lifecycle
- BM25 and dense retrieval
- Metadata filtering and query planning
- Query rewriting, decomposition, and multi-hop retrieval
- Reranking and context selection
- Structure-aware chunking, contextual enrichment, and context budgets
- Retrieval versus long-context trade-offs
- Index freshness and deletion guarantees

### Deliverables

- [ ] PDF, HTML, Markdown, and plain-text ingestion adapters
- [ ] OCR path for scanned documents with quality flags
- [ ] Source checksum, version, page/section, and ingestion-time provenance
- [ ] Metadata filters applied before ranking
- [ ] PostgreSQL/pgvector adapter with server-side tenant and permission filters
- [ ] BM25 plus dense-vector retrieval fused with reciprocal-rank fusion
- [ ] Query rewrite/decomposition policy with bounded retrieval budget
- [ ] Cross-encoder or model-based reranker behind a port
- [ ] Structure-aware chunking and contextual-enrichment variants
- [ ] Six-configuration bake-off changing one retrieval variable per run
- [ ] Failure-driven decision record for late chunking, late interaction, HyDE,
      multi-query, agentic retrieval, and graph augmentation
- [ ] Separate result slices for table-answered and prose-answered questions
- [ ] Long-context baseline run against the same versioned evaluation set
- [ ] Context-token budget with evidence that included passages are necessary
- [ ] Incremental update, re-index, and hard-delete workflows
- [ ] Chunking and retrieval configuration experiment report

### Initial exit targets

- At least five supported source formats with provenance-preserving citations
- At least 5 percentage-point Recall@5 improvement over Milestone 2 baseline, or
  maintenance of the quality target with a documented latency/cost reduction
- Hit@5, Hit@10, rank distribution, latency, and cost reported for every variant
- Each material gain attributable to one isolated retrieval or context change
- Deleted content absent from retrieval within the defined freshness SLO
- No duplicate active chunks after repeated ingestion or re-indexing
- Parser failures surfaced as explicit job failures rather than silent omissions

## Milestone 4 — Security, identity, and governance

**Status:** Planned

### Outcome

Protect data and actions under realistic enterprise identity, authorization,
privacy, and adversarial-input conditions.

### Learning targets

- Zero trust and least privilege
- OIDC/JWT validation and role-based access
- Document-level authorization-aware retrieval
- Indirect prompt injection and document poisoning
- PII classification, retention, residency, and auditability
- Threat modelling and red-team operations

### Deliverables

- [ ] OIDC/JWT authentication adapter with key rotation
- [ ] Tenant, role, group, and document-level authorization policies
- [ ] Authorization filters applied before retrieval scoring
- [ ] Prompt-injection and poisoned-document corpus
- [ ] PII detection/redaction policy and retention jobs
- [ ] Immutable security audit event contract
- [ ] Data deletion verification and evidence report
- [ ] Provider/data-residency routing policy
- [ ] Deterministic guardrails outside the model that can block, escalate, and log
- [ ] Approval boundary for any future action with side effects
- [ ] Threat model and red-team runbook

### Initial exit targets

- Zero unauthorized documents returned across the adversarial authorization suite
- Zero write actions caused by retrieved document instructions
- Every protected operation emits an attributable audit event
- Guardrail decisions remain enforceable when the model or retrieved text disagrees
- Credential rotation succeeds without downtime in an integration test
- Tenant deletion removes active data and produces verifiable completion evidence

## Milestone 5 — LLMOps, reliability, and FinOps

**Status:** Planned

### Outcome

Operate the assistant as a measurable service with explicit reliability, latency,
quality, and cost objectives.

### Learning targets

- Distributed tracing and AI-specific telemetry
- SLOs, error budgets, and incident response
- Prompt/model/index version lineage
- Rate limiting, quotas, retries, fallbacks, and circuit breakers
- Caching and model routing
- Gateway-based provider portability and task-level model cascades
- Vendor-neutral telemetry with a replaceable trace viewer
- Per-tenant cost attribution and capacity planning

### Deliverables

- [ ] LiteLLM gateway adapter with per-task model routes and an evaluated fallback
- [ ] OpenTelemetry GenAI traces spanning API, authentication, retrieval, and generation
- [ ] Langfuse deployment/view configured from the OpenTelemetry signal
- [ ] Metrics for latency, errors, abstention, tokens, cost, and retrieval quality
- [ ] Prompt, model, embedding, corpus, and index version attached to every trace
- [ ] Retrieved chunk IDs/scores, guardrail decisions, retries, and errors on traces
- [ ] Background ingestion queue with retries and dead-letter handling
- [ ] Per-tenant quotas and rate limits
- [ ] Timeout, retry, fallback, and circuit-breaker policies
- [ ] Safe semantic/exact caching with tenant-aware cache keys
- [ ] SLO dashboard, alerts, and incident runbooks
- [ ] Database migration and backup/restore automation
- [ ] Three reasoning-effort settings compared across two model tiers
- [ ] Context-token reduction experiment targeting 50% fewer input tokens

### Initial exit targets

- Query availability SLO: 99.9% for the defined production profile
- p95 latency and cost budgets defined per query class and enforced in CI/load tests
- No retry amplification during provider-failure simulations
- Every production answer traceable to exact model, prompt, and index versions
- At least one alternate model passes the same repository-owned evaluation suite
- A measured cost-quality curve identifies the cheapest route within the quality gate
- Context input is reduced by 50%, or the report explains with evidence why doing so
  would move quality beyond the measured noise floor
- Backup restoration meets documented RPO and RTO targets

## Milestone 6 — Bounded agentic workflow

**Status:** Planned

### Outcome

Extend the assistant from answering questions to completing one valuable business
task while keeping autonomy, side effects, and failure recovery tightly bounded.

### Learning targets

- Function calling and structured outputs
- Deterministic orchestration versus model-directed decisions
- Durable workflow state and idempotent tools
- Typed tool contracts and reusable MCP integration boundaries
- Human-in-the-loop approval
- Compensation, retries, budgets, and stopping conditions
- Task-level agent evaluation

### Deliverables

- [ ] Three to four real enterprise tools, including at least one read-only tool
- [ ] One idempotent write tool with dry-run mode and a reversibility classification
- [ ] One MCP server exposing a reusable, narrowly scoped integration
- [ ] Explicit approval record required before every write
- [ ] Durable workflow and tool-call state
- [ ] Tool input/output schemas and validation
- [ ] Retry, timeout, call-count, token, and cost budgets
- [ ] Audit evidence and compensating action for failed writes
- [ ] Agent task-success and policy-compliance evaluation suite
- [ ] Deterministic-workflow versus agent-directed implementation comparison
- [ ] Tool-selection experiment that grows a test catalog from 5 to 25 tools
- [ ] Exercised operator kill switch and recovery procedure

### Initial exit targets

- Task success rate: at least 0.90 on the versioned workflow dataset
- Unapproved write rate: exactly 0
- Duplicate side effects during retries: exactly 0
- Tool-selection degradation is measured and informs the exposed tool catalog
- Every action linked to user intent, evidence, approval, and final outcome
- Workflow stops safely when evidence, permission, or budget is insufficient

## Milestone 7 — Scale and deployment readiness

**Status:** Planned

### Outcome

Prove that the architecture meets its isolation, freshness, reliability, and cost
targets at a documented enterprise load profile.

### Learning targets

- Managed versus self-hosted search infrastructure
- Horizontal scaling and workload isolation
- Asynchronous ingestion and backpressure
- Capacity testing and noisy-neighbour control
- Deployment strategies and disaster recovery
- Regional architecture and data residency

### Deliverables

- [ ] Validate and tune the PostgreSQL/pgvector retrieval adapter at the load profile
- [ ] Automated schema and index migrations
- [ ] Containerized service and infrastructure-as-code baseline
- [ ] Separate online query and background ingestion workloads
- [ ] Load, soak, failover, and noisy-neighbour test suites
- [ ] Canary or blue/green deployment with automated rollback
- [ ] Multi-region/residency decision record
- [ ] Disaster-recovery exercise report

### Initial exit targets

- Load profile covers at least 100 tenants and 1 million chunks
- Tenant isolation remains perfect under concurrent load
- Defined p95/p99 latency and error-rate SLOs hold during the soak test
- One tenant cannot exhaust another tenant's reserved capacity
- Rollback and disaster recovery succeed within documented RTO/RPO targets

## Milestone 8 — Architecture experiments and portfolio evidence

**Status:** Planned

### Outcome

Use measured evidence to make and communicate senior-level architecture decisions
rather than presenting one implementation as universally optimal.

### Learning targets

- Build-versus-buy analysis
- Model and provider portability
- Model adaptation and training-method selection
- Quality/latency/cost trade-offs
- Experiment design and architectural governance
- Executive and engineering communication

### Deliverables

- [ ] RAG versus long-context comparison
- [ ] Prompting versus supervised fine-tuning comparison
- [ ] Adaptation-ladder decision record covering examples, retrieval, distillation,
      SFT/LoRA, preference optimization, and verifiable-reward training
- [ ] Large-model versus routed-small-model comparison
- [ ] Hosted versus self-managed retrieval comparison
- [ ] Deterministic workflow versus agent-directed workflow comparison
- [ ] Distillation experiment from a proven stronger-model result to a smaller model
- [ ] Total-cost-of-ownership model
- [ ] Red-team and rebuild exercise on an unfamiliar AI system
- [ ] Final architecture, threat model, SLO, and evaluation reports
- [ ] Demonstrable system and concise portfolio case study

### Exit criteria

- Each recommendation cites a versioned experiment and its limitations.
- Quality, security, latency, operational complexity, and cost are compared together.
- The chosen architecture has documented rejection reasons for credible alternatives.
- The distillation report includes quality, latency, and cost deltas on the same dataset.
- The unfamiliar-system exercise records diagnosis, intervention, and measured outcome.
- Another engineer can reproduce the main results from repository instructions.

## Recommended execution order

Milestones 0 and 1 are complete. Continue sequentially through Milestone 5 because
evaluation, retrieval, security, and operations establish the safety envelope for
tools. Build Milestone 6 only after those controls exist. Milestones 7 and 8 then
prove the design under scale and turn implementation experience into reusable
architecture judgment.

Evaluation comes before optimization so later claims have a stable yardstick.
Retrieval and context quality come before model adaptation because missing or noisy
evidence is rarely repaired by a different model. Security and operational controls
come before write-capable tools because an agent amplifies both permissions and
failure modes. Scale and portfolio evidence come last because they should validate
a measured design, not compensate for an unclear one.

## Concepts covered across the capstone

- RAG, embeddings, chunking, hybrid retrieval, reranking, context engineering,
  long-context comparison, citations, groundedness, and abstention
- Golden datasets, deterministic and model-based graders, human calibration,
  retrieval and task metrics, failure slices, CI regression gates, and noise floors
- Structured outputs, typed tool contracts, MCP, deterministic workflows,
  bounded agents, durable execution, approvals, compensation, and kill switches
- Multi-tenancy, OIDC/JWT, permission-aware retrieval, prompt-injection defense,
  PII policy, auditability, residency, and red-team practice
- Model gateways, per-task cascades, caching, fallbacks, OpenTelemetry, Langfuse,
  SLOs, incident response, per-tenant cost attribution, and inference economics
- PostgreSQL/pgvector, incremental ingestion, provenance, containers,
  infrastructure as code, capacity testing, disaster recovery, and model portability
- Prompting versus fine-tuning/distillation, hosted versus self-managed systems,
  build-versus-buy analysis, and evidence-based architecture decisions

The capstone intentionally does not equate installing a framework with learning a
capability. LangGraph, Langfuse, LiteLLM, pgvector, MCP, or vLLM is introduced only
where the milestone has a concrete problem and a measurable success condition.

## Coverage boundary

This capstone goes deep on the grounded knowledge-assistant blueprint and then adds
one bounded operational workflow. It directly exercises retrieval, evaluation,
context, structured interfaces, multi-tenancy, security, observability, cost,
operations, tools, MCP, agents, and model-adaptation judgement.

The broader capability map also covers document extraction, classification,
text-to-SQL, translation, voice, multimodal generation, browser/computer use,
monitoring, and automated decisions affecting individuals. This repository may
use extraction or classification inside its pipeline, but it does not claim
production mastery of every one of those product categories. They need separate
datasets, risk controls, interfaces, and capstones; adding their names here would
not constitute learning them.
