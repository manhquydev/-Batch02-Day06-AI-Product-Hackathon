"""Unit tests for comparison module."""

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from src.services.comparison import run_parallel_comparison


class TestRunParallelComparison:
    """Tests for run_parallel_comparison() function."""

    @pytest.mark.asyncio
    async def test_happy_case_two_models_succeed(self):
        """Both models succeed: returns ok=True for each."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            return {
                "answer": f"Result from {provider}/{model}",
                "trace": [],
                "steps": 1,
                "latency_ms": 500,
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                "mode": "ReAct Agent",
            }

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        assert "openai/gpt-4o-mini" in result
        assert "deepseek/deepseek-chat" in result
        assert result["openai/gpt-4o-mini"]["ok"] is True
        assert result["deepseek/deepseek-chat"]["ok"] is True
        assert "answer" in result["openai/gpt-4o-mini"]
        assert "answer" in result["deepseek/deepseek-chat"]

    @pytest.mark.asyncio
    async def test_partial_failure_one_model_fails(self):
        """One model fails: failed entry has ok=False with error."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            if provider == "openai":
                return {
                    "answer": "Result from OpenAI",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 500,
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                    "mode": "ReAct Agent",
                }
            else:
                raise Exception("DeepSeek API error")

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        assert result["openai/gpt-4o-mini"]["ok"] is True
        assert result["deepseek/deepseek-chat"]["ok"] is False
        assert "error" in result["deepseek/deepseek-chat"]
        assert "DeepSeek API error" in result["deepseek/deepseek-chat"]["error"]

    @pytest.mark.asyncio
    async def test_partial_failure_has_movies_key(self):
        """Failed entry MUST have 'movies' key (empty list)."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            if provider == "openai":
                return {
                    "answer": "Success",
                    "trace": [{"step": 1, "observation": "Inception"}],
                    "steps": 1,
                    "latency_ms": 500,
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                    "mode": "ReAct Agent",
                }
            else:
                raise Exception("Error")

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        failed = result["deepseek/deepseek-chat"]
        assert "movies" in failed
        assert failed["movies"] == []

    @pytest.mark.asyncio
    async def test_all_models_fail(self):
        """All models fail: all entries have ok=False."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            raise Exception(f"Error from {provider}")

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        assert result["openai/gpt-4o-mini"]["ok"] is False
        assert result["deepseek/deepseek-chat"]["ok"] is False
        assert "error" in result["openai/gpt-4o-mini"]
        assert "error" in result["deepseek/deepseek-chat"]

    @pytest.mark.asyncio
    async def test_successful_result_shape(self):
        """Successful result preserves all fields from run_query."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            return {
                "answer": "Test answer",
                "trace": [{"step": 1, "thought": "Think", "action": "act", "observation": "obs", "raw": "..."}],
                "steps": 1,
                "latency_ms": 123,
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                "mode": "ReAct Agent",
            }

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        entry = result["openai/gpt-4o-mini"]
        assert entry["ok"] is True
        assert entry["answer"] == "Test answer"
        assert entry["trace"] == [{"step": 1, "thought": "Think", "action": "act", "observation": "obs", "raw": "..."}]
        assert entry["steps"] == 1
        assert entry["latency_ms"] == 123
        assert entry["usage"]["prompt_tokens"] == 100

    @pytest.mark.asyncio
    async def test_failed_result_error_message(self):
        """Failed result includes stringified error."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            raise ValueError("Invalid model configuration")

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        entry = result["openai/gpt-4o-mini"]
        assert "error" in entry
        assert "Invalid model configuration" in entry["error"]

    @pytest.mark.asyncio
    async def test_failed_result_has_answer_field(self):
        """Failed result includes 'Lỗi: ...' answer."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            raise Exception("Network error")

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        entry = result["openai/gpt-4o-mini"]
        assert "answer" in entry
        assert "Lỗi:" in entry["answer"]

    @pytest.mark.asyncio
    async def test_parallel_execution_timing(self):
        """Both models run in parallel (not sequentially)."""
        call_times = []

        async def mock_run_query(mode, query, provider, model, max_steps):
            call_times.append((provider, time.time()))
            await asyncio.sleep(0.1)  # Simulate 100ms query
            return {
                "answer": "Result",
                "trace": [],
                "steps": 1,
                "latency_ms": 100,
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                "mode": "ReAct Agent",
            }

        start = time.time()
        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )
        elapsed = time.time() - start

        # If sequential: ~200ms (100ms + 100ms)
        # If parallel: ~100ms (both at same time)
        # With some overhead, should be close to 100ms, definitely less than 150ms
        assert elapsed < 0.15, f"Queries appear sequential (took {elapsed}s), expected parallel (<0.15s)"

    @pytest.mark.asyncio
    async def test_single_model(self):
        """Single model in list works correctly."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            return {
                "answer": "Result",
                "trace": [],
                "steps": 1,
                "latency_ms": 500,
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                "mode": "ReAct Agent",
            }

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        assert len(result) == 1
        assert "openai/gpt-4o-mini" in result
        assert result["openai/gpt-4o-mini"]["ok"] is True

    @pytest.mark.asyncio
    async def test_three_models_mixed_results(self):
        """Three models with mixed success/failure."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            if provider == "openai":
                return {
                    "answer": "OpenAI result",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 500,
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                    "mode": "ReAct Agent",
                }
            elif provider == "deepseek":
                raise Exception("DeepSeek unavailable")
            else:  # ollama
                return {
                    "answer": "Ollama result",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 600,
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                    "mode": "ReAct Agent",
                }

        result = await run_parallel_comparison(
            ["openai/gpt-4o-mini", "deepseek/deepseek-chat", "ollama/llama2"],
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        assert result["openai/gpt-4o-mini"]["ok"] is True
        assert result["deepseek/deepseek-chat"]["ok"] is False
        assert result["ollama/llama2"]["ok"] is True

    @pytest.mark.asyncio
    async def test_result_dict_keys_match_input_models(self):
        """Result dict keys exactly match input model keys."""
        async def mock_run_query(mode, query, provider, model, max_steps):
            return {
                "answer": "Result",
                "trace": [],
                "steps": 1,
                "latency_ms": 500,
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                "mode": "ReAct Agent",
            }

        models = ["openai/gpt-4o-mini", "deepseek/deepseek-chat", "ollama/llama2"]
        result = await run_parallel_comparison(
            models,
            "ReAct Agent",
            "Gợi ý phim",
            5,
            run_fn=mock_run_query,
        )

        assert set(result.keys()) == set(models)
