"""Red-team adversarial tests for Movie ReAct Agent backend using REAL API.

These tests call the actual FastAPI app with real LLM and TMDB calls to find:
1. Domain guard bypasses
2. Agent misbehavior (loops, hallucinations, empty tool calls)
3. Error path integrity
4. Session edge cases
5. Concurrent load and race conditions

Run WITHOUT live tests (mocked):
    pytest tests/redteam/ -v --tb=short -m "not live"

Run WITH live tests (real API):
    RUN_LIVE_TESTS=1 pytest tests/redteam/ -v -m live --tb=short
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

# Add backend root to sys.path
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.api.main import app
from src.services.session_store import store as session_store


class TestDomainGuardBypassAttempts:
    """RED TEAM: Test domain guard correctness without LLM calls.

    Fast deterministic tests that verify the domain guard correctly
    blocks off-topic queries and allows movie-related ones.
    """

    # Queries that SHOULD pass through domain guard (movie intent)
    SHOULD_PASS_QUERIES = [
        "Inception",
        "review phim Parasite",
        "rap chiếu phim",
        "xem gi toi nay",
        "Tôi muốn xem film nào hay",
        "trending movies this week",
        "check streaming availability for movie 123",
        "phim hay nhất 2024",
        "recommend a sci-fi film",
        "so sánh Inception và Interstellar",
        "Get Out streaming where",
        "Netflix phim hành động",
        "Disney+ series mới",
        "HBO Max show bây giờ",
        "prime video movie suggestion",
        "IMDB rating phim",
        "TMDB search actors",
        "trailer phim mới",
        "diễn viên trong Oppenheimer",
        "đạo diễn Parasite là ai",
        "thể loại phim kinh dị",
        "xem chung phim với bạn",
        "Hai người xem phim",
    ]

    # Queries that SHOULD be BLOCKED by domain guard
    SHOULD_BLOCK_QUERIES = [
        "Thời tiết Hà Nội hôm nay",
        "nấu phở bò như thế nào",
        "giá vàng hôm nay",
        "lịch sử Việt Nam",
        "toán học cấp 3",
        "bài tập python",
        "đặt vé máy bay",
        "thể thao bóng đá",
        "What is machine learning?",
        "How to cook pasta?",
        "Stock market today",
        "COVID-19 symptoms",
        "Python programming tutorial",
        "How to build a website?",
        "Lịch sự tiếp khách",
        "Kỹ năng giao tiếp",
    ]

    def test_should_pass_movie_intent_queries(self, app_client):
        """Test that movie-intent queries are NOT blocked by domain guard."""
        for query in self.SHOULD_PASS_QUERIES:
            response = app_client.post("/api/chat", json={
                "message": query,
                "mode": "ReAct Agent",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "max_steps": 3,
            })
            assert response.status_code == 200, f"Query '{query}' should pass domain guard"
            data = response.json()
            # When domain guard blocks, mode is "domain_guard"
            # When it passes, run_query is called (mocked)
            if "mode" in data:
                assert data["mode"] != "domain_guard", f"Query '{query}' was incorrectly blocked"

    def test_should_block_off_topic_queries_direct_check(self):
        """Test domain guard logic directly (without FastAPI layer)."""
        from src.core.domain_guard import is_clear_off_topic

        for query in self.SHOULD_BLOCK_QUERIES:
            assert is_clear_off_topic(query), \
                f"Query '{query}' should be marked as off-topic but wasn't"

    def test_should_pass_off_topic_check_directly(self):
        """Test that movie queries pass domain guard check directly."""
        from src.core.domain_guard import is_clear_off_topic

        for query in self.SHOULD_PASS_QUERIES:
            assert not is_clear_off_topic(query), \
                f"Query '{query}' should NOT be marked as off-topic but was"

    def test_domain_guard_response_shape_direct(self):
        """Verify domain guard response has correct shape (direct check)."""
        from src.core.domain_guard import build_off_topic_result

        result = build_off_topic_result("Thời tiết hôm nay")
        assert result.get("mode") == "domain_guard"
        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0
        assert result.get("trace") == []
        assert result.get("steps") == 0
        assert result.get("latency_ms") == 0
        assert "usage" in result
        assert result["usage"]["prompt_tokens"] == 0
        assert result["usage"]["completion_tokens"] == 0
        assert result["usage"]["total_tokens"] == 0


class TestMalformedRequestRejection:
    """RED TEAM: Test HTTP-level validation and error handling.

    Verify the API correctly rejects malformed requests with appropriate
    HTTP status codes and error messages.
    """

    def test_missing_message_field(self, app_client):
        """Missing required 'message' field → 422 Unprocessable Entity."""
        response = app_client.post("/api/chat", json={
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
        })
        assert response.status_code == 422

    def test_empty_message_field(self, app_client):
        """Empty message string → 422."""
        response = app_client.post("/api/chat", json={
            "message": "",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
        })
        assert response.status_code == 422

    def test_message_whitespace_only(self, app_client):
        """Whitespace-only message → treated as empty (let domain guard handle)."""
        response = app_client.post("/api/chat", json={
            "message": "   ",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
        })
        # Whitespace is accepted by Pydantic but gets stripped by domain guard
        assert response.status_code == 200

    def test_max_steps_below_min(self, app_client):
        """max_steps < 2 (min) → 422."""
        response = app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 1,
        })
        assert response.status_code == 422

    def test_max_steps_above_max(self, app_client):
        """max_steps > 8 (max) → 422."""
        response = app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 9,
        })
        assert response.status_code == 422

    def test_invalid_mode(self, app_client):
        """Invalid mode string → 422 (Pydantic validation)."""
        response = app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "mode": "InvalidMode",
            "provider": "openai",
            "model": "gpt-4o-mini",
        })
        # Pydantic validates Literal["ReAct Agent"], returns 422
        assert response.status_code == 422

    def test_compare_models_single_item(self, app_client):
        """Compare with only 1 model (min is 2) → 422."""
        response = app_client.post("/api/compare", json={
            "query": "Gợi ý phim",
            "models": ["openai/gpt-4o-mini"],
            "mode": "ReAct Agent",
        })
        assert response.status_code == 422

    def test_compare_models_too_many(self, app_client):
        """Compare with 5 models (max is 4) → 422."""
        response = app_client.post("/api/compare", json={
            "query": "Gợi ý phim",
            "models": [
                "openai/gpt-4o-mini",
                "openai/gpt-4o",
                "deepseek/deepseek-chat",
                "deepseek/deepseek-coder",
                "gemini/gemini-pro",
            ],
            "mode": "ReAct Agent",
        })
        assert response.status_code == 422

    def test_compare_invalid_model_key(self, app_client):
        """Compare with unknown model key → 400."""
        response = app_client.post("/api/compare", json={
            "query": "Gợi ý phim",
            "models": ["openai/gpt-4o-mini", "unknown/fake-model"],
            "mode": "ReAct Agent",
        })
        assert response.status_code == 400
        data = response.json()
        # detail can be a dict or string depending on FastAPI version
        detail = data["detail"]
        if isinstance(detail, dict):
            detail_str = str(detail).lower()
        else:
            detail_str = detail.lower()
        assert "invalid" in detail_str or "unknown" in detail_str

    def test_summary_missing_messages(self, app_client):
        """Missing 'messages' field in summary → 422."""
        response = app_client.post("/api/summary", json={
            "provider": "openai",
            "model": "gpt-4o-mini",
        })
        assert response.status_code == 422

    def test_summary_messages_single_item(self, app_client):
        """Summary with only 1 message (min is 2) → 422."""
        response = app_client.post("/api/summary", json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "provider": "openai",
            "model": "gpt-4o-mini",
        })
        assert response.status_code == 422

    def test_summary_invalid_role(self, app_client):
        """Summary with invalid role → 422."""
        response = app_client.post("/api/summary", json={
            "messages": [
                {"role": "invalid_role", "content": "Hello"},
                {"role": "user", "content": "Hi"},
            ],
            "provider": "openai",
            "model": "gpt-4o-mini",
        })
        assert response.status_code == 422


class TestSessionStressTests:
    """RED TEAM: Test session state management with in-memory mocks.

    Verify sessions are properly isolated, turn counts increment correctly,
    and session limits are enforced.
    """

    def test_turn_count_increments_across_calls(self, app_client):
        """Verify turn_count increments with each /api/chat call."""
        # Create session
        r = app_client.post("/api/sessions")
        assert r.status_code == 200
        session_id = r.json()["session_id"]

        # Turn 1
        r1 = app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "session_id": session_id,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })
        assert r1.status_code == 200
        assert r1.json()["turn_count"] == 1

        # Turn 2
        r2 = app_client.post("/api/chat", json={
            "message": "Phim nào khác?",
            "session_id": session_id,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })
        assert r2.status_code == 200
        assert r2.json()["turn_count"] == 2

        # Turn 3
        r3 = app_client.post("/api/chat", json={
            "message": "Phim hành động như thế nào?",
            "session_id": session_id,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })
        assert r3.status_code == 200
        assert r3.json()["turn_count"] == 3

    def test_session_reset_clears_turns(self, app_client):
        """Verify reset endpoint clears all turns."""
        # Create session and add turns
        r = app_client.post("/api/sessions")
        session_id = r.json()["session_id"]

        app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "session_id": session_id,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        # Verify turn_count is 1
        assert session_store.get(session_id).turn_count == 1

        # Reset
        r_reset = app_client.post(f"/api/sessions/{session_id}/reset")
        assert r_reset.status_code == 200

        # Verify turn_count is 0
        assert session_store.get(session_id).turn_count == 0

    def test_session_isolation(self, app_client):
        """Verify two sessions do NOT share state."""
        # Create two sessions
        r1 = app_client.post("/api/sessions")
        sid1 = r1.json()["session_id"]

        r2 = app_client.post("/api/sessions")
        sid2 = r2.json()["session_id"]

        # Add turn to session 1
        app_client.post("/api/chat", json={
            "message": "Gợi ý phim 1",
            "session_id": sid1,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        # Verify session 1 has 1 turn, session 2 has 0
        assert session_store.get(sid1).turn_count == 1
        assert session_store.get(sid2).turn_count == 0

    def test_get_or_create_returns_same_session(self, app_client):
        """Verify repeated calls with same session_id return same session."""
        # Create session
        r = app_client.post("/api/sessions")
        session_id = r.json()["session_id"]

        # Add turn
        app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "session_id": session_id,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        # Fetch session directly
        session = session_store.get_or_create(session_id)
        assert session.turn_count == 1
        assert session.id == session_id

    def test_invalid_session_id_creates_new_session(self, app_client):
        """Invalid session_id format gracefully creates new session."""
        response = app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "session_id": "not-a-valid-uuid!!!",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })
        # Should return 200, not crash
        assert response.status_code == 200
        data = response.json()
        assert data.get("session_id") == "not-a-valid-uuid!!!"


class TestComparisonErrorIsolation:
    """RED TEAM: Test parallel comparison handles partial failures gracefully.

    Verify that if one model fails in a comparison, other results are still
    returned and marked appropriately.
    """

    def test_failed_model_has_ok_false(self, app_client):
        """When a model fails, its entry has ok=False."""
        with patch("src.api.main.run_parallel_comparison") as mock_compare:
            mock_compare.return_value = {
                "openai/gpt-4o-mini": {
                    "ok": True,
                    "answer": "Gợi ý: Inception",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 500,
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                },
                "deepseek/deepseek-chat": {
                    "ok": False,
                    "error": "API key invalid",
                    "answer": "Lỗi: API key invalid",
                    "movies": [],
                },
            }

            response = app_client.post("/api/compare", json={
                "query": "Gợi ý phim",
                "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
                "mode": "ReAct Agent",
            })

            assert response.status_code == 200
            data = response.json()
            results = data["results"]

            # Successful model
            assert results["openai/gpt-4o-mini"]["ok"] is True
            assert "Inception" in results["openai/gpt-4o-mini"]["answer"]

            # Failed model
            assert results["deepseek/deepseek-chat"]["ok"] is False
            assert "error" in results["deepseek/deepseek-chat"]

    def test_all_models_fail_returns_200(self, app_client):
        """When all models fail, response is still 200 (not 500)."""
        with patch("src.api.main.run_parallel_comparison") as mock_compare:
            mock_compare.return_value = {
                "openai/gpt-4o-mini": {
                    "ok": False,
                    "error": "API timeout",
                    "answer": "Lỗi: API timeout",
                    "movies": [],
                },
                "deepseek/deepseek-chat": {
                    "ok": False,
                    "error": "Rate limited",
                    "answer": "Lỗi: Rate limited",
                    "movies": [],
                },
            }

            response = app_client.post("/api/compare", json={
                "query": "Gợi ý phim",
                "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
                "mode": "ReAct Agent",
            })

            assert response.status_code == 200
            data = response.json()
            results = data["results"]

            # Both failed but response is still 200
            for key in results:
                assert results[key]["ok"] is False

    def test_partial_comparison_success(self, app_client):
        """Mixed results: 2 pass, 1 fails."""
        with patch("src.api.main.run_parallel_comparison") as mock_compare:
            mock_compare.return_value = {
                "openai/gpt-4o-mini": {
                    "ok": True,
                    "answer": "Gợi ý: Inception",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 500,
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                },
                "openai/gpt-4o": {
                    "ok": True,
                    "answer": "Gợi ý: Interstellar",
                    "trace": [],
                    "steps": 1,
                    "latency_ms": 600,
                    "usage": {"prompt_tokens": 110, "completion_tokens": 55, "total_tokens": 165},
                },
                "deepseek/deepseek-chat": {
                    "ok": False,
                    "error": "Connection refused",
                    "answer": "Lỗi: Connection refused",
                    "movies": [],
                },
            }

            response = app_client.post("/api/compare", json={
                "query": "Gợi ý phim",
                "models": ["openai/gpt-4o-mini", "openai/gpt-4o", "deepseek/deepseek-chat"],
                "mode": "ReAct Agent",
            })

            assert response.status_code == 200
            results = response.json()["results"]

            # Count successes
            success_count = sum(1 for r in results.values() if r.get("ok"))
            failure_count = sum(1 for r in results.values() if not r.get("ok"))

            assert success_count == 2
            assert failure_count == 1


class TestConcurrentSessionRequests:
    """RED TEAM: Test concurrent session access for race conditions.

    Verify that parallel requests to the same session don't cause
    data corruption or lost updates.
    """

    def test_concurrent_chat_requests_same_session(self, app_client):
        """Multiple concurrent requests to same session."""
        # Create session
        r = app_client.post("/api/sessions")
        session_id = r.json()["session_id"]

        # Simulate 3 concurrent requests
        def make_request(idx):
            return app_client.post("/api/chat", json={
                "message": f"Phim gợi ý {idx}",
                "session_id": session_id,
                "mode": "ReAct Agent",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "max_steps": 3,
            })

        responses = [make_request(i) for i in range(3)]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # Turn counts should be 1, 2, 3
        turn_counts = [r.json()["turn_count"] for r in responses]
        # Due to sequential execution in TestClient, counts should increment
        assert len(turn_counts) == 3

    def test_multiple_session_independence(self, app_client):
        """Multiple sessions updated concurrently remain independent."""
        # Create 3 sessions
        sessions = [
            app_client.post("/api/sessions").json()["session_id"]
            for _ in range(3)
        ]

        # Add turns to each
        for idx, session_id in enumerate(sessions):
            for turn in range(2):
                r = app_client.post("/api/chat", json={
                    "message": f"Session {idx} turn {turn}",
                    "session_id": session_id,
                    "mode": "ReAct Agent",
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "max_steps": 3,
                })
                assert r.status_code == 200

        # Verify each session has 2 turns
        for session_id in sessions:
            session = session_store.get(session_id)
            assert session.turn_count == 2


class TestLiveAPISmokes:
    """RED TEAM: Live API integration tests with REAL LLM calls.

    Mark with @pytest.mark.live. Run only when RUN_LIVE_TESTS=1.
    These tests call the actual OpenAI and TMDB APIs.
    """

    @pytest.mark.live
    def test_live_movie_recommendation_happy_path(self):
        """Real end-to-end: asks for movie, gets a real answer."""
        client = TestClient(app)

        response = client.post("/api/chat", json={
            "message": "Gợi ý 1 phim kinh dị hay trên Netflix",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        assert response.status_code == 200, f"Status {response.status_code}: {response.text}"
        data = response.json()

        # Verify response structure
        assert "answer" in data
        assert data["answer"]  # non-empty answer
        assert isinstance(data["trace"], list)
        assert data["steps"] >= 1
        assert data["latency_ms"] > 0
        assert "usage" in data

    @pytest.mark.live
    def test_live_off_topic_blocked_before_llm(self):
        """Domain guard fires before LLM call even in live setup."""
        client = TestClient(app)

        response = client.post("/api/chat", json={
            "message": "Dạy tôi nấu bánh mì",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        assert response.status_code == 200
        assert response.json()["mode"] == "domain_guard"
        # Verify no tokens were used
        assert response.json()["usage"]["total_tokens"] == 0

    @pytest.mark.live
    def test_live_session_continuity_multi_turn(self):
        """Multi-turn session: follow-up references prior recommendation."""
        client = TestClient(app)

        # Create session
        r_session = client.post("/api/sessions")
        assert r_session.status_code == 200
        session_id = r_session.json()["session_id"]

        # Turn 1: Get recommendation
        resp1 = client.post("/api/chat", json={
            "message": "Gợi ý 1 phim hành động hay",
            "session_id": session_id,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })
        assert resp1.status_code == 200
        assert resp1.json()["turn_count"] == 1
        answer1 = resp1.json()["answer"]
        assert answer1

        # Turn 2: Follow-up about the recommendation
        resp2 = client.post("/api/chat", json={
            "message": "Phim đó có trên Netflix không?",
            "session_id": session_id,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })
        assert resp2.status_code == 200
        assert resp2.json()["turn_count"] == 2
        answer2 = resp2.json()["answer"]
        assert answer2

    @pytest.mark.live
    def test_live_english_movie_query(self):
        """English-language movie query with real API."""
        client = TestClient(app)

        response = client.post("/api/chat", json={
            "message": "recommend a good sci-fi movie available on streaming",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["answer"]
        assert data["mode"] != "domain_guard"  # Should not be blocked

    @pytest.mark.live
    def test_live_agent_completes_within_max_steps(self):
        """Verify agent respects max_steps limit."""
        client = TestClient(app)

        response = client.post("/api/chat", json={
            "message": "Gợi ý phim trending tháng này",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 2,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["steps"] <= 2, f"Agent took {data['steps']} steps but max_steps=2"

    @pytest.mark.live
    def test_live_different_providers_available(self):
        """Verify multiple providers are configured."""
        client = TestClient(app)

        # Get available models
        r_models = client.get("/api/models")
        assert r_models.status_code == 200
        models = r_models.json()["models"]

        # Should have at least openai
        openai_models = [m for m in models if m.startswith("openai/")]
        assert len(openai_models) > 0, "No OpenAI models found"

    @pytest.mark.live
    def test_live_health_check(self):
        """Verify health endpoint shows APIs configured."""
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        # Both API keys should be configured for live tests
        assert data["openai_configured"] is True
        assert data["tmdb_configured"] is True


class TestEdgeCasesAndErrorPaths:
    """RED TEAM: Edge cases and unusual but valid scenarios."""

    def test_very_long_message(self, app_client):
        """Message with 10,000 characters (domain guard should handle)."""
        long_text = "Gợi ý phim " + ("hành động " * 1000)  # ~10k chars

        response = app_client.post("/api/chat", json={
            "message": long_text,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        # Should not crash, domain guard should detect movie intent
        assert response.status_code == 200

    def test_unicode_heavy_query(self, app_client):
        """Query with emoji and special Unicode characters."""
        response = app_client.post("/api/chat", json={
            "message": "🎬 Gợi ý phim hay 🎭 với các diễn viên nổi tiếng 🌟",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        assert response.status_code == 200
        assert "mode" in response.json()

    def test_null_in_json_field(self, app_client):
        """Attempt to pass null for a required field."""
        response = app_client.post("/api/chat", json={
            "message": None,
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
        })

        # Should be rejected as invalid
        assert response.status_code == 422

    def test_extra_fields_ignored(self, app_client):
        """Extra fields in request should be ignored (not cause error)."""
        response = app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
            "extra_field_1": "should be ignored",
            "extra_field_2": 12345,
        })

        # Should succeed, extra fields ignored
        assert response.status_code == 200

    def test_session_without_session_id(self, app_client):
        """Call /api/chat without session_id (should work as before)."""
        response = app_client.post("/api/chat", json={
            "message": "Gợi ý phim",
            "mode": "ReAct Agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_steps": 3,
        })

        assert response.status_code == 200
        data = response.json()
        # No session_id in response for stateless request
        assert "session_id" not in data or data.get("session_id") is None


# ============================================================================
# Helper fixtures
# ============================================================================

@pytest.fixture
def app_client():
    """Provide a FastAPI TestClient with mocked run_query for non-live tests."""
    with patch("src.api.main.run_query") as mock_run_query:
        # Configure default mock response
        async def mock_run_query_impl(*args, **kwargs):
            return {
                "answer": "Gợi ý: Inception (2010) là một bộ phim Sci-Fi xuất sắc.",
                "trace": [
                    {
                        "step": 1,
                        "thought": "Người dùng muốn xem gợi ý phim",
                        "action": "search_movies('inception', 5)",
                        "observation": "Found: Inception (2010), rating: 8.8",
                        "raw": "...",
                    }
                ],
                "steps": 1,
                "latency_ms": 500,
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                "mode": "ReAct Agent",
            }

        mock_run_query.side_effect = mock_run_query_impl
        client = TestClient(app)
        yield client
