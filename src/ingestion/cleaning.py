from __future__ import annotations

from datetime import UTC, datetime
import html

from pathlib import Path
import re

import pandas as pd

from ingestion.crossref import PaperRecord


def clean_text(text: str) -> str:
    """Loai bo html/xml tags, unescape html entities va normalize khoang trang."""
    if not text:
        return ""
    # 1. Unescape HTML entities (e.g. &amp; -> &, &lt; -> <)
    cleaned = html.unescape(text)
    # 2. Strip XML/HTML tags (e.g. <jats:p>, <b>, <i>)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # 3. Normalize multiple spaces and newlines into a single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed.

    Rules:
    1. Normalize title, summary, authors, categories (loai bo xml/html tags).
    2. Drop record khong co title hoac summary qua ngan (< 100 ky tu).
    3. Parse published date va tinh age_days so voi run_date.
    4. Tao cac cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding (Title: [title] | Authors: [authors] | Summary: [summary])
    5. Drop duplicates theo paper_id.
    6. Sort dataframe va return.
    """
    clean_rows: list[dict] = []

    # Ensure run_date is datetime object for date calculations
    if isinstance(run_date, str):
        try:
            run_date = datetime.fromisoformat(run_date)
        except Exception:
            run_date = datetime.now(UTC)

    ref_date = run_date.date() if isinstance(run_date, datetime) else run_date

    for record in records:
        title = clean_text(record.title)
        summary = clean_text(record.summary)

        # Rule: Drop missing title or summary < 100 chars
        if not title or len(summary) < 100:
            continue

        # Authors & Categories joined
        authors = [clean_text(a) for a in record.authors if a]
        authors_joined = ", ".join(authors) if authors else "Unknown"

        categories = [clean_text(c) for c in record.categories if c]
        categories_joined = ", ".join(categories) if categories else "General"
        primary_category = record.primary_category or (categories[0] if categories else "General")

        # Freshness: published date & age_days calculation
        published_str = record.published
        try:
            pub_dt = datetime.strptime(published_str, "%Y-%m-%d")
            age_days = (ref_date - pub_dt.date()).days
            if age_days < 0:
                age_days = 0
        except Exception:
            pub_dt = datetime(1970, 1, 1)
            published_str = "1970-01-01"
            age_days = (ref_date - pub_dt.date()).days

        summary_chars = len(summary)
        text_for_embedding = f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"

        clean_rows.append(
            {
                "paper_id": record.paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published_str,
                "updated": record.updated or published_str,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": record.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(clean_rows)

    if df.empty:
        # Return empty dataframe with expected schema
        return pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors",
                "categories",
                "primary_category",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "authors_joined",
                "categories_joined",
                "summary_chars",
                "age_days",
                "text_for_embedding",
            ]
        )

    # Drop duplicates by paper_id
    df = df.drop_duplicates(subset=["paper_id"]).copy()

    # Sort dataframe by published descending, then paper_id
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)

    return df


def save_clean_dataframe(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    """Luu cleaned dataframe vao data/clean/ (ca 2 dang CSV va JSON)."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)

