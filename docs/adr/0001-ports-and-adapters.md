# ADR 0001: Isolate AI and storage vendors behind ports

- Status: Accepted
- Date: 2026-09-03

## Context

The original pipeline directly coupled use-case logic to FAISS, LangChain, and
OpenAI. Production systems need to change models, indexes, and persistence without
rewriting tenant and grounding policies.

## Decision

Define `EmbeddingProvider`, `AnswerGenerator`, and `KnowledgeRepository` ports.
Keep orchestration in a framework-independent `KnowledgeAssistant` service. Wire
concrete adapters only in the API composition root.

## Consequences

Tests can run deterministically without network calls. Vendor migrations become
adapter changes, but interfaces must remain deliberately small and domain-focused.
