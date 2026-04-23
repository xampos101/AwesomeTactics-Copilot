"""Batch benchmark runner — execute questions across models and store results."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from app.config import EVAL_DIR, get_providers
from evaluation.score import compute_all_scores
from rag.pipeline import run_query

logger = logging.getLogger(__name__)


def load_questions(path: Path | None = None) -> list[dict]:
    """Load benchmark questions from JSON."""
    if path is None:
        path = EVAL_DIR / "benchmark_questions.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_benchmark(
    questions: list[dict] | None = None,
    max_questions: int | None = None,
    provider_names: list[str] | None = None,
) -> list[dict]:
    """Run questions across all (or specified) providers, returning scored rows."""
    if questions is None:
        questions = load_questions()
    if max_questions:
        questions = questions[:max_questions]

    providers = get_providers()
    if provider_names:
        providers = [p for p in providers if p.name in provider_names]

    if not providers:
        logger.error("No providers configured. Set .env variables.")
        return []

    results: list[dict] = []

    for i, q in enumerate(questions):
        for prov in providers:
            mode = q.get("type", "recommend")
            if mode in ("adversarial", "ambiguous"):
                mode = "recommend"

            logger.info(
                "[%d/%d] %s | %s | %s",
                i + 1, len(questions), q["id"], prov.name, q["question"][:60],
            )

            r = run_query(
                user_query=q["question"],
                mode=mode,
                provider=prov,
                n_results=8,
            )

            parsed = r.get("parsed", {})
            scores = compute_all_scores(
                parsed=parsed,
                retrieved=r.get("retrieved_tactics", []),
                question_type=q.get("type", "recommend"),
                latency=r.get("latency_seconds", 0),
            )

            results.append(
                {
                    "question_id": q["id"],
                    "question_type": q.get("type", ""),
                    "difficulty": q.get("difficulty", ""),
                    "model": prov.name,
                    "is_commercial": prov.is_commercial,
                    **scores,
                    "error": r.get("error", ""),
                }
            )

    return results


def save_results(results: list[dict], path: Path | None = None) -> Path:
    """Write results to a timestamped JSON file."""
    if path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = EVAL_DIR / f"benchmark_results_{ts}.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Results saved to %s", path)
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    max_q = int(sys.argv[1]) if len(sys.argv) > 1 else None
    results = run_benchmark(max_questions=max_q)
    if results:
        out = save_results(results)
        print(f"\nDone. {len(results)} rows saved to {out}")

        import pandas as pd

        df = pd.DataFrame(results)
        print("\n=== Summary by Model ===")
        summary = df.groupby("model")[
            ["groundedness", "citation_presence", "parse_success", "dark_tactic_safety", "latency_seconds"]
        ].mean()
        print(summary.to_string())
    else:
        print("No results generated. Check provider configuration.")
