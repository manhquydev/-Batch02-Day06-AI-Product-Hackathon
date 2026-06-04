# Red-Team Adversarial Test Suite

Comprehensive adversarial testing for the Movie ReAct Agent backend using REAL APIs (not mocked).

## Quick Start

### Run all tests WITHOUT live API calls (fast, ~19s):
```bash
cd backend
python -m pytest tests/redteam/ -v --tb=short -m "not live"
```

### Run ONLY live API tests (real OpenAI + TMDB, ~43s):
```bash
cd backend
RUN_LIVE_TESTS=1 python -m pytest tests/redteam/ -v -m live
```

### Run everything (31 non-live + 7 live, ~59s):
```bash
cd backend
RUN_LIVE_TESTS=1 python -m pytest tests/redteam/ -v
```

## Test Categories

| Category | Tests | Status |
|----------|-------|--------|
| Domain Guard & Intent Detection | 4 | ✅ All Pass |
| HTTP-Level Validation | 12 | ✅ All Pass |
| Session State Management | 5 | ✅ All Pass |
| Error Handling & Resilience | 3 | ✅ All Pass |
| Concurrency & Race Conditions | 2 | ✅ All Pass |
| Live API Integration | 7 | ✅ All Pass |
| Edge Cases & Boundaries | 5 | ✅ All Pass |
| **TOTAL** | **38** | **✅ 38/38 Pass** |

## What Gets Tested

### Domain Guard (no LLM calls)
- ✅ Movie-intent queries pass through (23 queries tested)
- ✅ Off-topic queries blocked (16 queries tested)
- ✅ Zero token usage for blocked queries
- ✅ Response structure correct (empty trace, zero steps)

### Input Validation
- ✅ Missing/empty/whitespace-only messages rejected
- ✅ max_steps constraints (2–8) enforced
- ✅ Model count constraints (2–4 for compare) enforced
- ✅ Invalid enums rejected with 422
- ✅ Extra fields ignored gracefully

### Session Management
- ✅ Turn counter increments reliably
- ✅ Sessions properly isolated from each other
- ✅ Reset clears all turns
- ✅ Invalid session IDs handled gracefully
- ✅ Thread-safe concurrent access

### Error Handling
- ✅ Partial failures don't cascade (1 failed model doesn't crash others)
- ✅ All-model-failures return 200 (not 500)
- ✅ Error messages propagated correctly
- ✅ movies[] field present but empty for failed entries

### Live API Integration
- ✅ Real OpenAI API calls work
- ✅ TMDB movie data retrieval works
- ✅ Multi-turn sessions preserve context
- ✅ Language detection (Vietnamese/English) works
- ✅ Agent respects step limits
- ✅ All API keys configured

### Edge Cases
- ✅ Very long messages (~10k chars) handled
- ✅ Unicode + emoji normalized correctly
- ✅ Null values rejected appropriately
- ✅ Stateless mode still works

## File Structure

```
tests/redteam/
├── __init__.py
├── README.md (this file)
└── test_live_adversarial.py (840 lines, 38 tests)
```

## Test Configuration

**pytest.ini** includes:
```ini
[pytest]
asyncio_mode = auto
markers =
    live: marks tests as live (requiring real API keys, deselect with -m "not live")
```

## Environment Requirements

- `.env` file with `OPENAI_API_KEY` and `TMDB_API_KEY` configured
- Python 3.11+
- FastAPI, Pydantic, pytest, pytest-asyncio

## Architecture

```
test_live_adversarial.py
├── TestDomainGuardBypassAttempts (domain guard logic)
├── TestMalformedRequestRejection (HTTP validation)
├── TestSessionStressTests (session isolation & state)
├── TestComparisonErrorIsolation (resilience)
├── TestConcurrentSessionRequests (race conditions)
├── TestLiveAPISmokes (real API integration) *marked with @pytest.mark.live*
└── TestEdgeCasesAndErrorPaths (boundary conditions)
```

## Key Insights

### Strengths
- Domain guard is robust and prevents hallucinations
- Input validation is comprehensive (Pydantic)
- Session management is thread-safe
- Error handling gracefully degrades
- Real API integration works correctly

### What's NOT Tested (Future Work)
- Rate limiting behavior
- TMDB API error scenarios (invalid IDs, timeouts)
- Summarization trigger (turn_limit=10)
- Tool execution edge cases
- Streaming response validation (if added)

## CI/CD Integration

**For GitHub Actions:**

```yaml
# Fast check on every commit
- name: Run red-team tests (non-live)
  run: pytest tests/redteam/ -v -m "not live"

# Nightly or pre-release validation
- name: Run live tests
  if: github.event_name == 'schedule'
  run: RUN_LIVE_TESTS=1 pytest tests/redteam/ -v -m live
```

## Report

Full test report: `plans/reports/tester-20260604-red-team-adversarial-tests.md`

---

**Last Updated:** 2026-06-04  
**Total Tests:** 38  
**Pass Rate:** 100%  
**Execution Time:** ~19s (non-live), ~59s (with live)
