"""Run ReAct agent queries with async execution and dynamic language detection."""

import re
from typing import Any, Dict

from src.agent.agent import ReActAgent
from src.core.domain_guard import build_off_topic_result, is_clear_off_topic
from src.core.factory import get_llm_provider
from src.tools.registry import TOOL_SPECS
from src.tools.tmdb_client import get_client

EXAMPLE_PROMPTS = [
    "Tôi vừa xem Inception, gợi ý phim tương tự có trên Netflix.",
    "Phim trending tuần này ở VN thể loại Sci-Fi là gì?",
    "Tôi buồn, muốn xem phim nhẹ nhàng — gợi ý 3 phim.",
    "So sánh Inception, Interstellar và The Prestige.",
    "Phim Get Out có trên Netflix VN không?",
]

VALID_MODES = ("ReAct Agent", "ReAct Agent v2", "ReAct Agent v1", "Chatbot Baseline")

# Simple heuristic: if the query contains Vietnamese-specific characters, treat as Vietnamese
_VIETNAMESE_PATTERN = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)


def detect_language(text: str) -> str:
    """Detect query language: returns 'vi-VN' for Vietnamese, 'en-US' for English."""
    if _VIETNAMESE_PATTERN.search(text):
        return "vi-VN"
    return "en-US"


async def run_query(mode: str, user_input: str, provider: str, model: str, max_steps: int) -> Dict[str, Any]:
    if is_clear_off_topic(user_input):
        return build_off_topic_result(user_input)

    # Dynamic language detection for TMDB locale
    language = detect_language(user_input)
    get_client(language=language)

    llm = get_llm_provider(provider=provider, model=model)
    return await ReActAgent(llm=llm, tools=TOOL_SPECS, max_steps=max_steps).run(user_input)
