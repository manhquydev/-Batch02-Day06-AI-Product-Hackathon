"""Async multi-model parallel comparison using asyncio.gather."""

import asyncio
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.services.query_runner import run_query


@lru_cache(maxsize=1)
def build_model_options() -> tuple[str, ...]:
    """Return 'provider/model' strings for all available providers."""
    from src.core.factory import DEEPSEEK_MODELS, GEMINI_MODELS, OPENAI_MODELS, is_local_provider_available
    from src.core.gemini_provider import list_available_models as list_gemini_models
    from src.core.ollama_provider import is_ollama_running, list_available_models

    options: List[str] = [f"openai/{m}" for m in OPENAI_MODELS]
    options += [f"deepseek/{m}" for m in DEEPSEEK_MODELS]
    if os.getenv("GEMINI_API_KEY"):
        gemini_models = list_gemini_models(api_key=os.getenv("GEMINI_API_KEY")) or list(GEMINI_MODELS)
        preferred = [m for m in GEMINI_MODELS if m in gemini_models]
        extras = [m for m in gemini_models if m not in preferred]
        options += [f"gemini/{m}" for m in preferred + extras[:2]]
    if is_ollama_running():
        ollama_models = list_available_models() or ["llama3.2:3b"]
        options += [f"ollama/{m}" for m in ollama_models]
    project_root = Path(__file__).resolve().parents[2]
    local_model_path = Path(os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf"))
    if not local_model_path.is_absolute():
        local_model_path = project_root / local_model_path
    if is_local_provider_available() and local_model_path.exists():
        options += [f"local/{local_model_path.name}"]
    return tuple(options)


async def run_parallel_comparison(
    selected_models: List[str],
    mode: str,
    query: str,
    max_steps: int,
    run_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Run multiple provider/model combos in parallel using asyncio.gather."""
    executor_fn = run_fn or run_query

    async def _run_one(key: str) -> tuple[str, Dict[str, Any]]:
        provider, model = key.split("/", 1)
        try:
            res = await executor_fn(mode, query, provider, model, max_steps)
            return key, {"ok": True, **res}
        except Exception as exc:
            return key, {"ok": False, "error": str(exc), "answer": f"Lỗi: {exc}"}

    pairs = await asyncio.gather(*[_run_one(key) for key in selected_models])
    return {key: result for key, result in pairs}
