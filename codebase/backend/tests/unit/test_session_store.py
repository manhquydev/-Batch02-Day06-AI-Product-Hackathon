"""Unit tests for session_store module."""

import threading
from typing import Set

import pytest

from src.services.session_store import ChatSession, ChatTurn, SessionStore


class TestChatTurn:
    """Tests for ChatTurn dataclass."""

    def test_chat_turn_creation(self):
        """ChatTurn can be created with user and assistant messages."""
        turn = ChatTurn(user="Hello", assistant="Hi there")
        assert turn.user == "Hello"
        assert turn.assistant == "Hi there"


class TestChatSession:
    """Tests for ChatSession dataclass."""

    def test_session_creation_with_id(self):
        """ChatSession can be created with an id."""
        session = ChatSession(id="test-id-123")
        assert session.id == "test-id-123"
        assert session.turns == []
        assert session.summary is None

    def test_session_turn_count_empty(self):
        """Empty session has turn_count of 0."""
        session = ChatSession(id="test")
        assert session.turn_count == 0

    def test_session_turn_count_with_turns(self):
        """Session turn_count reflects number of turns."""
        session = ChatSession(id="test")
        session.turns.append(ChatTurn(user="Hi", assistant="Hello"))
        assert session.turn_count == 1

        session.turns.append(ChatTurn(user="How are you?", assistant="Good"))
        assert session.turn_count == 2

    def test_session_summary_optional(self):
        """Session summary is optional (None by default)."""
        session = ChatSession(id="test")
        assert session.summary is None

    def test_session_summary_can_be_set(self):
        """Session summary can be set."""
        session = ChatSession(id="test")
        session.summary = "Previous conversation about movies"
        assert session.summary == "Previous conversation about movies"


class TestSessionStore:
    """Tests for SessionStore class."""

    @pytest.fixture
    def store(self):
        """Create a fresh SessionStore for each test."""
        return SessionStore()

    def test_store_create_returns_session(self, store):
        """create() returns a ChatSession."""
        session = store.create()
        assert isinstance(session, ChatSession)

    def test_store_create_generates_uuid(self, store):
        """create() generates a unique UUID as session_id."""
        session = store.create()
        assert session.id is not None
        assert len(session.id) > 0
        # UUID format check (basic)
        assert "-" in session.id

    def test_store_create_with_custom_id(self, store):
        """create(session_id='custom-id') uses the provided ID."""
        session = store.create(session_id="custom-id-123")
        assert session.id == "custom-id-123"

    def test_store_create_multiple_unique_ids(self, store):
        """Multiple create() calls generate unique IDs."""
        session1 = store.create()
        session2 = store.create()
        session3 = store.create()
        assert session1.id != session2.id != session3.id

    def test_store_get_existing_session(self, store):
        """get() returns existing session."""
        created = store.create(session_id="test-session")
        retrieved = store.get("test-session")
        assert retrieved is not None
        assert retrieved.id == "test-session"
        assert retrieved is created

    def test_store_get_nonexistent_returns_none(self, store):
        """get() returns None for unknown session_id."""
        result = store.get("nonexistent-session")
        assert result is None

    def test_store_get_or_create_existing(self, store):
        """get_or_create() returns existing session without resetting."""
        created = store.create(session_id="test-session")
        created.turns.append(ChatTurn(user="Hi", assistant="Hello"))
        assert created.turn_count == 1

        retrieved = store.get_or_create("test-session")
        assert retrieved is created
        assert retrieved.turn_count == 1  # Not reset

    def test_store_get_or_create_new(self, store):
        """get_or_create() creates new session if not found."""
        session = store.get_or_create("new-session-id")
        assert session is not None
        assert session.id == "new-session-id"
        assert session.turn_count == 0

    def test_store_reset_clears_turns(self, store):
        """reset() clears turns from existing session."""
        session = store.create(session_id="test")
        session.turns.append(ChatTurn(user="Hi", assistant="Hello"))
        assert session.turn_count == 1

        reset_session = store.reset("test")
        assert reset_session.turn_count == 0
        assert reset_session.id == "test"

    def test_store_reset_clears_summary(self, store):
        """reset() clears summary from existing session."""
        session = store.create(session_id="test")
        session.summary = "Previous conversation"
        assert session.summary == "Previous conversation"

        reset_session = store.reset("test")
        assert reset_session.summary is None

    def test_store_reset_nonexistent_creates_new(self, store):
        """reset() creates new session if it doesn't exist."""
        session = store.reset("nonexistent")
        assert session is not None
        assert session.id == "nonexistent"
        assert session.turn_count == 0

    def test_store_reset_returns_same_id(self, store):
        """reset() returns session with same id."""
        store.create(session_id="test")
        reset_session = store.reset("test")
        assert reset_session.id == "test"

    # --- Concurrency tests ---
    def test_store_concurrent_creates_unique_ids(self, store):
        """Multiple threads creating sessions get unique IDs."""
        session_ids: Set[str] = set()
        lock = threading.Lock()

        def create_session():
            session = store.create()
            with lock:
                session_ids.add(session.id)

        threads = [threading.Thread(target=create_session) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(session_ids) == 10

    def test_store_concurrent_get_or_create(self, store):
        """Concurrent get_or_create() on same ID returns same session."""
        session_ids: Set[str] = set()
        lock = threading.Lock()

        def get_or_create_session():
            session = store.get_or_create("concurrent-test")
            with lock:
                session_ids.add(id(session))  # Python object id, not session.id

        threads = [threading.Thread(target=get_or_create_session) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All threads should get the same session object (or at least same session.id)
        assert len(session_ids) == 1

    def test_store_concurrent_get_or_create_preserves_turns(self, store):
        """Concurrent get_or_create() doesn't reset existing turns."""
        session = store.get_or_create("test")
        session.turns.append(ChatTurn(user="Initial", assistant="Response"))

        retrieved_sessions = []
        lock = threading.Lock()

        def get_or_create_session():
            s = store.get_or_create("test")
            with lock:
                retrieved_sessions.append(s)

        threads = [threading.Thread(target=get_or_create_session) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All retrieved sessions should have 1 turn
        for s in retrieved_sessions:
            assert s.turn_count == 1
