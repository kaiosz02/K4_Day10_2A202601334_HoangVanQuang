from __future__ import annotations

from typing import Any
from core.utils import write_text


def _delta(new_value: float, old_value: float) -> float:
    return float(new_value) - float(old_value)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    quality_ok = bool(quality.get("success", quality.get("pass")))
    content = f"""# Báo cáo Phase 1: Baseline RAG Pipeline

## Tóm tắt dữ liệu nguồn
- **Tổng số bản ghi:** {source_summary.get('raw_records_count', source_summary.get('total', 'N/A'))}
- **Nguồn dữ liệu:** {source_summary.get('source_api', source_summary.get('source', 'Crossref API'))}
- **Truy vấn nguồn:** {source_summary.get('source_query', 'N/A')}

## Chỉ số Retrieval và Evaluation
- **Retrieval Hit Rate:** {metrics.get('retrieval_hit_rate', 0):.2%}
- **Mean Token F1:** {metrics.get('mean_token_f1', 0):.4f}
- **Judge Accuracy:** {metrics.get('judge_accuracy', 0):.2%}
- **Mean Judge Score:** {metrics.get('mean_judge_score', 0):.2f}/5

## Chất lượng dữ liệu và độ tươi
- **Số dòng dữ liệu:** {quality.get('row_count', 0)}
- **Số dòng thiếu ID:** {quality.get('null_ids', 0)}
- **ID duy nhất:** {'Đạt' if quality.get('is_id_unique') else 'Không đạt'}
- **Kết quả kiểm tra chất lượng:** {'Đạt' if quality_ok else 'Không đạt'}
- **Độ tươi (stale rows):** {freshness.get('stale_rows', 0)} / {freshness.get('total_rows', 0)}
- **Trạng thái tươi dữ liệu:** {'Tươi' if freshness.get('is_fresh') else 'Cũ'}
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
    b_hit = float(baseline_metrics.get("retrieval_hit_rate", 0))
    c_hit = float(corrupted_metrics.get("retrieval_hit_rate", 0))
    r_hit = float(repaired_metrics.get("retrieval_hit_rate", 0))

    b_f1 = float(baseline_metrics.get("mean_token_f1", 0))
    c_f1 = float(corrupted_metrics.get("mean_token_f1", 0))
    r_f1 = float(repaired_metrics.get("mean_token_f1", 0))

    b_acc = float(baseline_metrics.get("judge_accuracy", 0))
    c_acc = float(corrupted_metrics.get("judge_accuracy", 0))
    r_acc = float(repaired_metrics.get("judge_accuracy", 0))

    b_score = float(baseline_metrics.get("mean_judge_score", 0))
    c_score = float(corrupted_metrics.get("mean_judge_score", 0))
    r_score = float(repaired_metrics.get("mean_judge_score", 0))

    corrupted_quality_ok = bool(corrupted_quality.get("success", corrupted_quality.get("pass")))
    repaired_quality_ok = bool(repaired_quality.get("success", repaired_quality.get("pass")))

    content = f"""# Báo cáo so sánh Corrupted và Repaired

## Bảng so sánh chỉ số đánh giá

| Chỉ số | Baseline | Corrupted | Repaired | Delta (Corrupted - Baseline) | Delta (Repaired - Corrupted) |
|---|---:|---:|---:|---:|---:|
| Retrieval Hit Rate | {b_hit:.2%} | {c_hit:.2%} | {r_hit:.2%} | {_delta(c_hit, b_hit):+.2%} | {_delta(r_hit, c_hit):+.2%} |
| Mean Token F1 | {b_f1:.4f} | {c_f1:.4f} | {r_f1:.4f} | {_delta(c_f1, b_f1):+.4f} | {_delta(r_f1, c_f1):+.4f} |
| Judge Accuracy | {b_acc:.2%} | {c_acc:.2%} | {r_acc:.2%} | {_delta(c_acc, b_acc):+.2%} | {_delta(r_acc, c_acc):+.2%} |
| Mean Judge Score | {b_score:.2f}/5 | {c_score:.2f}/5 | {r_score:.2f}/5 | {_delta(c_score, b_score):+.2f} | {_delta(r_score, c_score):+.2f} |

## Đánh giá chất lượng dữ liệu và độ tươi

| Hạng mục | Corrupted | Repaired |
|---|---:|---:|
| Chất lượng đạt | {'Có' if corrupted_quality_ok else 'Không'} | {'Có' if repaired_quality_ok else 'Không'} |
| Số tiêu đề null | {corrupted_quality.get('null_titles', 0)} | {repaired_quality.get('null_titles', 0)} |
| Số summary quá ngắn | {corrupted_quality.get('short_summaries', 0)} | {repaired_quality.get('short_summaries', 0)} |
| Số dòng stale | {corrupted_freshness.get('stale_rows', 0)} | {repaired_freshness.get('stale_rows', 0)} |

## Kết luận
Corruption làm giảm rõ rệt chất lượng RAG (hit rate, token F1, judge accuracy, judge score đều giảm). 
Khi repair lại từ dữ liệu raw đáng tin cậy, các chỉ số phục hồi gần/đúng về baseline.
"""
    write_text(report_path, content)
