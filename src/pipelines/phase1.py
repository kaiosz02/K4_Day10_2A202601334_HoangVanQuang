from __future__ import annotations

from datetime import datetime

from core.config import load_settings
from core.utils import write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Execute end-to-end Phase 1 Baseline Data Pipeline."""
    print("=== [PHASE 1] Starting Baseline Data Pipeline ===")
    settings = load_settings()
    run_dt = datetime.now()

    # 1. Fetch raw records from Crossref source
    print("Step 1: Fetching raw records from Crossref API...")
    raw_records = fetch_source_records(settings)
    print(f"-> Fetched {len(raw_records)} raw paper records.")

    # 2. Clean data and construct DataFrame
    print("Step 2: Cleaning and normalizing paper records...")
    clean_df = build_clean_dataframe(raw_records, run_date=run_dt)
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))
    print(f"-> Saved {len(clean_df)} clean records to {settings.paths.clean_csv}")

    # 3. Build ChromaDB Vector Index
    print("Step 3: Building MiniLM ChromaDB vector index...")
    index = LocalEmbeddingIndex.build(
        df=clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"-> Created collection '{index.collection_name}' with {len(index.documents)} documents.")

    # 4. Generate or load evaluation test set
    print("Step 4: Building evaluation test set...")
    build_test_set(df=clean_df, output_path=settings.paths.eval_testset)
    print(f"-> Evaluation test set generated at {settings.paths.eval_testset}")

    # 5. Evaluate baseline pipeline performance
    print("Step 5: Evaluating baseline RAG pipeline metrics...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(f"-> Retrieval Hit Rate: {eval_bundle.summary.get('retrieval_hit_rate', 0):.4f}")
    print(f"-> Mean Token F1:     {eval_bundle.summary.get('mean_token_f1', 0):.4f}")
    print(f"-> Judge Accuracy:    {eval_bundle.summary.get('judge_accuracy', 0):.4f}")

    # 6. Run Data Quality Checks & Freshness Monitoring
    print("Step 6: Running Data Quality Checks & Freshness Monitoring...")
    quality = run_data_quality_checks(clean_df, settings, "quality_report_baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    print(f"-> Quality Checks Status: {'PASSED ✅' if quality.get('success') else 'FAILED ❌'}")
    print(f"-> Freshness SLA Status: {'FRESH ✅' if freshness.get('is_fresh') else 'STALE ⚠️'}")

    # 7. Generate Phase 1 Baseline Markdown Report
    print("Step 7: Generating Phase 1 Baseline Markdown Report...")
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "raw_records_count": len(raw_records),
        "clean_records_count": len(clean_df),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"-> Phase 1 Report written to {settings.paths.baseline_report}")

    # 8. Agent Demo Question Execution
    print("Step 8: Running Agent Demo Question...")
    try:
        agent = build_agent(settings, index)
        demo_question = f"What is the main topic of paper '{clean_df.iloc[0]['title']}'?"
        demo_answer = run_agent_question(agent, demo_question)
        write_json(settings.paths.demo_answers, [{"question": demo_question, "answer": demo_answer}])
        print(f"-> Agent Demo Answer: {demo_answer[:100]}...")
    except Exception as e:
        print(f"-> Agent Demo skipped or failed gracefully: {e}")

    print("=== [PHASE 1] Baseline Data Pipeline Completed Successfully! ===")


if __name__ == "__main__":
    main()
