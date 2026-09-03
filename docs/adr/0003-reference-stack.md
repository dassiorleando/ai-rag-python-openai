# ADR 0003: Adopt the Automathing reference stack by layer

- Status: Accepted
- Date: 2026-09-03

## Context

The capability-map, applied-stack, and mastery-path references define a durable
practice model: own evaluation, ingestion, state, output contracts, prompts, and
adapters; keep providers, frameworks, search engines, observability viewers, and
serving infrastructure replaceable.

## Decision

Adopt `docs/tech-stack.md` as this capstone's default stack. Preserve the current
SQLite, direct-provider, unittest, and FastAPI choices as explicit learning-stage
deviations with resolution milestones. Require measured evidence and an ADR for
future deviations.

## Consequences

The repository gains a clear target without pretending its first milestone already
implements every production layer. Langfuse is the default observability viewer,
while OpenTelemetry remains the instrumentation contract. PostgreSQL/pgvector and
LiteLLM become planned adapters rather than immediate rewrites that would obscure
the concepts currently being learned.
