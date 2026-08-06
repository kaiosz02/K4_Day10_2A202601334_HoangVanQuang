from __future__ import annotations

import itertools
from functools import lru_cache
import time
from typing import Callable, TypeVar

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sentence_transformers import SentenceTransformer

T = TypeVar("T")
_embedding_key_cycles: dict[str, itertools.cycle] = {}


@lru_cache(maxsize=4)
def _load_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


class GeminiEmbeddings(Embeddings):
    def __init__(self, model_name: str = "gemini-embedding-2", api_key: str | None = None):
        requested_model = (model_name or "").strip()
        normalized = requested_model.lower()
        is_sentence_transformer = normalized.startswith("sentence-transformers/")

        self._delegate: Embeddings
        if is_sentence_transformer:
            self._delegate = MiniLMEmbeddings(model_name=requested_model)
            self._delegates = [self._delegate]
            self._rotation_group = f"sentence-transformers::{requested_model}"
            return

        # Gemini model names may be provided as "gemini-embedding-2" or full "models/...".
        gemini_model = requested_model or "gemini-embedding-2"
        if not gemini_model.startswith("models/"):
            gemini_model = f"models/{gemini_model}"
        keys = [k.strip() for k in (api_key or "").split(",") if k.strip()]
        if keys:
            self._delegates = [
                GoogleGenerativeAIEmbeddings(model=gemini_model, google_api_key=key)
                for key in keys
            ]
        else:
            self._delegates = [GoogleGenerativeAIEmbeddings(model=gemini_model, google_api_key=None)]
        self._delegate = self._delegates[0]
        self._rotation_group = f"gemini-emb::{gemini_model}"

    def _rotated_delegates(self) -> list[Embeddings]:
        if len(self._delegates) <= 1:
            return self._delegates
        if self._rotation_group not in _embedding_key_cycles:
            _embedding_key_cycles[self._rotation_group] = itertools.cycle(range(len(self._delegates)))
        start_idx = next(_embedding_key_cycles[self._rotation_group])
        return self._delegates[start_idx:] + self._delegates[:start_idx]

    @staticmethod
    def _is_rate_limited(exc: Exception) -> bool:
        message = str(exc)
        return "RESOURCE_EXHAUSTED" in message or "429" in message

    def _invoke_with_retry(self, fn: Callable[..., T], *args, **kwargs) -> T:
        if len(self._delegates) == 1:
            for attempt in range(3):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if not self._is_rate_limited(exc) or attempt == 2:
                        raise
                    # Gemini free-tier embedding has per-minute quota; wait then retry.
                    time.sleep(50)
            raise RuntimeError("Unexpected retry flow in GeminiEmbeddings.")

        last_rate_limit_error: Exception | None = None
        for _attempt in range(3):
            for delegate in self._rotated_delegates():
                bound_fn = getattr(delegate, fn.__name__)
                try:
                    return bound_fn(*args, **kwargs)
                except Exception as exc:
                    if not self._is_rate_limited(exc):
                        raise
                    last_rate_limit_error = exc
                    continue
            # All keys were rate-limited in this round.
            time.sleep(50)
        if last_rate_limit_error is not None:
            raise last_rate_limit_error
        raise RuntimeError("Unexpected retry flow in GeminiEmbeddings.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._invoke_with_retry(self._delegate.embed_documents, texts)

    def embed_query(self, text: str) -> list[float]:
        return self._invoke_with_retry(self._delegate.embed_query, text)


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = _load_model(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()
