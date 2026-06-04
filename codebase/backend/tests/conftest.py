"""Shared pytest fixtures for the Movie ReAct Agent API tests."""

import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Add backend root to sys.path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def mock_llm_provider() -> AsyncMock:
    """Mock LLMProvider that returns controlled responses."""
    provider = AsyncMock()
    provider.generate = AsyncMock(
        return_value={
            "content": "Final Answer: Gợi ý phim: Inception (2010)",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
            "latency_ms": 100,
            "provider": "openai",
        }
    )

    async def mock_stream(*args, **kwargs):
        """Mock streaming generator."""
        tokens = ["Gợi ý", " phim", ": Inception"]
        for token in tokens:
            yield token

    provider.stream = mock_stream
    return provider


@pytest.fixture
def mock_agent_result() -> Dict[str, Any]:
    """Standard mock agent result."""
    return {
        "answer": "Gợi ý: Inception (2010) là một bộ phim Sci-Fi xuất sắc.",
        "trace": [
            {
                "step": 1,
                "thought": "Người dùng muốn xem gợi ý phim.",
                "action": "search_movies('inception', 5)",
                "observation": "Found: Inception (2010), rating: 8.8",
                "raw": "...",
            }
        ],
        "steps": 1,
        "latency_ms": 500,
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 80,
            "total_tokens": 200,
        },
        "mode": "ReAct Agent",
    }


@pytest.fixture
def app_client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient with mocked run_query."""
    from unittest.mock import AsyncMock, patch

    from src.api.main import app

    with patch("src.api.main.run_query") as mock_run_query:
        # Configure default mock response
        mock_run_query.return_value = {
            "answer": "Gợi ý: Inception (2010)",
            "trace": [
                {
                    "step": 1,
                    "thought": "Search for movie",
                    "action": "search_movies('inception', 5)",
                    "observation": "Found Inception",
                    "raw": "...",
                }
            ],
            "steps": 1,
            "latency_ms": 500,
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "mode": "ReAct Agent",
        }
        # Make it async-compatible for FastAPI
        if not isinstance(mock_run_query.return_value, dict):
            mock_run_query.return_value = AsyncMock(
                return_value=mock_run_query.return_value
            )

        client = TestClient(app)
        client.mock_run_query = mock_run_query
        yield client


@pytest.fixture
def mock_comparison_result() -> Dict[str, Any]:
    """Mock result from run_parallel_comparison."""
    return {
        "openai/gpt-4o-mini": {
            "ok": True,
            "answer": "Gợi ý: Inception",
            "trace": [],
            "steps": 1,
            "latency_ms": 500,
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "mode": "ReAct Agent",
        },
        "deepseek/deepseek-chat": {
            "ok": True,
            "answer": "Gợi ý: Interstellar",
            "trace": [],
            "steps": 1,
            "latency_ms": 600,
            "usage": {"prompt_tokens": 110, "completion_tokens": 55, "total_tokens": 165},
            "mode": "ReAct Agent",
        },
    }


@pytest.fixture(autouse=True)
def reset_session_store() -> Generator[None, None, None]:
    """Clear session store state before/after each test.

    Mutates the existing singleton in-place so all module-level references
    (main.py, test modules) remain valid without needing patching.
    """
    from src.services.session_store import store as _store

    _store._sessions.clear()
    yield
    _store._sessions.clear()


@pytest.fixture(autouse=True)
def clear_comparison_cache() -> Generator[None, None, None]:
    """Clear the build_model_options LRU cache before each test."""
    from src.services.comparison import build_model_options

    build_model_options.cache_clear()
    yield
    build_model_options.cache_clear()
