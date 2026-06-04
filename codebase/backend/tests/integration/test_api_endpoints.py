"""Integration tests for FastAPI endpoints."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create a TestClient with mocked run_query and run_parallel_comparison."""
    with patch("src.api.main.run_query") as mock_run_query, \
         patch("src.api.main.run_parallel_comparison") as mock_parallel:

        # Default mock for run_query
        async def default_run_query(*args, **kwargs):
            return {
                "answer": "Gợi ý: Inception (2010)",
                "trace": [
                    {
                        "step": 1,
                        "thought": "Search for movie",
                        "action": "search_movies('inception', 5)",
                        "observation": "Found: Inception",
                        "raw": "...",
                    }
                ],
                "steps": 1,
                "latency_ms": 500,
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                "mode": "ReAct Agent",
            }

        mock_run_query.side_effect = default_run_query

        # Default mock for run_parallel_comparison
        async def default_parallel(*args, **kwargs):
            return {
                "openai/gpt-4o-mini": {
                    "ok": True,
                    "answer": "Result from OpenAI",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 500,
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                    "mode": "ReAct Agent",
                },
                "deepseek/deepseek-chat": {
                    "ok": True,
                    "answer": "Result from DeepSeek",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 600,
                    "usage": {"prompt_tokens": 110, "completion_tokens": 55, "total_tokens": 165},
                    "mode": "ReAct Agent",
                },
            }

        mock_parallel.side_effect = default_parallel

        test_client = TestClient(app)
        test_client.mock_run_query = mock_run_query
        test_client.mock_parallel = mock_parallel
        yield test_client


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200(self, client):
        """GET /health returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_includes_status_ok(self, client):
        """Response includes 'status': 'ok'."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_includes_api_key_flags(self, client):
        """Response includes openai_configured and tmdb_configured flags."""
        response = client.get("/health")
        data = response.json()
        assert "openai_configured" in data
        assert "tmdb_configured" in data
        assert isinstance(data["openai_configured"], bool)
        assert isinstance(data["tmdb_configured"], bool)


class TestModesEndpoint:
    """Tests for GET /api/modes endpoint."""

    def test_modes_returns_200(self, client):
        """GET /api/modes returns 200."""
        response = client.get("/api/modes")
        assert response.status_code == 200

    def test_modes_returns_list(self, client):
        """Response includes 'modes' array."""
        response = client.get("/api/modes")
        data = response.json()
        assert "modes" in data
        assert isinstance(data["modes"], list)

    def test_modes_includes_react_agent(self, client):
        """Modes list includes 'ReAct Agent'."""
        response = client.get("/api/modes")
        data = response.json()
        assert "ReAct Agent" in data["modes"]

    def test_modes_only_valid_modes(self, client):
        """Only valid modes are returned."""
        response = client.get("/api/modes")
        data = response.json()
        # According to spec, should only include "ReAct Agent" (stale modes removed)
        assert all(mode in ["ReAct Agent", "ReAct Agent v2", "ReAct Agent v1", "Chatbot Baseline"]
                  for mode in data["modes"])


class TestExamplePromptsEndpoint:
    """Tests for GET /api/example-prompts endpoint."""

    def test_example_prompts_returns_200(self, client):
        """GET /api/example-prompts returns 200."""
        response = client.get("/api/example-prompts")
        assert response.status_code == 200

    def test_example_prompts_returns_list(self, client):
        """Response includes 'prompts' array."""
        response = client.get("/api/example-prompts")
        data = response.json()
        assert "prompts" in data
        assert isinstance(data["prompts"], list)

    def test_example_prompts_not_empty(self, client):
        """Prompts list is not empty."""
        response = client.get("/api/example-prompts")
        data = response.json()
        assert len(data["prompts"]) > 0

    def test_example_prompts_are_strings(self, client):
        """All prompts are strings."""
        response = client.get("/api/example-prompts")
        data = response.json()
        assert all(isinstance(p, str) for p in data["prompts"])


