from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate various types of data corruption for testing observability and resilience.

    Corruptions performed:
    1. Drop some latest records.
    2. Set summary to blank on selected rows.
    3. Inject random noise into summary text.
    4. Truncate titles on selected rows.
    5. Shift published date to be stale (> 180 days).
    6. Add duplicate rows.
    7. Rebuild text_for_embedding, age_days, and summary_chars.
    8. Write corruption log to output_log_path.
    """
    corrupted_df = df.copy()
    corruption_log: list[dict[str, Any]] = []

    total_orig = len(corrupted_df)
    if total_orig == 0:
        write_json(Path(output_log_path), {"corruptions": [], "total_rows_before": 0, "total_rows_after": 0})
        return corrupted_df

    # 1. Drop latest 2 records
    if len(corrupted_df) > 3:
        dropped_ids = corrupted_df.iloc[:2]["paper_id"].tolist()
        corrupted_df = corrupted_df.iloc[2:].reset_index(drop=True)
        corruption_log.append(
            {
                "type": "drop_latest_records",
                "count": len(dropped_ids),
                "affected_paper_ids": dropped_ids,
                "description": "Dropped latest records to simulate missing source records.",
            }
        )

    # 2. Blank summary on 2 rows
    if len(corrupted_df) > 2:
        blank_idx = [0, 1]
        blank_ids = corrupted_df.iloc[blank_idx]["paper_id"].tolist()
        corrupted_df.loc[blank_idx, "summary"] = ""
        corruption_log.append(
            {
                "type": "blank_summary",
                "count": len(blank_ids),
                "affected_paper_ids": blank_ids,
                "description": "Blanked out summaries to simulate missing payload content.",
            }
        )

    # 3. Inject noise into summary on 2 rows
    if len(corrupted_df) > 4:
        noise_idx = [2, 3]
        noise_ids = corrupted_df.iloc[noise_idx]["paper_id"].tolist()
        for idx in noise_idx:
            orig_sum = corrupted_df.loc[idx, "summary"]
            corrupted_df.loc[idx, "summary"] = f"[NOISE GARBAGE ERR 0x99] {orig_sum} [UNRELATED ADVERTISEMENT]"
        corruption_log.append(
            {
                "type": "inject_noise",
                "count": len(noise_ids),
                "affected_paper_ids": noise_ids,
                "description": "Injected random text noise into summaries.",
            }
        )

    # 4. Truncate title on 2 rows
    if len(corrupted_df) > 5:
        trunc_idx = [4, 5]
        trunc_ids = corrupted_df.iloc[trunc_idx]["paper_id"].tolist()
        for idx in trunc_idx:
            orig_title = str(corrupted_df.loc[idx, "title"])
            corrupted_df.loc[idx, "title"] = orig_title[:10] + "..."
        corruption_log.append(
            {
                "type": "truncate_title",
                "count": len(trunc_ids),
                "affected_paper_ids": trunc_ids,
                "description": "Truncated paper titles to incomplete snippets.",
            }
        )

    # 5. Make published date stale (> 365 days ago) on 3 rows
    if len(corrupted_df) > 3:
        stale_idx = [0, 1, 2]
        stale_ids = corrupted_df.iloc[stale_idx]["paper_id"].tolist()
        for idx in stale_idx:
            corrupted_df.loc[idx, "published"] = "2020-01-01"
            corrupted_df.loc[idx, "age_days"] = 1500
        corruption_log.append(
            {
                "type": "stale_published_date",
                "count": len(stale_ids),
                "affected_paper_ids": stale_ids,
                "description": "Shifted publication dates back to 2020 to violate freshness SLA.",
            }
        )

    # 6. Add duplicate rows
    if len(corrupted_df) > 2:
        dupes = corrupted_df.iloc[:2].copy()
        corrupted_df = pd.concat([corrupted_df, dupes], ignore_index=True)
        corruption_log.append(
            {
                "type": "add_duplicates",
                "count": len(dupes),
                "affected_paper_ids": dupes["paper_id"].tolist(),
                "description": "Duplicated rows to test unique ID validation.",
            }
        )

    # 7. Rebuild summary_chars and text_for_embedding
    corrupted_df["summary_chars"] = corrupted_df["summary"].fillna("").astype(str).str.len()
    corrupted_df["text_for_embedding"] = (
        "Title: " + corrupted_df["title"].astype(str) + ". Summary: " + corrupted_df["summary"].astype(str)
    )

    # 8. Write corruption log
    log_payload = {
        "timestamp": datetime.now().isoformat(),
        "total_rows_before": total_orig,
        "total_rows_after": len(corrupted_df),
        "corruptions": corruption_log,
    }
    write_json(Path(output_log_path), log_payload)

    return corrupted_df
