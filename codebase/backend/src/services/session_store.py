"""In-memory chat sessions for guest UI (demo)."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional, Set
import uuid

TURN_LIMIT = 10
RECENT_TURNS_AFTER_SUMMARY = 4


@dataclass
class ChatTurn:
    user: str
    assistant: str
    movies: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ChatSession:
    id: str
    turns: List[ChatTurn] = field(default_factory=list)
    summary: Optional[str] = None
    rejected_movie_ids: Set[int] = field(default_factory=set)

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    def suggested_movie_ids(self) -> List[int]:
        seen: set[int] = set()
        ordered: List[int] = []
        for turn in self.turns:
            for movie in turn.movies:
                mid = movie.get("id")
                if isinstance(mid, int) and mid not in seen:
                    seen.add(mid)
                    ordered.append(mid)
        return ordered

    def find_movie_by_title(self, title_query: str) -> Optional[Dict[str, Any]]:
        """Match a film from prior turns (detail/review follow-ups)."""
        from src.utils.request_limits import _normalize

        q = _normalize(title_query.strip())
        if not q:
            return None

        for turn in reversed(self.turns):
            for movie in turn.movies:
                title = _normalize(str(movie.get("title") or ""))
                if not title:
                    continue
                if q == title or q in title or title in q:
                    return movie
                if len(q) >= 2 and (title.startswith(q) or q.startswith(title)):
                    return movie
        return None


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, ChatSession] = {}
        self._lock = Lock()

    def create(self, session_id: Optional[str] = None) -> ChatSession:
        sid = session_id or str(uuid.uuid4())
        session = ChatSession(id=sid)
        with self._lock:
            self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> Optional[ChatSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> ChatSession:
        with self._lock:
            existing = self._sessions.get(session_id)
            if existing:
                return existing
            session = ChatSession(id=session_id)
            self._sessions[session_id] = session
            return session

    def append_turn(self, session_id: str, turn: "ChatTurn") -> int:
        """Atomically append a turn and return the new turn count."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return 0
            session.turns.append(turn)
            return len(session.turns)

    def reset(self, session_id: str) -> ChatSession:
        with self._lock:
            session = ChatSession(id=session_id)
            self._sessions[session_id] = session
            return session

    def list_all(self) -> List[ChatSession]:
        with self._lock:
            return list(self._sessions.values())

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


store = SessionStore()
