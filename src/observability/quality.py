from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json

def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    row_count = len(df)
    
    if row_count > 0 and "paper_id" in df.columns:
        null_ids = int(df["paper_id"].isnull().sum())
        unique_ids = int(df["paper_id"].nunique())
        is_id_unique = (unique_ids == row_count)
    else:
        null_ids = row_count
        unique_ids = 0
        is_id_unique = False
        
    null_titles = int(df["title"].isnull().sum()) if row_count > 0 and "title" in df.columns else row_count
    
    if row_count > 0 and "summary" in df.columns:
        short_summaries = int(df["summary"].fillna("").astype(str).str.len().lt(10).sum())
    else:
        short_summaries = row_count
        
    if row_count > 0 and "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = row_count

    results = {
        "row_count": row_count,
        "null_ids": null_ids,
        "is_id_unique": is_id_unique,
        "null_titles": null_titles,
        "short_summaries": short_summaries,
        "stale_rows": stale_rows,
        "pass": (null_ids == 0 and is_id_unique and null_titles == 0 and short_summaries == 0)
    }
    
    out_path = settings.paths.quality_dir / report_name
    write_json(out_path, results)
    return results


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    row_count = len(df)
    
    if row_count > 0 and "published" in df.columns:
        published_dates = pd.to_datetime(df["published"], errors="coerce")
        latest_published = str(published_dates.max().date()) if not pd.isna(published_dates.max()) else "Unknown"
        oldest_published = str(published_dates.min().date()) if not pd.isna(published_dates.min()) else "Unknown"
    else:
        latest_published = "Unknown"
        oldest_published = "Unknown"
        
    if row_count > 0 and "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0
        
    is_fresh = (stale_rows == 0)
    
    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": row_count,
        "is_fresh": is_fresh
    }
    
    write_json(report_path, payload)
    return payload
