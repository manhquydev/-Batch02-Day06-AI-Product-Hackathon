import re
from typing import Any, Dict, List, Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.tools.registry import TOOL_SPECS, execute_tool, parse_action


class ReActAgent:
    """Consolidated ReAct agent: Thought -> Action -> Observation loop for movie recommendations.
    
    Includes key improvements:
    - Concrete few-shot examples per tool.
    - Format recovery: inject format hints when tool calls fail with invalid arguments.
    - Retry logic: up to 2 format retries per step when no valid Action/Final Answer is found.
    """

    MAX_FORMAT_RETRIES = 2

    def __init__(self, llm: LLMProvider, tools: Optional[List[Dict[str, Any]]] = None, max_steps: int = 10):
        self.llm = llm
        self.tools = tools or TOOL_SPECS
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        tool_lines = []
        for tool in self.tools:
            tool_lines.append(f"- {tool['name']}: {tool['description']}")
            if tool.get("example"):
                tool_lines.append(f"  Example: Action: {tool['example']}")

        tools_block = "\n".join(tool_lines)
        return f"""You are a movie recommendation ReAct agent with live TMDB API tools.

Available tools:
{tools_block}

STRICT FORMAT — follow exactly or the tool will fail:

Each step must be ONE of:
  a) Thought + Action (when you need data):
       Thought: <your reasoning>
       Action: tool_name(arg1, arg2)
  b) Final Answer (only when you have enough data):
       Final Answer: <recommendation in Vietnamese or English matching the user>

CORRECT examples (arguments are required — never call with empty parentheses):
  Action: search_movies("Inception", 5)
  Action: filter_by_mood("sad", 5)
  Action: get_movie_details(27205)
  Action: get_trending_movies("VN", "Sci-Fi", "week")
  Action: get_similar_movies(27205, 5)
  Action: check_streaming_availability(27205, "VN")
  Action: compare_movies([27205, 157336, 1124])
  Action: get_reviews(27205, 2)

WRONG — do not do this:
  Action: filter_by_mood()      ← missing required 'mood' argument
  Action: search_movies()       ← missing required 'query' argument
  Action: get_movie_details()   ← missing required 'movie_id' argument

Additional rules:
- If a request is not clearly about movies, series, cinemas, streaming, or watch recommendations, do not call tools and do not invent a movie angle. Reply with a short Final Answer saying this demo only handles movie-related questions.
- When the user message is inside a session block `[Ngữ cảnh cuộc trò chuyện]` / `[Câu hỏi mới nhất]`, treat follow-ups ("phim khác", "thêm 3 phim") as continuing the same topic. TMDB tools already skip movie ids suggested earlier in the session — use get_trending_movies / filter_by_mood / discover again for more titles, never repeat the same ids in Final Answer.
- Search for a movie first with search_movies() to get the correct movie_id.
- Never invent movie_id values.
- Valid moods: happy, sad, relaxed, excited, romantic, scary.
- If the user message states a number of films (e.g. "3 phim"), use that exact number as limit in list tools and in Final Answer — do not return more titles than requested.
- If the user asks for details about one film ("biết thêm về phim X", "thông tin phim X"), use get_movie_details for that title only — never answer with a new list of 3–5 unrelated films.
- Use at most one Action per step. Stop when you have enough data.
- If Observation contains "TMDB network error", retry the same Action once before giving up.
- Only say you cannot connect when TMDB errors persist after a retry; otherwise answer with movie data from tools.
- When comparing movies, compare_movies already includes 1-2 real user reviews per movie. You MUST translate each review to Vietnamese and include the full translated review in your Final Answer so the user can read them directly. Format each review clearly with the author name and their full opinion. Do NOT summarize — translate and show the entire review.
- Use get_reviews separately when the user asks for reviews of a single movie. Always translate the full review content to Vietnamese and include it in your answer for the user to read.
- When recommending movies, if you have review data, translate the reviews to Vietnamese and include the full text so users can judge for themselves.
"""

    def _parse_llm_step(self, content: str) -> Dict[str, Optional[str]]:
        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|$)", content, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r"Action:\s*(.+?)(?=\n|$)", content, re.IGNORECASE)
        final_match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL | re.IGNORECASE)

        return {
            "thought": thought_match.group(1).strip() if thought_match else None,
            "action": action_match.group(1).strip() if action_match else None,
            "final_answer": final_match.group(1).strip() if final_match else None,
            "raw": content,
        }

    async def _force_final_answer(
        self,
        scratchpad: str,
        total_usage: Dict[str, int],
        total_latency: int,
    ) -> Optional[str]:
        """One extra LLM call to synthesize Final Answer from the scratchpad when steps run out."""
        prompt = (
            scratchpad
            + "\n\nBạn đã hết lượt gọi tool. Dựa trên các Observation ở trên, trả lời NGAY theo format:\n"
            "Final Answer: <câu trả lời tiếng Việt, đủ gợi ý phim / thông tin đã thu thập>\n"
        )
        try:
            result = await self.llm.generate(prompt, system_prompt=self.get_system_prompt())
            total_latency += result.get("latency_ms", 0)
            usage = result.get("usage") or {}
            for key in total_usage:
                total_usage[key] += usage.get(key, 0)
            parsed = self._parse_llm_step(result.get("content", ""))
            if parsed.get("final_answer"):
                return parsed["final_answer"]
            raw = (result.get("content") or "").strip()
            if raw.lower().startswith("final answer:"):
                return raw.split(":", 1)[1].strip()
            return raw or None
        except Exception:
            return None

    async def _execute_tool(self, action_line: str) -> str:
        try:
            name, args = parse_action(action_line)
        except ValueError as exc:
            return f'{{"error": "{exc}"}}'

        observation = await execute_tool(name, args)
        logger.log_event("TOOL_CALL", {"tool": name, "args": args, "observation_preview": observation[:200]})
        return observation

    async def run(self, user_input: str) -> Dict[str, Any]:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        trace: List[Dict[str, Any]] = []
        scratchpad = f"Question: {user_input}\n"
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        total_latency = 0
        final_answer: Optional[str] = None
        steps = 0
        format_retries = 0

        while steps < self.max_steps:
            steps_left = self.max_steps - steps
            step_hint = "\nYour next step:"
            if steps_left <= 2:
                step_hint = (
                    f"\nYour next step: (còn {steps_left} bước — nếu đã đủ dữ liệu từ Observation, "
                    "bắt buộc trả lời Final Answer ngay, không gọi thêm tool.)\n"
                )
            prompt = scratchpad + step_hint
            result = await self.llm.generate(prompt, system_prompt=self.get_system_prompt())
            content = result.get("content", "")
            total_latency += result.get("latency_ms", 0)

            usage = result.get("usage") or {}
            for key in total_usage:
                total_usage[key] += usage.get(key, 0)

            parsed = self._parse_llm_step(content)
            step_record: Dict[str, Any] = {
                "step": steps + 1,
                "thought": parsed["thought"],
                "action": parsed["action"],
                "observation": None,
                "raw": content,
            }

            if parsed["final_answer"]:
                final_answer = parsed["final_answer"]
                trace.append(step_record)
                break

            if parsed["action"]:
                observation = await self._execute_tool(parsed["action"])
                step_record["observation"] = observation
                trace.append(step_record)
                format_retries = 0

                # Error recovery: inject explicit format hint when tool args are wrong
                if "Invalid arguments" in observation:
                    scratchpad += (
                        f"\nThought: {parsed['thought'] or ''}\n"
                        f"Action: {parsed['action']}\n"
                        f"Observation: {observation}\n"
                        "HINT: The tool failed due to missing or wrong arguments. "
                        "Check the CORRECT examples in the system prompt and include ALL required arguments.\n"
                    )
                elif "TMDB network error" in observation:
                    scratchpad += (
                        f"\nThought: {parsed['thought'] or ''}\n"
                        f"Action: {parsed['action']}\n"
                        f"Observation: {observation}\n"
                        "HINT: TMDB had a transient network error. Retry the same Action once. "
                        "Do not apologize until the retry also fails.\n"
                    )
                else:
                    scratchpad += (
                        f"\nThought: {parsed['thought'] or ''}\n"
                        f"Action: {parsed['action']}\n"
                        f"Observation: {observation}\n"
                    )
                steps += 1
            else:
                # Format retry: re-prompt with format reminder; does NOT consume a step
                format_retries += 1
                trace.append(step_record)
                if format_retries <= self.MAX_FORMAT_RETRIES:
                    scratchpad += (
                        f"\n{content}\n"
                        "REMINDER: output a valid Action in this exact format:\n"
                        "Thought: <reason>\nAction: tool_name(arg1, arg2)\n"
                        "OR if done: Final Answer: <answer>\n"
                    )
                else:
                    scratchpad += (
                        f"\n{content}\n"
                        "Observation: No valid Action after retries. "
                        "Please provide Final Answer now.\n"
                    )
                    format_retries = 0
                    steps += 1

        if not final_answer:
            final_answer = await self._force_final_answer(scratchpad, total_usage, total_latency)
            if not final_answer:
                final_answer = (
                    "Không thể hoàn thành trong số bước cho phép. "
                    f"Hãy thử câu hỏi cụ thể hơn hoặc tăng max_steps (hiện tại {self.max_steps}, "
                    f"có thể gửi tối đa qua API /api/chat)."
                )

        logger.log_event("AGENT_END", {"steps": steps, "trace_len": len(trace)})
        return {
            "answer": final_answer,
            "trace": trace,
            "steps": steps,
            "usage": total_usage,
            "latency_ms": total_latency,
            "mode": "react_agent",
        }
