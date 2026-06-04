"""Build agent input from session history + optional summary."""

from __future__ import annotations

from typing import List, Optional, Tuple

from src.services.session_store import RECENT_TURNS_AFTER_SUMMARY, TURN_LIMIT, ChatSession, ChatTurn


def format_turns(turns: List[ChatTurn]) -> str:
    if not turns:
        return ""
    parts = []
    for t in turns:
        parts.append(f"Người dùng: {t.user}\nTrợ lý: {t.assistant}")
    return "\n\n".join(parts)


def build_context_prefix(session: ChatSession) -> str:
    """Context from completed turns (not including the new user message)."""
    parts = []

    if session.turn_count > 0:
        if session.turn_count < TURN_LIMIT:
            block = format_turns(session.turns)
            if block:
                parts.append(f"[Ngữ cảnh cuộc trò chuyện]\n{block}")
        else:
            if session.summary:
                parts.append(f"[Tóm tắt các lượt trước]\n{session.summary}")
            recent = session.turns[-RECENT_TURNS_AFTER_SUMMARY:]
            if recent:
                parts.append(f"[Vài lượt gần nhất]\n{format_turns(recent)}")

    if session.rejected_movie_ids:
        ids_str = ", ".join(str(mid) for mid in sorted(session.rejected_movie_ids))
        parts.append(f"[Phim đã từ chối - KHÔNG GỢI Ý LẠI]\nID TMDB: {ids_str}")

    return "\n\n".join(parts)


def build_agent_input(context_prefix: str, message: str) -> str:
    if not context_prefix.strip():
        return message
    return (
        f"{context_prefix.strip()}\n\n"
        f"[Câu hỏi mới nhất của người dùng]\n{message.strip()}\n\n"
        "Trả lời dựa trên ngữ cảnh trên và câu hỏi mới nhất. "
        "Nếu người dùng tham chiếu 'phim trên', 'cái đó', hãy hiểu theo lịch sử chat."
    )


async def prepare_session_turn(
    session: ChatSession,
    message: str,
    provider: str,
    model: str,
    summarize_fn,
) -> Tuple[str, str, bool]:
    """
    Returns (agent_input, latest_user_message_for_guard, did_summarize).
    """
    summarized = False
    if session.turn_count >= TURN_LIMIT and (
        session.summary is None or session.turn_count % TURN_LIMIT == 0
    ):
        session.summary = await summarize_fn(session.turns, provider, model)
        summarized = True

    prefix = build_context_prefix(session)
    agent_input = build_agent_input(prefix, message)
    return agent_input, message, summarized
