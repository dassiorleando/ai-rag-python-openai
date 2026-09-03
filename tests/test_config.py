import unittest

from pydantic import ValidationError

from knowledge_assistant.config import Settings


class SettingsTests(unittest.TestCase):
    def test_top_k_limits_must_be_positive_and_ordered(self):
        for values in (
            {"default_top_k": 0},
            {"maximum_top_k": 0},
            {"default_top_k": 21, "maximum_top_k": 20},
        ):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                Settings(_env_file=None, **values)

    def test_chunk_overlap_must_be_smaller_than_chunk_size(self):
        with self.assertRaises(ValidationError):
            Settings(_env_file=None, chunk_size=100, chunk_overlap=100)

    def test_document_size_must_be_positive(self):
        with self.assertRaises(ValidationError):
            Settings(_env_file=None, maximum_document_characters=0)
