from __future__ import annotations

from datetime import datetime
import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Execute end-to-end Data Corruption, Evaluation, Repair, and Comparison Pipeline."""
    print("=== [PHASE 2] Starting Data Corruption & Automated Repair Pipeline ===")
    settings = load_settings()
    run_dt = datetime.now()

    # 1. Load baseline clean DataFrame and metrics
    print("Step 1: Loading baseline clean dataset...")
    if settings.paths.clean_csv.exists():
        clean_df = pd.read_csv(settings.paths.clean_csv)
    else:
        print("-> Clean CSV not found. Building clean DataFrame from source...")
        raw_records = fetch_source_records(settings)
        clean_df = build_clean_dataframe(raw_records, run_date=run_dt)
        write_csv(clean_df, settings.paths.clean_csv)

    if settings.paths.baseline_metrics.exists():
        baseline_metrics = read_json(settings.paths.baseline_metrics)
    else:
        baseline_metrics = {"retrieval_hit_rate": 1.0, "mean_token_f1": 0.8, "judge_accuracy": 1.0, "mean_judge_score": 4.5}

    # 2. Generate corrupted DataFrame
    print("Step 2: Simulating data corruptions (drop latest, blank summary, inject noise, truncate, stale dates)...")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    print(f"-> Corrupted DataFrame saved ({len(corrupted_df)} rows) to {settings.paths.corrupted_clean_csv}")

    # 3. Build Corrupted Vector Index
    print("Step 3: Building corrupted ChromaDB vector index ('papers-corrupted')...")
    corrupted_index = LocalEmbeddingIndex.build(
        df=corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )

    # 4. Evaluate Corrupted Index on baseline test set
    print("Step 4: Re-evaluating metrics on corrupted index...")
    corrupted_eval = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"-> Corrupted Hit Rate: {corrupted_eval.summary.get('retrieval_hit_rate', 0):.4f}")
    print(f"-> Corrupted Token F1: {corrupted_eval.summary.get('mean_token_f1', 0):.4f}")

    # 5. Run Quality Checks & Freshness on Corrupted Data
    print("Step 5: Running observability quality & freshness checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "quality_report_corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, settings.paths.quality_dir / "freshness_report_corrupted.json"
    )
    print(f"-> Corrupted Quality Pass: {'PASSED' if corrupted_quality.get('success') else 'FAILED'}")
    print(f"-> Corrupted Freshness:   {'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE'}")

    # 6. Repair Data from Authoritative Raw Source
    print("Step 6: Repairing dataset from raw source snapshot...")
    if settings.paths.raw_records_json.exists():
        raw_records = load_raw_records(settings.paths.raw_records_json)
    else:
        raw_records = fetch_source_records(settings)

    repaired_df = build_clean_dataframe(raw_records, run_date=run_dt)
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"-> Repaired DataFrame saved ({len(repaired_df)} rows) to {settings.paths.repaired_clean_csv}")

    # 7. Build Repaired Vector Index
    print("Step 7: Building repaired ChromaDB vector index ('papers-repaired')...")
    repaired_index = LocalEmbeddingIndex.build(
        df=repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )

    # 8. Re-evaluate Repaired Index
    print("Step 8: Re-evaluating metrics on repaired index...")
    repaired_eval = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"-> Repaired Hit Rate: {repaired_eval.summary.get('retrieval_hit_rate', 0):.4f}")
    print(f"-> Repaired Token F1: {repaired_eval.summary.get('mean_token_f1', 0):.4f}")

    # 9. Run Quality Checks & Freshness on Repaired Data
    print("Step 9: Running observability checks on repaired data...")
    repaired_quality = run_data_quality_checks(repaired_df, settings, "quality_report_repaired")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, settings.paths.quality_dir / "freshness_report_repaired.json"
    )

    # 10. Generate Comparison Report
    print("Step 10: Generating Corruption vs Repair Comparison Report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval.summary,
        repaired_metrics=repaired_eval.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"-> Comparison Markdown Report written to {settings.paths.comparison_report}")

    print("=== [PHASE 2] Corruption & Automated Repair Pipeline Completed Successfully! ===")


if __name__ == "__main__":
    main()
