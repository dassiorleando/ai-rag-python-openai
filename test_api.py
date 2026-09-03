"""Compatibility smoke test for the top-level ASGI entry point."""

import unittest

from api import app


class ApiEntryPointTests(unittest.TestCase):
    def test_top_level_module_exports_the_production_app(self):
        self.assertEqual(app.title, "Multi-tenant Knowledge Assistant")


if __name__ == "__main__":
    unittest.main()
