"""Factory tạo chat model theo LLM_PROVIDER. Node chỉ gọi `get_chat_model()`, không import provider trực tiếp."""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from ai_core.config import settings


@lru_cache(maxsize=1)
def get_chat_model() -> BaseChatModel:
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=settings.llm_model, api_key=settings.llm_api_key, max_tokens=4096)
    if provider == "openai":
        from langchain_openai import ChatOpenAI  # pip install -e ".[openai]"

        return ChatOpenAI(model=settings.llm_model, api_key=settings.llm_api_key)
    if provider == "ollama":
        from langchain_ollama import ChatOllama  # pip install -e ".[ollama]"

        return ChatOllama(model=settings.llm_model)
    raise ValueError(f"Unknown LLM_PROVIDER={settings.llm_provider!r}")
