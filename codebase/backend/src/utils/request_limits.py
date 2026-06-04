"""Parse how many movies the user asked for from their message."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

MIN_MOVIES = 1
MAX_MOVIES = 10
DEFAULT_MOVIES = 5

# Ordered: more specific patterns first
_COUNT_PATTERNS = [
    re.compile(r"\b(\d{1,2})\s*(?:bo\s*)?phim\b", re.I),
    re.compile(r"\bphim\s*(\d{1,2})\b", re.I),
    re.compile(r"\b(?:goi\s*y|đề\s*xuất|đề xuất|cho|tim|lấy|lay|top)\s*(?:toi|tôi|minh|mình)?\s*(\d{1,2})\b", re.I),
    re.compile(r"\b(\d{1,2})\s*(?:movies?|films?|titles?)\b", re.I),
    re.compile(r"\b(\d{1,2})\s*(?:cai|cuon|bộ)\b", re.I),
]


def _normalize(text: str) -> str:
    text = text.strip().lower()
    decomposed = unicodedata.normalize("NFD", text)
    no_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", no_accents)


def parse_requested_movie_count(message: str) -> Optional[int]:
    """
    Extract requested movie count from user text.
    Returns None if no explicit number (caller should use DEFAULT_MOVIES).
    """
    normalized = _normalize(message)
    if not normalized:
        return None

    for pattern in _COUNT_PATTERNS:
        match = pattern.search(normalized)
        if match:
            value = int(match.group(1))
            return max(MIN_MOVIES, min(MAX_MOVIES, value))

    return None


def clamp_movie_count(value: Optional[int]) -> int:
    if value is None:
        return DEFAULT_MOVIES
    return max(MIN_MOVIES, min(MAX_MOVIES, int(value)))
