"""Summarize long chat sessions for compact agent context."""

from __future__ import annotations

from typing import Any, Dict, List

from src.core.factory import get_llm_provider
from src.services.session_store import ChatTurn

SUMMARY_SYSTEM = (
    "Bạn tóm tắt cuộc trò chuyện gợi ý phim. Giữ lại: gu phim, thể loại, tâm trạng, "
    "nền tảng (Netflix VN…), phim đã nhắc, yêu cầu chưa được đáp ứng. "
    "Viết tiếng Việt, tối đa 12 câu, không markdown."
)


def _format_turns(turns: List[ChatTurn]) -> str:
    from src.services.chat_context import format_turn

    blocks = []
    for i, t in enumerate(turns, 1):
        blocks.append(f"Lượt {i} —\n{format_turn(t)}")
    return "\n\n".join(blocks)


async def summarize_turns(
    turns: List[ChatTurn],
    provider: str,
    model: str,
) -> str:
    if not turns:
        return ""
    llm = get_llm_provider(provider=provider, model=model)
    prompt = (
        "Hãy tóm tắt cuộc trò chuyện sau để làm ngữ cảnh cho câu hỏi tiếp theo:\n\n"
        + _format_turns(turns)
    )
    result = await llm.generate(prompt, system_prompt=SUMMARY_SYSTEM)
    return (result.get("content") or "").strip()


async def summarize_messages(
    messages: List[Dict[str, str]],
    provider: str,
    model: str,
) -> str:
    turns: List[ChatTurn] = []
    pending_user: str | None = None
    for m in messages:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            pending_user = content
        elif role == "assistant" and pending_user:
            turns.append(ChatTurn(user=pending_user, assistant=content))
            pending_user = None
    return await summarize_turns(turns, provider, model)