class TestCreateSessionEndpoint:
    """Tests for POST /api/sessions endpoint."""

    def test_create_session_returns_200(self, client):
        """POST /api/sessions returns 200."""
        response = client.post("/api/sessions")
        assert response.status_code == 200

    def test_create_session_returns_session_id(self, client):
        """Response includes 'session_id'."""
        response = client.post("/api/sessions")
        data = response.json()
        assert "session_id" in data
        assert isinstance(data["session_id"], str)

    def test_create_session_id_not_empty(self, client):
        """Session ID is not empty."""
        response = client.post("/api/sessions")
        data = response.json()
        assert len(data["session_id"]) > 0

    def test_create_session_unique_ids(self, client):
        """Multiple creates return different session IDs."""
        response1 = client.post("/api/sessions")
        response2 = client.post("/api/sessions")
        id1 = response1.json()["session_id"]
        id2 = response2.json()["session_id"]
        assert id1 != id2

    def test_create_session_id_valid_uuid_format(self, client):
        """Session ID follows UUID format (contains hyphens)."""
        response = client.post("/api/sessions")
        session_id = response.json()["session_id"]
        # Basic UUID check
        assert "-" in session_id


class TestResetSessionEndpoint:
    """Tests for POST /api/sessions/{session_id}/reset endpoint."""

    def test_reset_session_returns_200(self, client):
        """POST /api/sessions/{id}/reset returns 200."""
        response = client.post("/api/sessions/test-session-123/reset")
        assert response.status_code == 200

    def test_reset_session_returns_session_id(self, client):
        """Response includes 'session_id'."""
        response = client.post("/api/sessions/test-session-123/reset")
        data = response.json()
        assert "session_id" in data

    def test_reset_session_same_id(self, client):
        """Reset returns the same session_id that was passed."""
        session_id = "test-session-456"
        response = client.post(f"/api/sessions/{session_id}/reset")
        data = response.json()
        assert data["session_id"] == session_id

    def test_reset_nonexistent_session_still_200(self, client):
        """Reset on non-existent session still returns 200."""
        response = client.post("/api/sessions/nonexistent-session-xyz/reset")
        assert response.status_code == 200


