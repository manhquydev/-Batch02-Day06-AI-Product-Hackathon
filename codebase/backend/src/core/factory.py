import os
from typing import Optional

from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider

OPENAI_MODELS = ("gpt-4o",)


def get_llm_provider(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMProvider:
    return OpenAIProvider(
        model_name="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
    )
