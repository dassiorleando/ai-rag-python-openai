# ADR 0002: Derive tenant context from credentials

- Status: Accepted
- Date: 2026-09-03

## Context

Accepting `tenant_id` from a request body or query parameter would let callers
attempt to select another tenant's data.

## Decision

Authenticate `X-API-Key` at the API boundary and resolve it to a `TenantPrincipal`.
Pass that principal's tenant ID explicitly through every use case. Apply tenant
filters in SQL before retrieval scoring or deletion.

## Consequences

The API cannot perform cross-tenant operations by changing payload fields. Static
keys are intentionally a replaceable learning adapter; enterprise deployment must
use an identity provider, short-lived credentials, rotation, and finer-grained ACLs.
