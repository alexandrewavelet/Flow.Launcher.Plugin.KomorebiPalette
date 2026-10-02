"""Forgiving search: prefixes, abbreviations, typos and accents."""

from __future__ import annotations

import difflib
import unicodedata
from typing import Sequence


def normalize(text: str) -> str:
    """Lowercase and strip accents: 'Défilement' -> 'defilement'."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def tokenize(text: str) -> list:
    return normalize(text).split()


def word_score(token: str, word: str) -> int:
    """How well one typed token matches one word (0 = no match)."""
    if word.startswith(token):
        return 100
    if len(token) >= 3 and token in word:
        return 80
    if len(token) >= 4:  # typo: "cetner" -> "center", "tilling" -> "tiling"
        ratio = max(difflib.SequenceMatcher(None, token, word).ratio(),
                    difflib.SequenceMatcher(None, token, word[: len(token)]).ratio())
        if ratio >= 0.75:
            return int(ratio * 70)
    # Abbreviation: same first letter, letters in order ("cntr" -> "center")
    if len(token) >= 2 and token[0] == word[0] and len(word) <= len(token) * 3:
        remaining = iter(word)
        if all(char in remaining for char in token):
            return 50
    return 0


def match_score(tokens: Sequence[str], text: str) -> int:
    """Every token must match a word of `text`; 0 means no match."""
    if not tokens:
        return 1
    words = tokenize(text)
    total = 0
    for token in tokens:
        best = max((word_score(token, word) for word in words), default=0)
        if best == 0:
            return 0
        total += best
    return total
