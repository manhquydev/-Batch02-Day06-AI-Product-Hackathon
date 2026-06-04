"""Detect user intent: list recommendations vs. one-movie details."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from src.utils.request_limits import _normalize


_DETAIL_CUES = (
    "biet them",
    "cho biet them",
    "cho minh biet",
    "cho toi biet",
    "thong tin",
    "chi tiet",
    "ke ve",
    "ke cho",
    "ke minh nghe",
    "tim hieu",
    "gioi thieu",
    "noi ve",
    "noi them",
    "mo ta",
    "review phim",
    "danh gia phim",
    "ve bo phim",
    "ve cuon phim",
)

_TITLE_PATTERNS = [
    re.compile(
        r"(?:biet them|thong tin|chi tiet|ke (?:cho|ve)?|tim hieu|gioi thieu|noi (?:them )?ve)\s+"
        r"(?:ve\s+)?(?:bo\s+)?phim\s+(.+)$",
        re.I,
    ),
    re.compile(r"(?:ve|about)\s+(?:bo\s+)?phim\s+(.+)$", re.I),
    re.compile(r"phim\s+(.+?)\s+(?:la gi|co gi|co hay|the nao)", re.I),
    re.compile(r"them\s+ve\s+phim\s+(.+)$", re.I),
]


def is_movie_detail_request(message: str) -> bool:
    """True when the user wants info about one specific film, not a new list."""
    normalized = _normalize(message)
    if not normalized:
        return False
    if any(cue in normalized for cue in _DETAIL_CUES):
        return True
    if re.search(r"\bphim\s+\S+", normalized) and re.search(
        r"\b(biet|thong tin|chi tiet|ke ve|tim hieu|gioi thieu)\b", normalized
    ):
        return True
    return False


def extract_target_movie_title(message: str) -> Optional[str]:
    """Best-effort movie title from a detail-style question."""
    raw = message.strip()
    if not raw:
        return None

    for pattern in _TITLE_PATTERNS:
        match = pattern.search(raw)
        if match:
            title = match.group(1).strip(" ?!.,")
            if len(title) >= 2:
                return title

    normalized = _normalize(raw)
    match = re.search(
        r"(?:biet them|thong tin|chi tiet|ke ve|tim hieu|gioi thieu|noi ve)\s+(?:ve\s+)?phim\s+(.+)$",
        normalized,
    )
    if match:
        return match.group(1).strip()

    return None
