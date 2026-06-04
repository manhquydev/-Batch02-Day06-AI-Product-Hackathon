"""Unit tests for chat_context module."""

import pytest

from src.services.chat_context import (
    build_agent_input,
    build_context_prefix,
    format_turns,
    prepare_session_turn,
)
from src.services.session_store import RECENT_TURNS_AFTER_SUMMARY, TURN_LIMIT, ChatSession, ChatTurn


class TestFormatTurns:
    """Tests for format_turns() function."""

    def test_format_empty_turns(self):
        """Empty turns list returns empty string."""
        result = format_turns([])
        assert result == ""

    def test_format_single_turn(self):
        """Single turn is formatted correctly."""
        turns = [ChatTurn(user="Hi", assistant="Hello")]
        result = format_turns(turns)
        assert "Người dùng: Hi" in result
        assert "Trợ lý: Hello" in result

    def test_format_multiple_turns(self):
        """Multiple turns are separated by double newlines."""
        turns = [
            ChatTurn(user="Hi", assistant="Hello"),
            ChatTurn(user="How are you?", assistant="Good"),
        ]
        result = format_turns(turns)
        assert "Người dùng: Hi" in result
        assert "Trợ lý: Hello" in result
        assert "Người dùng: How are you?" in result
        assert "Trợ lý: Good" in result
        assert "\n\n" in result  # Separator

    def test_format_turns_vietnamese_content(self):
        """Vietnamese content is preserved."""
        turns = [ChatTurn(user="Xin chào", assistant="Chào bạn")]
        result = format_turns(turns)
        assert "Xin chào" in result
        assert "Chào bạn" in result


class TestBuildContextPrefix:
    """Tests for build_context_prefix() function."""

    def test_empty_session_returns_empty_prefix(self):
        """Empty session returns empty string."""
        session = ChatSession(id="test")
        prefix = build_context_prefix(session)
        assert prefix == ""

    def test_single_turn_includes_context_header(self):
        """Single turn includes '[Ngữ cảnh cuộc trò chuyện]' header."""
        session = ChatSession(id="test")
        session.turns.append(ChatTurn(user="Hi", assistant="Hello"))
        prefix = build_context_prefix(session)
        assert "[Ngữ cảnh cuộc trò chuyện]" in prefix
        assert "Người dùng: Hi" in prefix
        assert "Trợ lý: Hello" in prefix

    def test_multiple_turns_under_limit(self):
        """Multiple turns under TURN_LIMIT include full history."""
        session = ChatSession(id="test")
        for i in range(3):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))
        prefix = build_context_prefix(session)
        assert "[Ngữ cảnh cuộc trò chuyện]" in prefix
        assert "Q0" in prefix and "Q1" in prefix and "Q2" in prefix

    def test_at_turn_limit_with_summary(self):
        """Session at TURN_LIMIT with summary includes summary."""
        session = ChatSession(id="test")
        for i in range(TURN_LIMIT):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))
        session.summary = "Previously discussed: Inception and movies"
        prefix = build_context_prefix(session)
        assert "[Tóm tắt các lượt trước]" in prefix
        assert "Previously discussed" in prefix

    def test_at_turn_limit_with_summary_includes_recent(self):
        """At TURN_LIMIT with summary, recent turns are included."""
        session = ChatSession(id="test")
        for i in range(TURN_LIMIT):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))
        session.summary = "Earlier summary"
        prefix = build_context_prefix(session)
        # Should include recent turns
        assert "[Vài lượt gần nhất]" in prefix
        # Recent turns should be the last RECENT_TURNS_AFTER_SUMMARY turns
        recent_idx = TURN_LIMIT - RECENT_TURNS_AFTER_SUMMARY
        assert f"Q{recent_idx}" in prefix

    def test_at_turn_limit_without_summary(self):
        """At TURN_LIMIT without summary still produces output."""
        session = ChatSession(id="test")
        for i in range(TURN_LIMIT):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))
        prefix = build_context_prefix(session)
        # Should still include recent turns
        assert prefix != ""
        # Should include at least one turn
        assert "Q" in prefix

    def test_exactly_turn_limit_minus_one(self):
        """At TURN_LIMIT-1, full history is shown (no summary path)."""
        session = ChatSession(id="test")
        for i in range(TURN_LIMIT - 1):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))
        prefix = build_context_prefix(session)
        assert "[Ngữ cảnh cuộc trò chuyện]" in prefix
        # All turns should be visible
        for i in range(TURN_LIMIT - 1):
            assert f"Q{i}" in prefix

    def test_summary_and_recent_parts_joined(self):
        """Summary and recent parts are joined with double newline."""
        session = ChatSession(id="test")
        for i in range(TURN_LIMIT):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))
        session.summary = "Summary text"
        prefix = build_context_prefix(session)
        assert "\n\n" in prefix  # Parts are separated


