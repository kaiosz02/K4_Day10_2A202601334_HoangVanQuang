from __future__ import annotations

from pathlib import Path
import sys

# Ensure src is in sys.path
src_dir = Path(__file__).resolve().parents[1] / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pandas as pd

from core.config import load_settings
from core.utils import write_json
from retrieval.index import LocalEmbeddingIndex


def main():
    settings = load_settings()
    df = pd.read_csv(settings.paths.clean_csv)
    index = LocalEmbeddingIndex.build(df=df, settings=settings, embeddings_output_path=settings.paths.embeddings_json)

    print("=== SAVING BASELINE QUERIES BENCHMARK ===")

    benchmark_queries = []
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        query = f"{row['title'][:40]} {row['summary'][:40]}"
        results = index.search(query, top_k=1)
        top_res = results[0] if results else None

        benchmark_queries.append(
            {
                "query_type": "semantic_search",
                "query": query,
                "expected_paper_id": row["paper_id"],
                "baseline_top_retrieved_id": top_res.paper_id if top_res else None,
                "baseline_top_retrieved_title": top_res.title if top_res else None,
                "baseline_top_score": round(top_res.score, 4) if top_res else 0.0,
                "is_exact_match": top_res.paper_id == row["paper_id"] if top_res else False,
            }
        )

    sample_paper = df.iloc[0]
    lookup_id_res = index.lookup(sample_paper["paper_id"])
    lookup_title_res = index.lookup(sample_paper["title"])

    lookup_records = [
        {
            "lookup_type": "paper_id",
            "lookup_key": sample_paper["paper_id"],
            "found": lookup_id_res is not None,
            "title": lookup_id_res["title"] if lookup_id_res else None,
        },
        {
            "lookup_type": "title",
            "lookup_key": sample_paper["title"],
            "found": lookup_title_res is not None,
            "paper_id": lookup_title_res["paper_id"] if lookup_title_res else None,
        },
    ]

    benchmark_payload = {
        "description": "Baseline reference queries & lookups stored for cross-phase comparison (Baseline vs Corrupted vs Repaired).",
        "timestamp": settings.paths.embeddings_json.stat().st_mtime if settings.paths.embeddings_json.exists() else None,
        "semantic_queries": benchmark_queries,
        "exact_lookups": lookup_records,
    }

    output_path = settings.paths.project_dir / "data" / "eval" / "baseline_queries_benchmark.json"
    write_json(output_path, benchmark_payload)

    print(f"Saved baseline query benchmark to: {output_path}")
    print(f"Semantic search benchmark count: {len(benchmark_queries)}")
    print(f"Exact lookup benchmark count:   {len(lookup_records)}")
    print("=== SUCCESS ===")


if __name__ == "__main__":
    main()
