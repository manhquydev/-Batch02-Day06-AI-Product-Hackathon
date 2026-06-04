"""Run chatbot / ReAct agents (logic from former Streamlit app)."""
from typing import Any, Dict

from src.agent.agent import ReActAgent
from src.agent.agent_v2 import ReActAgentV2
from src.agent.chatbot import ChatbotBaseline
from src.core.domain_guard import build_off_topic_result, is_clear_off_topic
from src.core.factory import get_llm_provider
from src.tools.registry import TOOL_SPECS

EXAMPLE_PROMPTS = [
    "Tôi vừa xem Inception, gợi ý phim tương tự có trên Netflix.",
    "Phim trending tuần này ở VN thể loại Sci-Fi là gì?",
    "Tôi buồn, muốn xem phim nhẹ nhàng — gợi ý 3 phim.",
    "So sánh Inception, Interstellar và The Prestige.",
    "Phim Get Out có trên Netflix VN không?",
]

VALID_MODES = ("ReAct Agent v2", "ReAct Agent v1", "Chatbot Baseline")


def run_query(mode: str, user_input: str, provider: str, model: str, max_steps: int) -> Dict[str, Any]:
    if is_clear_off_topic(user_input):
        return build_off_topic_result(user_input)

    llm = get_llm_provider(provider=provider, model=model)
    if mode == "ReAct Agent v2":
        return ReActAgentV2(llm=llm, tools=TOOL_SPECS, max_steps=max_steps).run(user_input)
    if mode == "ReAct Agent v1":
        return ReActAgent(llm=llm, tools=TOOL_SPECS, max_steps=max_steps).run(user_input)
    return ChatbotBaseline(llm=llm).run(user_input)
