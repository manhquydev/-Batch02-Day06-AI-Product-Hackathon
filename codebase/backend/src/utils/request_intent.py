"""Detect user intent: list recommendations vs. one-movie details vs. reviews."""

from __future__ import annotations

import re
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
    "ve bo phim",
    "ve cuon phim",
)

_REVIEW_CUES = (
    "review phim",
    "review ve",
    "review cua",
    "danh gia phim",
    "danh gia ve",
    "nhan xet phim",
    "nhan xet ve",
    "binh luan phim",
    "binh luan ve",
    "doc review",
    "xem review",
    "user review",
    "danh gia cua",
    "nhan xet cua",
)

_COMPARE_CUES = (
    "so sanh",
    "compare",
    "doi chieu",
)

_TITLE_PATTERNS = [
    re.compile(
        r"(?:biet them|thong tin|chi tiet|ke (?:cho|ve)?|tim hieu|gioi thieu|noi (?:them )?ve)\s+"
        r"(?:ve\s+)?(?:bo\s+)?phim\s+(.+)$",
        re.I,
    ),
    re.compile(
        r"(?:review|danh gia|nhan xet|binh luan)\s+(?:ve\s+)?(?:bo\s+)?phim\s+(.+)$",
        re.I,
    ),
    re.compile(r"(?:ve|about)\s+(?:bo\s+)?phim\s+(.+)$", re.I),
    re.compile(r"phim\s+(.+?)\s+(?:la gi|co gi|co hay|the nao|review|danh gia|nhan xet)", re.I),
    re.compile(r"them\s+ve\s+phim\s+(.+)$", re.I),
    re.compile(r"(?:review|danh gia|nhan xet)\s+(.+)$", re.I),
]


def is_movie_review_request(message: str) -> bool:
    """True when the user wants TMDB user reviews, not metadata or a new list."""
    normalized = _normalize(message)
    if not normalized:
        return False
    if any(cue in normalized for cue in _COMPARE_CUES):
        return False
    if any(cue in normalized for cue in _REVIEW_CUES):
        return True
    if re.search(r"\breview\b", normalized) and re.search(r"\bphim\b", normalized):
        return True
    if re.search(r"\b(danh gia|nhan xet|binh luan)\b", normalized) and re.search(
        r"\bphim\b", normalized
    ):
        return True
    return False


def is_movie_detail_request(message: str) -> bool:
    """True when the user wants info about one specific film, not a new list."""
    if is_movie_review_request(message):
        return False
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
    """Best-effort movie title from a detail- or review-style question."""
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
    for prefix in (
        r"(?:biet them|thong tin|chi tiet|ke ve|tim hieu|gioi thieu|noi ve|review|danh gia|nhan xet)\s+"
        r"(?:ve\s+)?phim\s+(.+)$",
    ):
        match = re.search(prefix, normalized)
        if match:
            return match.group(1).strip()

    return None
