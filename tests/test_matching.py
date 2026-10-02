import unittest

from plugin.matching import match_score, normalize, tokenize


class NormalizeTest(unittest.TestCase):

    def test_strips_accents_and_case(self):
        self.assertEqual(normalize("Défilement Écran"), "defilement ecran")

    def test_tokenize(self):
        self.assertEqual(tokenize("  Send  3 "), ["send", "3"])


class MatchScoreTest(unittest.TestCase):

    def test_empty_query_matches_everything(self):
        self.assertGreater(match_score([], "Toggle float"), 0)

    def test_prefix(self):
        self.assertGreater(match_score(["tog"], "Toggle float"), 0)

    def test_typo(self):
        self.assertGreater(match_score(["tilling"], "Toggle tiling"), 0)
        self.assertGreater(match_score(["cetner"], "Promote to main tile center"), 0)

    def test_abbreviation(self):
        self.assertGreater(match_score(["cntr"], "center"), 0)

    def test_every_token_must_match(self):
        self.assertEqual(match_score(["toggle", "zzz"], "Toggle float"), 0)

    def test_unrelated_word_does_not_match(self):
        self.assertEqual(match_score(["zen"], "Force restart komorebi kill stuck"), 0)

    def test_prefix_beats_typo(self):
        self.assertGreater(match_score(["tiling"], "tiling"), match_score(["tilling"], "tiling"))


if __name__ == "__main__":
    unittest.main()
