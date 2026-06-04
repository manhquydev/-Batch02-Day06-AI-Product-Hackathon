"""Rank TMDB search hits by title similarity to the user query."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

# Minimum relevance to keep a search result (0–1).
MIN_TITLE_MATCH_SCORE = 0.48


def normalize_title(text: str) -> str:
    text = text.strip().lower()
    decomposed = unicodedata.normalize("NFD", text)
    no_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    no_accents = re.sub(r"[^\w\s]", " ", no_accents)
    return re.sub(r"\s+", " ", no_accents).strip()


def _query_tokens(query: str) -> List[str]:
    normalized = normalize_title(query)
    return [t for t in normalized.split() if len(t) >= 2]


def score_title_relevance(query: str, title: str) -> float:
    """
    Higher = closer title match.
    Requires query tokens to appear in the same order in the title (reduces false positives
    like 'Cầm Tâm' when searching 'Tấm Cám').
    """
    q = normalize_title(query)
    t = normalize_title(title)
    if not q or not t:
        return 0.0

    if q in t:
        return 1.0

    tokens = _query_tokens(query)
    if not tokens:
        return SequenceMatcher(None, q, t).ratio()

    if not all(tok in t for tok in tokens):
        return 0.0

    pos = 0
    for tok in tokens:
        idx = t.find(tok, pos)
        if idx < 0:
            return 0.0
        pos = idx + len(tok)

    ratio = SequenceMatcher(None, q, t).ratio()
    coverage = sum(len(tok) for tok in tokens) / max(len(q), 1)
    return min(1.0, 0.55 + 0.25 * coverage + 0.35 * ratio)


def rank_search_results(
    results: List[Dict[str, Any]],
    query: str,
    *,
    min_score: float = MIN_TITLE_MATCH_SCORE,
) -> List[Tuple[float, Dict[str, Any]]]:
    """Return (score, movie) pairs sorted by relevance, dropping weak matches."""
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for movie in results:
        title = movie.get("title") or movie.get("original_title") or ""
        score = score_title_relevance(query, str(title))
        if score >= min_score:
            scored.append((score, movie))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored
