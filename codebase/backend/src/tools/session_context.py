"""Per-request exclusions for chat session follow-ups (no duplicate TMDB ids)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional, Set

from src.utils.request_limits import DEFAULT_MOVIES

_excluded_ids: ContextVar[Set[int]] = ContextVar("tmdb_excluded_ids", default=set())
_discover_start_page: ContextVar[int] = ContextVar("tmdb_discover_start_page", default=1)
_requested_movie_limit: ContextVar[int] = ContextVar("requested_movie_limit", default=DEFAULT_MOVIES)
_detail_mode: ContextVar[bool] = ContextVar("movie_detail_mode", default=False)
_focus_movie_id: ContextVar[Optional[int]] = ContextVar("focus_movie_id", default=None)
_focus_movie_title: ContextVar[Optional[str]] = ContextVar("focus_movie_title", default=None)


def set_session_exclusions(
    movie_ids: list[int],
    *,
    discover_start_page: int = 1,
) -> None:
    """Call before agent run when session has prior suggested movies."""
    _excluded_ids.set({int(mid) for mid in movie_ids if mid})
    _discover_start_page.set(max(1, int(discover_start_page)))


def get_excluded_ids() -> Set[int]:
    return set(_excluded_ids.get())


def get_discover_start_page() -> int:
    return _discover_start_page.get()


def set_requested_movie_limit(count: int) -> None:
    _requested_movie_limit.set(max(1, min(10, int(count))))


def get_requested_movie_limit() -> int:
    return _requested_movie_limit.get()


def set_movie_detail_focus(title: str, movie_id: Optional[int] = None) -> None:
    _detail_mode.set(True)
    _focus_movie_title.set(title.strip())
    _focus_movie_id.set(int(movie_id) if movie_id is not None else None)


def is_movie_detail_mode() -> bool:
    return _detail_mode.get()


def get_focus_movie_id() -> Optional[int]:
    return _focus_movie_id.get()


def get_focus_movie_title() -> Optional[str]:
    return _focus_movie_title.get()


def clear_session_exclusions() -> None:
    _excluded_ids.set(set())
    _discover_start_page.set(1)
    _requested_movie_limit.set(DEFAULT_MOVIES)
    _detail_mode.set(False)
    _focus_movie_id.set(None)
    _focus_movie_title.set(None)
