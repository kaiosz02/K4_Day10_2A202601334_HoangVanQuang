from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if len(df) == 0:
        return []

    # Chọn tối đa 3 paper đại diện
    sample_df = df.sample(n=min(3, len(df)), random_state=42)
    test_set = []

    for _, row in sample_df.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        summary = str(row.get("summary", ""))
        authors = str(row.get("authors", ""))
        published = str(row.get("published", ""))
        categories = str(row.get("categories", ""))

        # Câu hỏi về summary
        test_set.append({
            "id": f"q_sum_{paper_id}",
            "question_type": "summary",
            "question": f"What is the summary or main topic of the paper '{title}'?",
            "ground_truth": summary,
            "ground_truth_doc_ids": [paper_id]
        })

        # Câu hỏi về authors
        test_set.append({
            "id": f"q_auth_{paper_id}",
            "question_type": "authors",
            "question": f"Who are the authors of the paper '{title}'?",
            "ground_truth": authors,
            "ground_truth_doc_ids": [paper_id]
        })

        # Câu hỏi về date
        test_set.append({
            "id": f"q_date_{paper_id}",
            "question_type": "date",
            "question": f"When was the paper '{title}' published?",
            "ground_truth": published,
            "ground_truth_doc_ids": [paper_id]
        })

        # Câu hỏi về categories
        test_set.append({
            "id": f"q_cat_{paper_id}",
            "question_type": "categories",
            "question": f"What are the categories associated with the paper '{title}'?",
            "ground_truth": categories,
            "ground_truth_doc_ids": [paper_id]
        })

    write_json(output_path, test_set)
    return test_set
