from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class GeminiEmbeddings(Embeddings):
    def __init__(self, model_name: str = "gemini-embedding-2"):
        # Wrap GoogleGenerativeAIEmbeddings
        self.model = GoogleGenerativeAIEmbeddings(model=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)
