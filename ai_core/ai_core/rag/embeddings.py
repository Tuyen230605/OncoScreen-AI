"""Embedding function cho Chroma theo EMBEDDING_PROVIDER."""

from __future__ import annotations

from functools import lru_cache

from ai_core.config import settings


@lru_cache(maxsize=1)
def get_embedding_function():
    """Trả chromadb EmbeddingFunction."""
    if settings.embedding_provider == "local":
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

        return SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
    if settings.embedding_provider == "openai":
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        return OpenAIEmbeddingFunction(api_key=settings.llm_api_key, model_name=settings.embedding_model)
    raise ValueError(f"Unknown EMBEDDING_PROVIDER={settings.embedding_provider!r}")
