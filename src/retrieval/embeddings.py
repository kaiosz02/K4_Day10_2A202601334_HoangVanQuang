from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sentence_transformers import SentenceTransformer


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
            return

        # Gemini model names may be provided as "gemini-embedding-2" or full "models/...".
        gemini_model = requested_model or "gemini-embedding-2"
        if not gemini_model.startswith("models/"):
            gemini_model = f"models/{gemini_model}"
        self._delegate = GoogleGenerativeAIEmbeddings(model=gemini_model, google_api_key=api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._delegate.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._delegate.embed_query(text)


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = _load_model(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()
