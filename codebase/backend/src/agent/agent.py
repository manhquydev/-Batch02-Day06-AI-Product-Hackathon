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

    def __init__(self, llm: LLMProvider, tools: Optional[List[Dict[str, Any]]] = None, max_steps: int = 5):
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

WRONG — do not do this:
  Action: filter_by_mood()      ← missing required 'mood' argument
  Action: search_movies()       ← missing required 'query' argument
  Action: get_movie_details()   ← missing required 'movie_id' argument

Additional rules:
- If a request is not clearly about movies, series, cinemas, streaming, or watch recommendations, do not call tools and do not invent a movie angle. Reply with a short Final Answer saying this demo only handles movie-related questions.
- Search for a movie first with search_movies() to get the correct movie_id.
- Never invent movie_id values.
- Valid moods: happy, sad, relaxed, excited, romantic, scary.
- Use at most one Action per step. Stop when you have enough data.
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
            prompt = scratchpad + "\nYour next step:"
            result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
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
                else:
                    scratchpad += (
                        f"\nThought: {parsed['thought'] or ''}\n"
                        f"Action: {parsed['action']}\n"
                        f"Observation: {observation}\n"
                    )
            else:
                # Retry logic: re-prompt with format reminder before giving up the step
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
            final_answer = (
                "Không thể hoàn thành trong số bước cho phép. "
                "Hãy thử câu hỏi cụ thể hơn hoặc tăng max_steps."
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
