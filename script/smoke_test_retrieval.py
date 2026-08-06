from __future__ import annotations

import pandas as pd

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent


def run_smoke_test():
    print("=== Running Smoke Test for src/retrieval ===")
    settings = load_settings()
    
    # Check if clean data exists, otherwise create a minimal mock DataFrame for smoke testing
    if settings.paths.clean_csv.exists():
        print(f"Loading cleaned data from {settings.paths.clean_csv}...")
        df = pd.read_csv(settings.paths.clean_csv)
    else:
        print("Clean data not found. Creating sample mock DataFrame for smoke testing...")
        df = pd.DataFrame([
            {
                "paper_id": "10.1016/j.artint.2023.103900",
                "title": "Agentic Retrieval Augmented Generation for Academic Research",
                "text_for_embedding": "Title: Agentic Retrieval Augmented Generation for Academic Research. Summary: We present an agentic RAG framework designed for scholarly papers search using vector similarity.",
                "published": "2024-01-15",
                "authors_joined": "Alice Smith, Bob Jones",
                "categories_joined": "cs.AI, cs.IR",
                "summary": "We present an agentic RAG framework designed for scholarly papers search using vector similarity.",
                "abs_url": "https://doi.org/10.1016/j.artint.2023.103900",
                "pdf_url": "https://doi.org/10.1016/j.artint.2023.103900.pdf"
            },
            {
                "paper_id": "10.1145/3394486.3403011",
                "title": "Data Observability in Machine Learning Pipelines",
                "text_for_embedding": "Title: Data Observability in Machine Learning Pipelines. Summary: Observability metrics and automated quality checks ensure LLM data pipeline health.",
                "published": "2024-02-01",
                "authors_joined": "Carol Danvers",
                "categories_joined": "cs.DB",
                "summary": "Observability metrics and automated quality checks ensure LLM data pipeline health.",
                "abs_url": "https://doi.org/10.1145/3394486.3403011",
                "pdf_url": "https://doi.org/10.1145/3394486.3403011.pdf"
            }
        ])

    print("Building LocalEmbeddingIndex...")
    index = LocalEmbeddingIndex.build(df=df, settings=settings)
    print(f"Index built successfully in collection: '{index.collection_name}'. Document count: {len(index.documents)}")

    # 1. Smoke Query (Semantic Search)
    query = "agentic retrieval augmented generation"
    print(f"\n--- [1/3] Smoke Query: '{query}' ---")
    results = index.search(query=query, top_k=2)
    for i, res in enumerate(results, 1):
        print(f"  Result #{i}:")
        print(f"    - Paper ID: {res.paper_id}")
        print(f"    - Title   : {res.title}")
        print(f"    - Score   : {res.score:.4f}")
        print(f"    - Content : {res.content[:100]}...")

    # 2. Smoke Lookup by paper_id
    test_id = df.iloc[0]["paper_id"]
    print(f"\n--- [2/3] Smoke Lookup by paper_id: '{test_id}' ---")
    found_by_id = index.lookup(test_id)
    if found_by_id:
        print(f"  [SUCCESS] Found record: Title='{found_by_id['title']}'")
    else:
        print(f"  [FAILED] Record not found for paper_id '{test_id}'")

    # 3. Smoke Lookup by Title
    test_title = df.iloc[0]["title"]
    print(f"\n--- [3/3] Smoke Lookup by Title: '{test_title}' ---")
    found_by_title = index.lookup(test_title)
    if found_by_title:
        print(f"  [SUCCESS] Found record: paper_id='{found_by_title['paper_id']}'")
    else:
        print(f"  [FAILED] Record not found for title '{test_title}'")

    print("\n=== Smoke Test Completed Successfully! ===")


if __name__ == "__main__":
    run_smoke_test()
