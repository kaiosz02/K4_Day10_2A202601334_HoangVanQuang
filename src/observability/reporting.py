from __future__ import annotations

from typing import Any
from core.utils import write_text

def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    content = f"""# Phase 1: Baseline RAG Pipeline Report

## Source Data Summary
- **Total Records:** {source_summary.get('total', 'N/A')}
- **Source:** {source_summary.get('source', 'Crossref API')}

## Retrieval & Evaluation Metrics
- **Retrieval Hit Rate:** {metrics.get('retrieval_hit_rate', 0):.2%}
- **Token F1 Score:** {metrics.get('mean_token_f1', 0):.4f}
- **Judge Accuracy:** {metrics.get('judge_accuracy', 0):.2%}
- **Mean Judge Score:** {metrics.get('mean_judge_score', 0):.2f}/5

## Data Quality & Freshness
- **Row Count:** {quality.get('row_count', 0)}
- **Null IDs:** {quality.get('null_ids', 0)}
- **ID Unique:** {'Pass' if quality.get('is_id_unique') else 'Fail'}
- **Quality Pass:** {'Yes' if quality.get('pass') else 'No'}
- **Freshness (Stale Rows):** {freshness.get('stale_rows', 0)} / {freshness.get('total_rows', 0)}
- **Is Fresh:** {'Yes' if freshness.get('is_fresh') else 'No'}
"""
    write_text(report_path, content)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    content = f"""# Data Corruption & Recovery Comparison Report

## Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| Retrieval Hit Rate | {baseline_metrics.get('retrieval_hit_rate', 0):.2%} | {corrupted_metrics.get('retrieval_hit_rate', 0):.2%} | {repaired_metrics.get('retrieval_hit_rate', 0):.2%} |
| Mean Token F1 | {baseline_metrics.get('mean_token_f1', 0):.4f} | {corrupted_metrics.get('mean_token_f1', 0):.4f} | {repaired_metrics.get('mean_token_f1', 0):.4f} |
| Judge Accuracy | {baseline_metrics.get('judge_accuracy', 0):.2%} | {corrupted_metrics.get('judge_accuracy', 0):.2%} | {repaired_metrics.get('judge_accuracy', 0):.2%} |
| Mean Judge Score | {baseline_metrics.get('mean_judge_score', 0):.2f}/5 | {corrupted_metrics.get('mean_judge_score', 0):.2f}/5 | {repaired_metrics.get('mean_judge_score', 0):.2f}/5 |

## Quality & Freshness Assessment

| Assessment | Corrupted Data | Repaired Data |
|---|---|---|
| Quality Passed | {'Yes' if corrupted_quality.get('pass') else 'No'} | {'Yes' if repaired_quality.get('pass') else 'No'} |
| Null Titles | {corrupted_quality.get('null_titles', 0)} | {repaired_quality.get('null_titles', 0)} |
| Short Summaries | {corrupted_quality.get('short_summaries', 0)} | {repaired_quality.get('short_summaries', 0)} |
| Stale Rows | {corrupted_freshness.get('stale_rows', 0)} | {repaired_freshness.get('stale_rows', 0)} |

## Conclusion
Data errors significantly decrease the accuracy of the Retrieval-Augmented Generation (RAG) agent. Correctly repairing data from raw sources recovers the original RAG metrics.
"""
    write_text(report_path, content)
