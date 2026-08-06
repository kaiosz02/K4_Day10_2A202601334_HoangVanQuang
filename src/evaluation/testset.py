from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Build evaluation test set from clean DataFrame with summary, authors, date, and categories questions."""
    if len(df) == 0:
        empty_set: list[dict[str, Any]] = []
        write_json(Path(output_path), empty_set)
        return empty_set

    # Pick up to 4 representative papers deterministically
    sample_df = df.head(min(4, len(df)))
    test_set: list[dict[str, Any]] = []

    for idx, row in sample_df.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        summary = str(row.get("summary", ""))
        authors = str(row.get("authors_joined", row.get("authors", "")))
        published = str(row.get("published", ""))
        categories = str(row.get("categories_joined", row.get("categories", "")))

        # 1. Summary question
        test_set.append(
            {
                "id": f"q_sum_{idx}_{paper_id}",
                "question_type": "summary",
                "question": f"What is the main summary of the paper '{title}'?",
                "ground_truth": summary,
                "ground_truth_doc_ids": [paper_id],
            }
        )

        # 2. Authors question
        test_set.append(
            {
                "id": f"q_auth_{idx}_{paper_id}",
                "question_type": "authors",
                "question": f"Who authored the paper '{title}'?",
                "ground_truth": authors,
                "ground_truth_doc_ids": [paper_id],
            }
        )

        # 3. Publication date question
        test_set.append(
            {
                "id": f"q_date_{idx}_{paper_id}",
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": published,
                "ground_truth_doc_ids": [paper_id],
            }
        )

        # 4. Categories question
        test_set.append(
            {
                "id": f"q_cat_{idx}_{paper_id}",
                "question_type": "categories",
                "question": f"What categories belong to the paper '{title}'?",
                "ground_truth": categories,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    write_json(Path(output_path), test_set)
    return test_set
