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
    from src.core.factory import OPENAI_MODELS

    options: List[str] = [f"openai/{m}" for m in OPENAI_MODELS]
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
