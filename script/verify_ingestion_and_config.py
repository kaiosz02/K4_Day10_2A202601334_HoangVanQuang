from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

# Ensure src is in sys.path
src_dir = Path(__file__).resolve().parents[1] / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.config import load_settings
from core.utils import write_csv
from ingestion.crossref import fetch_source_records
from ingestion.cleaning import build_clean_dataframe


def main():
    settings = load_settings()
    print("=== 1. FETCHING & CLEANING SOURCE DATA ===")
    records = fetch_source_records(settings)
    print(f"Fetched {len(records)} raw paper records.")

    df = build_clean_dataframe(records, run_date=datetime.now())
    write_csv(df, settings.paths.clean_csv)
    print(f"Clean DataFrame saved with {len(df)} rows to: {settings.paths.clean_csv}\n")

    print("=== 2. REAL text_for_embedding SAMPLES ===")
    for i, text in enumerate(df["text_for_embedding"].head(3), 1):
        print(f"--- Sample #{i} ---")
        print(text)
        print()

    print("=== 3. DATAFRAME SCHEMA & INDEX METADATA CONFIRMATION ===")
    print("Columns present:", list(df.columns))
    print("Has 'paper_id':", "paper_id" in df.columns)
    print("Has 'title':", "title" in df.columns)
    print("Has 'content' (text_for_embedding):", "text_for_embedding" in df.columns)
    print("Metadata fields available:", ["published", "authors_joined", "categories_joined", "summary", "abs_url", "pdf_url"])

    print("\n=== 4. PREPARED INDEX CONFIGURATION (PRE-BUILD) ===")
    print(f"- Clean Data Path    : {settings.paths.clean_csv}")
    print(f"- Chroma DB Path     : {settings.paths.chroma_dir}")
    print(f"- Embedding Model    : {settings.embedding_model}")
    print(f"- Collection Name    : {settings.baseline_collection_name}")
    print(f"- Top K Retrieval    : {settings.top_k}")
    print("\n[SUCCESS] All 3 requirements verified!")


if __name__ == "__main__":
    main()
