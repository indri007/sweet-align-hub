"""
Evaluate the RAG job-matching pipeline (agents/rag_agent.match_cv_to_jobs) using
Ragas metrics.

This exercises the REAL pipeline the app uses in production — same vector
store, same LLM client, same prompt — not a re-implementation. For each sample
CV in evaluation/eval_dataset.py, it:
  1. Runs match_cv_to_jobs() to get retrieved job listings + the AI-generated
     recommendation narrative (exactly what a user sees on Step B).
  2. Packages (question, retrieved_contexts, response) into a Ragas sample.
  3. Scores it with reference-free metrics (no hand-labeled ground truth needed):
       - Faithfulness        — is the AI narrative actually grounded in the
                                retrieved job listings, or is it hallucinating?
       - ResponseRelevancy   — does the narrative actually address the CV?
       - LLMContextPrecisionWithoutReference
                              — are the retrieved job listings relevant, as
                                judged against the generated response?

Usage:
    python evaluation/run_ragas_eval.py
    python evaluation/run_ragas_eval.py --output results.json

Requires GEMINI_API_KEY (or OPENAI_API_KEY) to be configured in .env — the
same judge LLM is used both to generate summaries (via the app's own
llm_client) and to score them (via Ragas' LangchainLLMWrapper).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # allow running as a script

from evaluation.ragas_compat import apply_ragas_compat_shim
apply_ragas_compat_shim()

import config  # noqa: E402
from agents.rag_agent import match_cv_to_jobs  # noqa: E402
from evaluation.eval_dataset import EVAL_CVS  # noqa: E402


def build_samples() -> list:
    """Run the real RAG pipeline for each eval CV and package results for Ragas."""
    from ragas import SingleTurnSample

    samples = []
    for case in EVAL_CVS:
        print(f"  Matching CV: {case['id']} ({case['expected_category']})...")
        result = match_cv_to_jobs(case["cv_text"], top_k=config.TOP_K_RESULTS)
        matches = result.get("matches", [])
        ai_summary = result.get("ai_summary")

        if not matches:
            print(f"    WARNING: no matches retrieved for {case['id']}, skipping.")
            continue
        if not ai_summary:
            print(f"    WARNING: no AI summary generated for {case['id']}, skipping.")
            continue

        contexts = [m.get("document", "") for m in matches if m.get("document")]

        samples.append(
            SingleTurnSample(
                user_input=(
                    f"Berdasarkan CV berikut, rekomendasikan lowongan pekerjaan yang "
                    f"paling cocok:\n\n{case['cv_text'][:3000]}"
                ),
                retrieved_contexts=contexts,
                response=ai_summary,
            )
        )
    return samples


def get_judge_llm_and_embeddings():
    """
    Judge model for scoring: reuses whichever provider is configured for the
    app (Gemini by default). Embeddings for context-based metrics use the
    same local sentence-transformers model the app uses by default for
    ChromaDB, so evaluation doesn't require extra API keys/cost.
    """
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import HuggingFaceEmbeddings

    if not config.is_llm_configured():
        raise RuntimeError(
            "No LLM configured. Set GEMINI_API_KEY (or OPENAI_API_KEY) in .env "
            "before running the evaluation."
        )

    if config.LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GEMINI_API_KEY,
            temperature=0,
        )
    else:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=config.OPENAI_API_KEY,
            temperature=0,
        )

    judge_llm = LangchainLLMWrapper(llm)
    embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
    return judge_llm, embeddings


def main():
    parser = argparse.ArgumentParser(description="Ragas evaluation for job-matching RAG")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Optional path to save results as JSON (e.g. results.json)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Ragas Evaluation — Job Matching RAG Pipeline")
    print("=" * 60)

    print("\n[1/3] Running RAG pipeline on evaluation CVs...")
    samples = build_samples()
    if not samples:
        print("No samples could be built (LLM/vector store unavailable?). Aborting.")
        sys.exit(1)

    print(f"\n[2/3] Scoring {len(samples)} sample(s) with Ragas...")
    from ragas import EvaluationDataset, evaluate
    from ragas.metrics import (
        Faithfulness,
        ResponseRelevancy,
        LLMContextPrecisionWithoutReference,
    )

    judge_llm, embeddings = get_judge_llm_and_embeddings()
    dataset = EvaluationDataset(samples=samples)

    result = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            ResponseRelevancy(),
            LLMContextPrecisionWithoutReference(),
        ],
        llm=judge_llm,
        embeddings=embeddings,
    )

    print("\n[3/3] Results")
    print("-" * 60)
    df = result.to_pandas()
    for _, row in df.iterrows():
        print(f"  faithfulness={row.get('faithfulness', float('nan')):.2f}  "
              f"answer_relevancy={row.get('answer_relevancy', float('nan')):.2f}  "
              f"context_precision={row.get('llm_context_precision_without_reference', float('nan')):.2f}")

    print("-" * 60)
    print("Averages:")
    for col in ["faithfulness", "answer_relevancy", "llm_context_precision_without_reference"]:
        if col in df.columns:
            print(f"  {col}: {df[col].mean():.3f}")

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(
            json.dumps(json.loads(df.to_json(orient="records")), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nSaved detailed results to {out_path}")


if __name__ == "__main__":
    main()
