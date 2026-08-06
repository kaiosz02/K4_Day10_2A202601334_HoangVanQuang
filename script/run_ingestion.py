from datetime import datetime, UTC
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.config import load_settings
from ingestion.crossref import fetch_source_records
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe

def main():
    settings = load_settings()
    print(f"Source Query: '{settings.source_query}'")
    print("--- Step 1: Fetching Crossref records ---")
    records = fetch_source_records(settings)
    print(f"Successfully fetched/parsed {len(records)} records.")
    print(f"Raw HTTP response saved to: {settings.paths.raw_api_response}")
    print(f"Raw records saved to: {settings.paths.raw_records_json}")

    print("\n--- Step 2: Cleaning Data ---")
    run_date = datetime.now(UTC)
    df = build_clean_dataframe(records, run_date)
    print(f"Clean DataFrame shape: {df.shape}")

    if not df.empty:
        print("\nSample Titles Fetched:")
        for idx, title in enumerate(df["title"].head(5), 1):
            print(f"  {idx}. {title}")

    save_clean_dataframe(df, settings.paths.clean_csv, settings.paths.clean_json)
    print(f"\nClean CSV saved to: {settings.paths.clean_csv}")
    print(f"Clean JSON saved to: {settings.paths.clean_json}")

if __name__ == "__main__":
    main()
