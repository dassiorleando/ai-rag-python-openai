# Competency and proof map

The capstone is evaluated by evidence, not familiarity. A competency level counts
only when the repository contains a reproducible proof artifact. The targets below
are practice-level destinations: this repository can demonstrate L4 work and
produce reusable methods toward L5, but L5 is not earned until people outside the
project adopt or learn from those methods.

## Level definitions

| Level | Meaning |
|---|---|
| L1 — Aware | Explain the vocabulary and follow a known path. |
| L2 — Competent | Build the standard approach correctly with review. |
| L3 — Proficient | Build independently, anticipate common failures, estimate, and measure. |
| L4 — Expert | Diagnose unfamiliar systems, make non-obvious trade-offs, and teach the method. |
| L5 — Authority | Produce reusable methods or evidence that others adopt. |

## Target coverage

| Competency | Practice target | Primary milestones | Required proof from this repository |
|---|---:|---|---|
| Evaluation engineering | L5 | 2, 8 | Versioned datasets, calibrated graders, noise floor, CI gate, reusable method |
| Retrieval engineering | L5 | 3, 8 | Six-configuration bake-off, failure taxonomy, measured attribution of gains |
| Context engineering | L4 | 3, 5 | Token budget and a 50% context reduction without loss beyond noise floor |
| Agent and tool architecture | L4 | 6 | Workflow-versus-agent comparison, bounded tools, approvals, trajectory evals |
| Inference economics | L4 | 5, 8 | Cost per business transaction and measured cost-quality curve |
| AI security engineering | L4 | 4, 6, 8 | Threat model, adversarial suite, containment evidence, red-team report |
| Structured interfaces | L4 | 1, 6 | Schemas, evidence fields, repair/human route, downstream failure analysis |
| Data and integration for AI | L4 | 3, 6, 7 | Incremental provenance pipeline and permission-aware enterprise integration |
| Model adaptation judgement | L3 | 8 | Distillation/fine-tuning comparison with quality and cost deltas |
| Production operations | L4 | 5, 7 | OTel traces, Langfuse views, SLOs, failure drills, measured model migration |

Product judgement for probabilistic systems is cross-cutting. Every milestone must
show the user-visible confidence surface, citations or evidence, escape hatch,
empty state, error state, and human path appropriate to its risk.

## Proof drills incorporated into the milestones

- Build a 200-item evaluation set that reveals unexpected failures.
- Hand-grade 50 outputs and calibrate a model judge to at least 85% agreement.
- Run an unchanged evaluation five times and record the noise floor.
- Compare retrieval changes one at a time; never change two variables in one run.
- Include at least 30 out-of-corpus questions in the retrieval bake-off.
- Measure table-answered and prose-answered questions separately.
- Cut context tokens by 50% while holding quality within the noise floor.
- Compare the same task as a deterministic workflow and as an agent.
- Grow a test toolset from 5 to 25 and measure tool-selection degradation.
- Attack authorization, retrieved instructions, approvals, retries, and the kill switch.
- Distil a proven frontier-model result into a smaller model and measure both deltas.
- Diagnose and improve a system that was not originally built in this repository.

## Evidence register

Each completed milestone should add one row.

| Date | Milestone | Dataset/run version | Measurement | Artifact | Competency demonstrated |
|---|---|---|---|---|---|
| 2026-09-03 | 0 | Deterministic Stage 0 suite | 4 tests passed | [Milestone 0 guide](milestones/00-minimal-rag-loop.md) | RAG mechanics; retrieval/generation separation |
| 2026-09-03 | 1 | Deterministic full suite | 37 tests passed | [Milestone 1 guide](milestones/01-architecture-and-tenant-isolation.md) | Structured interfaces; security foundation |
