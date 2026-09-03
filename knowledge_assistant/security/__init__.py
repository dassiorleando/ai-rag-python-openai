"""Authentication and tenant-boundary policies."""

from knowledge_assistant.security.auth import ApiKeyAuthenticator, TenantPrincipal

__all__ = ["ApiKeyAuthenticator", "TenantPrincipal"]