class TestChatEndpoint:
    """Tests for POST /api/chat endpoint."""

    def test_chat_happy_case_returns_200(self, client):
        """POST /api/chat with valid data returns 200."""
        payload = {
            "message": "Gợi ý phim buồn",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

    def test_chat_response_includes_answer(self, client):
        """Response includes 'answer'."""
        payload = {
            "message": "Gợi ý phim buồn",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)

    def test_chat_response_includes_trace(self, client):
        """Response includes 'trace'."""
        payload = {
            "message": "Gợi ý phim buồn",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "trace" in data
        assert isinstance(data["trace"], list)

    def test_chat_response_includes_steps(self, client):
        """Response includes 'steps'."""
        payload = {
            "message": "Gợi ý phim buồn",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "steps" in data
        assert isinstance(data["steps"], int)

    def test_chat_response_includes_latency(self, client):
        """Response includes 'latency_ms'."""
        payload = {
            "message": "Gợi ý phim buồn",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "latency_ms" in data
        assert isinstance(data["latency_ms"], int)

    def test_chat_response_includes_movies(self, client):
        """Response includes 'movies'."""
        payload = {
            "message": "Gợi ý phim buồn",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "movies" in data
        assert isinstance(data["movies"], list)

    def test_chat_invalid_mode_returns_422(self, client):
        """Invalid mode returns 422 (Pydantic validation)."""
        payload = {
            "message": "test",
            "mode": "UnknownMode",  # Not in ModeType Literal
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_chat_with_session_id_returns_200(self, client):
        """Chat with session_id returns 200."""
        payload = {
            "message": "tiếp tục gợi ý",
            "session_id": "test-session-123",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

    def test_chat_with_session_id_includes_session_id_in_response(self, client):
        """Response includes 'session_id' when provided."""
        payload = {
            "message": "tiếp tục gợi ý",
            "session_id": "test-session-456",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "test-session-456"

    def test_chat_with_session_id_includes_turn_count(self, client):
        """Response includes 'turn_count' when session_id provided."""
        payload = {
            "message": "tiếp tục gợi ý",
            "session_id": "test-session-789",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "turn_count" in data
        assert isinstance(data["turn_count"], int)

    def test_chat_with_session_id_includes_summarized_flag(self, client):
        """Response includes 'summarized' flag when session_id provided."""
        payload = {
            "message": "tiếp tục gợi ý",
            "session_id": "test-session-999",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "summarized" in data
        assert isinstance(data["summarized"], bool)

    def test_chat_missing_message_returns_422(self, client):
        """Missing 'message' field returns 422."""
        payload = {
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_chat_empty_message_returns_422(self, client):
        """Empty 'message' returns 422 (min_length=1)."""
        payload = {
            "message": "",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 5,
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_chat_max_steps_below_min_returns_422(self, client):
        """max_steps < 2 returns 422."""
        payload = {
            "message": "test",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 1,  # Below ge=2
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_chat_max_steps_above_max_returns_422(self, client):
        """max_steps > 8 returns 422."""
        payload = {
            "message": "test",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 9,  # Above le=8
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422


class TestCompareEndpoint:
    """Tests for POST /api/compare endpoint."""

    def test_compare_happy_case_returns_200(self, client):
        """POST /api/compare with valid data returns 200."""
        payload = {
            "query": "Inception vs Interstellar",
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 200

    def test_compare_response_includes_results(self, client):
        """Response includes 'results' dict."""
        payload = {
            "query": "Inception vs Interstellar",
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], dict)

    def test_compare_results_include_all_models(self, client):
        """Results dict includes all requested models."""
        payload = {
            "query": "Inception vs Interstellar",
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        data = response.json()
        results = data["results"]
        assert "openai/gpt-4o-mini" in results
        assert "deepseek/deepseek-chat" in results

    def test_compare_result_entry_has_answer(self, client):
        """Each result entry includes 'answer'."""
        payload = {
            "query": "Inception vs Interstellar",
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        data = response.json()
        results = data["results"]
        assert "answer" in results["openai/gpt-4o-mini"]
        assert "answer" in results["deepseek/deepseek-chat"]

    def test_compare_result_entry_has_movies(self, client):
        """Each result entry includes 'movies' list."""
        payload = {
            "query": "Inception vs Interstellar",
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        data = response.json()
        results = data["results"]
        assert "movies" in results["openai/gpt-4o-mini"]
        assert "movies" in results["deepseek/deepseek-chat"]

    def test_compare_invalid_mode_returns_422(self, client):
        """Invalid mode returns 422."""
        payload = {
            "query": "test",
            "models": ["openai/gpt-4o-mini"],
            "mode": "Invalid Mode",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 422

    def test_compare_invalid_model_returns_400(self, client):
        """Invalid model key returns 400."""
        payload = {
            "query": "test",
            "models": ["invalid/model-xyz", "another/bad"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "Unknown model keys" in str(data)

    def test_compare_less_than_2_models_returns_422(self, client):
        """Less than 2 models returns 422 (min_length=2)."""
        payload = {
            "query": "test",
            "models": ["openai/gpt-4o-mini"],  # Only 1
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 422

    def test_compare_more_than_4_models_returns_422(self, client):
        """More than 4 models returns 422 (max_length=4)."""
        payload = {
            "query": "test",
            "models": [f"openai/model-{i}" for i in range(5)],  # 5 models
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 422

    def test_compare_missing_query_returns_422(self, client):
        """Missing 'query' returns 422."""
        payload = {
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 422

    def test_compare_empty_query_returns_422(self, client):
        """Empty 'query' returns 422."""
        payload = {
            "query": "",
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 422

    def test_compare_max_steps_validation(self, client):
        """max_steps validation applies (ge=2, le=8)."""
        payload = {
            "query": "test",
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 1,  # Below ge=2
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 422

    def test_compare_with_one_model_failing(self, client):
        """Comparison with one model failing returns 200 with ok=False for that model."""
        async def mock_with_failure(*args, **kwargs):
            return {
                "openai/gpt-4o-mini": {
                    "ok": True,
                    "answer": "Success",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 500,
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                    "mode": "ReAct Agent",
                },
                "deepseek/deepseek-chat": {
                    "ok": False,
                    "error": "API Error",
                    "answer": "Lỗi: API Error",
                    "movies": [],
                },
            }

        client.mock_parallel.side_effect = mock_with_failure

        payload = {
            "query": "test",
            "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
            "mode": "ReAct Agent",
            "max_steps": 5,
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        results = data["results"]
        assert results["openai/gpt-4o-mini"]["ok"] is True
        assert results["deepseek/deepseek-chat"]["ok"] is False
        assert "error" in results["deepseek/deepseek-chat"]
        assert "movies" in results["deepseek/deepseek-chat"]
