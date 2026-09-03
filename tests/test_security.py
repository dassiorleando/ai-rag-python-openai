import unittest

from knowledge_assistant.security.auth import ApiKeyAuthenticator


class ApiKeyAuthenticatorTests(unittest.TestCase):
    def test_same_key_cannot_be_assigned_to_multiple_tenants(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            ApiKeyAuthenticator({"tenant-a": "shared", "tenant-b": "shared"})
