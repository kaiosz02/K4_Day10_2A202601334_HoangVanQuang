import pandas as pd
from core.config import load_settings
from evaluation.testset import build_test_set
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question

def run_cp2():
    import os
    print("Loading settings...")
    settings = load_settings()
    if settings.google_api_key:
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key
    df = pd.read_csv(settings.paths.clean_csv)
    
    print("\n[CP2] Building Test Set...")
    test_set = build_test_set(df, settings.paths.eval_testset)
    print(f"Created test set with {len(test_set)} questions at {settings.paths.eval_testset}")

    print("\n[CP2] Building Embedding Index (papers-baseline)...")
    index = LocalEmbeddingIndex.build(df, settings)
    print(f"Created index collection: {index.collection_name}")
    print(f"Manifest written to: {settings.paths.embeddings_json}")

    print("\n[CP2] Smoke Test: Semantic Search")
    results = index.search("agentic intelligence framework", top_k=1)
    if results:
        print(f"Found: {results[0].title} with score {results[0].score:.4f}")
    else:
        print("No results found.")
    
    print("\n[CP2] Smoke Test: Exact Lookup")
    if results:
        lookup_res = index.lookup(results[0].paper_id)
        if lookup_res:
            print(f"Lookup Found: {lookup_res['title']}")

    print("\n[CP2] Smoke Test: Agent QA")
    try:
        agent = build_agent(settings, index)
        question = f"Who are the authors of '{results[0].title}'?" if results else "What is autonomous phishing detection?"
        answer = run_agent_question(agent, question)
        print(f"Q: {question}")
        print(f"A: {answer}")
    except Exception as e:
        print(f"Agent creation or execution failed: {e}")

if __name__ == '__main__':
    run_cp2()
