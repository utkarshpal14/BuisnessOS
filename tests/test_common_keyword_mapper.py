import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.common.keyword_mapper import KeywordMapper, matches_any


class TestKeywordMapper(unittest.TestCase):

    def setUp(self):
        self.mapper = KeywordMapper(
            rules=[
                (["alpha", "a1"], "first"),
                (["beta"], "second"),
            ],
            default="unknown",
        )

    def test_first_matching_rule_wins(self):
        self.assertEqual(self.mapper.resolve("Show me Alpha numbers"), "first")

    def test_second_rule_matches_when_first_does_not(self):
        self.assertEqual(self.mapper.resolve("beta report"), "second")

    def test_no_match_returns_default(self):
        self.assertEqual(self.mapper.resolve("gamma report"), "unknown")

    def test_empty_query_returns_default(self):
        self.assertEqual(self.mapper.resolve(""), "unknown")
        self.assertEqual(self.mapper.resolve(None), "unknown")

    def test_matching_is_case_insensitive(self):
        self.assertEqual(self.mapper.resolve("ALPHA"), "first")


class TestMatchesAny(unittest.TestCase):

    def test_true_when_any_keyword_present(self):
        self.assertTrue(matches_any("Give me a recommendation", ["recommend", "advice"]))

    def test_false_when_no_keyword_present(self):
        self.assertFalse(matches_any("Total revenue", ["recommend", "advice"]))

    def test_handles_empty_text(self):
        self.assertFalse(matches_any("", ["recommend"]))
        self.assertFalse(matches_any(None, ["recommend"]))


if __name__ == "__main__":
    unittest.main()
