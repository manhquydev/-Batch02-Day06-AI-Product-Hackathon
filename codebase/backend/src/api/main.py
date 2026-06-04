"""
FastAPI backend for Movie ReAct Agent demo.

Run from backend/:
    uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from src.services.comparison import build_model_options, run_parallel_comparison
from src.services.query_runner import EXAMPLE_PROMPTS, VALID_MODES, run_query
from src.tools.registry import TOOL_SPECS
from src.utils.movies import extract_movies_from_trace

app = FastAPI(
    title="Movie ReAct Agent API",
    description="Chatbot baseline vs ReAct Agent · TMDB tools",
    version="1.0.0",
)

# Configure allowed origins for both User and Admin Frontends
FRONTEND_USER_URL = os.getenv("FRONTEND_USER_URL", "http://localhost:3000")
FRONTEND_ADMIN_URL = os.getenv("FRONTEND_ADMIN_URL", "http://localhost:3001")

allowed_origins = [
    FRONTEND_USER_URL,
    FRONTEND_ADMIN_URL,
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ModeType = Literal["ReAct Agent", "ReAct Agent v2", "ReAct Agent v1", "Chatbot Baseline"]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    mode: ModeType = "ReAct Agent"
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_steps: int = Field(default=5, ge=2, le=8)
    session_id: Optional[str] = None


class CompareRequest(BaseModel):
    query: str = Field(..., min_length=1)
    models: List[str] = Field(..., min_length=2, max_length=4, description="provider/model keys")
    mode: ModeType = "ReAct Agent"
    max_steps: int = Field(default=5, ge=2, le=8)


def _serialize_tools() -> List[Dict[str, Any]]:
    return [
        {"name": t["name"], "description": t["description"], "example": t.get("example")}
        for t in TOOL_SPECS
    ]


def _enrich_result(result: Dict[str, Any]) -> Dict[str, Any]:
    return {**result, "movies": extract_movies_from_trace(result.get("trace"))}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "tmdb_configured": bool(os.getenv("TMDB_API_KEY")),
    }


@app.get("/api/models")
def list_models():
    return {"models": list(build_model_options())}


@app.get("/api/tools")
def list_tools():
    return {"tools": _serialize_tools()}


@app.get("/api/example-prompts")
def example_prompts():
    return {"prompts": EXAMPLE_PROMPTS}


@app.get("/api/modes")
def list_modes():
    return {"modes": list(VALID_MODES)}


# In-memory chat session store (session_id -> list of message dicts)
chat_sessions: Dict[str, List[Dict[str, str]]] = {}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    if body.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Choose one of: {VALID_MODES}")
    try:
        history = None
        if body.session_id:
            if body.session_id not in chat_sessions:
                chat_sessions[body.session_id] = []
            # Keep last 10 messages (5 turns) to prevent context token overflow
            history = chat_sessions[body.session_id][-10:]

        result = await run_query(
            body.mode,
            body.message,
            body.provider,
            body.model,
            body.max_steps,
            history=history,
        )

        if body.session_id:
            chat_sessions[body.session_id].append({"role": "User", "content": body.message})
            chat_sessions[body.session_id].append({"role": "Agent", "content": result.get("answer", "")})

        return _enrich_result(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/compare")
async def compare(body: CompareRequest):
    if body.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Choose one of: {VALID_MODES}")
    available = set(build_model_options())
    invalid = [m for m in body.models if m not in available]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail={"message": "Unknown model keys", "invalid": invalid, "available": list(available)},
        )
    try:
        results = await run_parallel_comparison(body.models, body.mode, body.query, body.max_steps)
        enriched = {}
        for key, res in results.items():
            enriched[key] = {**res, "movies": extract_movies_from_trace(res.get("trace"))}
        return {"results": enriched}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
