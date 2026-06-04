"""In-memory chat sessions for guest UI (demo)."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Optional, Set
import uuid

TURN_LIMIT = 10
RECENT_TURNS_AFTER_SUMMARY = 4


@dataclass
class ChatTurn:
    user: str
    assistant: str


@dataclass
class ChatSession:
    id: str
    turns: List[ChatTurn] = field(default_factory=list)
    summary: Optional[str] = None
    rejected_movie_ids: Set[int] = field(default_factory=set)

    @property
    def turn_count(self) -> int:
        return len(self.turns)


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

    def reset(self, session_id: str) -> ChatSession:
        with self._lock:
            session = ChatSession(id=session_id)
            self._sessions[session_id] = session
            return session


store = SessionStore()