class TestBuildAgentInput:
    """Tests for build_agent_input() function."""

    def test_empty_context_returns_message(self):
        """Empty context_prefix returns just the message."""
        result = build_agent_input("", "Gợi ý phim")
        assert result == "Gợi ý phim"

    def test_whitespace_context_returns_message(self):
        """Whitespace-only context_prefix returns just the message."""
        result = build_agent_input("   ", "Gợi ý phim")
        assert result == "Gợi ý phim"

    def test_with_context_includes_prefix(self):
        """With context, result includes the prefix."""
        prefix = "[Ngữ cảnh]\nPrevious turn"
        result = build_agent_input(prefix, "Gợi ý phim")
        assert prefix in result

    def test_with_context_includes_new_question_header(self):
        """With context, result includes '[Câu hỏi mới nhất của người dùng]'."""
        prefix = "[Ngữ cảnh]\nPrevious turn"
        result = build_agent_input(prefix, "Gợi ý phim")
        assert "[Câu hỏi mới nhất của người dùng]" in result

    def test_with_context_includes_message(self):
        """With context, result includes the new message."""
        prefix = "[Ngữ cảnh]\nPrevious"
        result = build_agent_input(prefix, "Gợi ý phim")
        assert "Gợi ý phim" in result

    def test_with_context_includes_instruction(self):
        """With context, result includes instruction about context."""
        prefix = "[Ngữ cảnh]\nPrevious"
        result = build_agent_input(prefix, "Gợi ý phim")
        assert "Trả lời dựa trên ngữ cảnh" in result

    def test_with_context_result_order(self):
        """Result preserves order: prefix, header, message, instruction."""
        prefix = "[Ngữ cảnh]\nPrevious"
        result = build_agent_input(prefix, "Gợi ý phim")
        prefix_idx = result.index("[Ngữ cảnh]")
        header_idx = result.index("[Câu hỏi mới nhất của người dùng]")
        msg_idx = result.index("Gợi ý phim")
        instruction_idx = result.index("Trả lời dựa trên")
        assert prefix_idx < header_idx < msg_idx < instruction_idx

    def test_context_prefix_stripped(self):
        """Context prefix is stripped of leading/trailing whitespace."""
        prefix = "  [Ngữ cảnh]\nPrevious  "
        result = build_agent_input(prefix, "Gợi ý phim")
        # Should not have excessive leading whitespace
        lines = result.split("\n")
        assert lines[0] == "[Ngữ cảnh]"

    def test_message_stripped(self):
        """Message is stripped of leading/trailing whitespace."""
        result = build_agent_input("[Ngữ cảnh]\nPrev", "  Gợi ý phim  ")
        # Message should appear without leading spaces
        assert "Gợi ý phim" in result


class TestPrepareSessionTurn:
    """Tests for prepare_session_turn() async function."""

    @pytest.mark.asyncio
    async def test_under_turn_limit_no_summarize(self):
        """Under TURN_LIMIT: summarize_fn NOT called."""
        session = ChatSession(id="test")
        for i in range(3):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))

        called = []

        async def mock_summarize_fn(turns, provider, model):
            called.append(True)
            return "Summary"

        agent_input, message, did_summarize = await prepare_session_turn(
            session, "New question", "openai", "gpt-4o", mock_summarize_fn
        )

        assert not called  # summarize_fn not called
        assert not did_summarize
        assert "New question" in agent_input
        assert message == "New question"

    @pytest.mark.asyncio
    async def test_at_turn_limit_no_summary_calls_summarize(self):
        """At TURN_LIMIT with no summary: summarize_fn IS called."""
        session = ChatSession(id="test")
        for i in range(TURN_LIMIT):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))

        called = []

        async def mock_summarize_fn(turns, provider, model):
            called.append((turns, provider, model))
            return "Summary of conversation"

        agent_input, message, did_summarize = await prepare_session_turn(
            session, "New question", "openai", "gpt-4o", mock_summarize_fn
        )

        assert len(called) == 1
        assert did_summarize
        assert session.summary == "Summary of conversation"

    @pytest.mark.asyncio
    async def test_at_turn_limit_with_summary_no_resummary(self):
        """At TURN_LIMIT + 1 with existing summary, not at modulo: no summarize call."""
        session = ChatSession(id="test")
        for i in range(TURN_LIMIT + 1):  # +1 to avoid exact modulo
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))
        session.summary = "Existing summary"

        called = []

        async def mock_summarize_fn(turns, provider, model):
            called.append(True)
            return "New summary"

        agent_input, message, did_summarize = await prepare_session_turn(
            session, "New question", "openai", "gpt-4o", mock_summarize_fn
        )

        assert not called  # Not at modulo (TURN_LIMIT * 2), so no re-summarize
        assert not did_summarize
        assert session.summary == "Existing summary"  # Not changed

    @pytest.mark.asyncio
    async def test_at_turn_limit_multiple_resummary(self):
        """At TURN_LIMIT * 2: summarize_fn IS called again (re-summarize)."""
        session = ChatSession(id="test")
        for i in range(TURN_LIMIT * 2):
            session.turns.append(ChatTurn(user=f"Q{i}", assistant=f"A{i}"))
        session.summary = "Old summary"

        called = []

        async def mock_summarize_fn(turns, provider, model):
            called.append(True)
            return "New summary"

        agent_input, message, did_summarize = await prepare_session_turn(
            session, "New question", "openai", "gpt-4o", mock_summarize_fn
        )

        assert len(called) == 1
        assert did_summarize
        assert session.summary == "New summary"

    @pytest.mark.asyncio
    async def test_prepare_returns_agent_input_with_context(self):
        """Returned agent_input includes context prefix."""
        session = ChatSession(id="test")
        session.turns.append(ChatTurn(user="Previous", assistant="Response"))

        async def mock_summarize_fn(turns, provider, model):
            return "Summary"

        agent_input, message, did_summarize = await prepare_session_turn(
            session, "New", "openai", "gpt-4o", mock_summarize_fn
        )

        assert "Người dùng: Previous" in agent_input
        assert "Trợ lý: Response" in agent_input

    @pytest.mark.asyncio
    async def test_prepare_returns_original_message(self):
        """Returned message is the original user input (for guard)."""
        session = ChatSession(id="test")

        async def mock_summarize_fn(turns, provider, model):
            return "Summary"

        agent_input, message, did_summarize = await prepare_session_turn(
            session, "User says this", "openai", "gpt-4o", mock_summarize_fn
        )

        assert message == "User says this"
