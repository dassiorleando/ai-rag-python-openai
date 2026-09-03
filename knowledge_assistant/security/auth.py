"""Small API-key authentication boundary for the reference implementation."""

from __future__ import annotations

import hmac
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TenantPrincipal:
    tenant_id: str


class ApiKeyAuthenticator:
    """Resolve tenant identity from a secret instead of user-controlled input.

    Static keys are suitable for this learning project. In a deployed enterprise
    system this port should be backed by an identity provider and short-lived JWTs.
    """

    def __init__(self, api_keys_by_tenant: dict[str, str]) -> None:
        if not api_keys_by_tenant:
            raise ValueError("At least one tenant API key must be configured")
        if len(set(api_keys_by_tenant.values())) != len(api_keys_by_tenant):
            raise ValueError("Tenant API keys must be unique")
        self._api_keys_by_tenant = api_keys_by_tenant.copy()

    def authenticate(self, supplied_key: str) -> TenantPrincipal | None:
        for tenant_id, expected_key in self._api_keys_by_tenant.items():
            if hmac.compare_digest(supplied_key, expected_key):
                return TenantPrincipal(tenant_id)
        return None
