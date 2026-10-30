"""Factory tạo chat model theo LLM_PROVIDER. Node chỉ gọi `get_chat_model()`, không import provider trực tiếp.

Mọi client đặt timeout và số lần thử lại tường minh: provider treo/chậm → exception → agent rơi về câu trả lời xác định
(fail-safe), không giữ request của backend vô thời hạn.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from ai_core.config import settings

LLM_TIMEOUT_SECONDS = 20.0
LLM_MAX_RETRIES = 1


@lru_cache(maxsize=1)
def get_chat_model() -> BaseChatModel:
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            max_tokens=4096,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
        )
    if provider in {"openai", "openrouter"}:
        from langchain_openai import ChatOpenAI  # pip install -e ".[openai]"

        options = {"base_url": "https://openrouter.ai/api/v1"} if provider == "openrouter" else {}
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            temperature=0,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            **options,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama  # pip install -e ".[ollama]"

        # ChatOllama không có max_retries; timeout đặt trên httpx client bên dưới.
        return ChatOllama(model=settings.llm_model, client_kwargs={"timeout": LLM_TIMEOUT_SECONDS})
    raise ValueError(f"Unknown LLM_PROVIDER={settings.llm_provider!r}")
