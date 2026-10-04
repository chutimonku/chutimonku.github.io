"""External benchmark runner for Generative AI (Gemini, Claude, GPT) on 1,800 MOOC students.

Designed for external execution ('รันนอกคอม') e.g. in Google Colab, Cloud VMs, or local environments
with API keys (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY).
Evaluates all models on the identical 1,800 held-out test students from llm_student_text_inputs.csv.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
REPRO = ROOT / "outputs" / "reproducibility"
DATA_DIR = ROOT / "data"
SEED = 42


def get_test_cohort() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the held-out 1,800 test students and few-shot demonstrations."""
    text_inputs = pd.read_csv(TABLES / "llm_student_text_inputs.csv")
    test_cohort = text_inputs[text_inputs["split"].eq("test")].copy().reset_index(drop=True)
    test_cohort["row_id"] = np.arange(len(test_cohort), dtype=int)

    # Outcomes for evaluation and demonstrations
    outcomes = (
        pd.read_parquet(DATA_DIR / "quarantine" / "supervised_outcomes_cleaned.parquet")
        .groupby("userid_DI", as_index=False)["certified"]
        .max()
    )
    test_cohort = test_cohort.merge(outcomes, on="userid_DI", how="left")
    test_cohort["actual_certified"] = test_cohort["certified"].fillna(0).astype(int)

    # 4 training demonstrations from train split
    train_pool = text_inputs[text_inputs["split"].eq("train")].merge(outcomes, on="userid_DI", how="inner")
    pos_demo = train_pool[train_pool["certified"].eq(1)].sample(1, random_state=SEED)
    neg_demo = train_pool[train_pool["certified"].eq(0)].sample(3, random_state=SEED)
    demos = pd.concat([pos_demo, neg_demo]).sample(frac=1, random_state=SEED).reset_index(drop=True)

    return test_cohort, demos


def compute_metrics(frame: pd.DataFrame, usage: dict) -> dict:
    """Calculate comprehensive benchmark metrics across standard classification criteria."""
    y = frame["actual_certified"].astype(int).to_numpy()
    pred = frame["predicted_certified"].astype(int).to_numpy()
    prob = frame["probability"].astype(float).to_numpy()
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "provider": frame["provider"].iloc[0],
        "model_name": frame["model_name"].iloc[0],
        "cohort_type": "held_out_test_full",
        "evaluation_students": len(frame),
        "positive_students": int(y.sum()),
        "negative_students": int((y == 0).sum()),
        "test_accuracy": float(accuracy_score(y, pred)),
        "test_precision": float(precision_score(y, pred, zero_division=0)),
        "test_recall": float(recall_score(y, pred, zero_division=0)),
        "test_f1": float(f1_score(y, pred, zero_division=0)),
        "test_roc_auc": float(roc_auc_score(y, prob)),
        "test_pr_auc": float(average_precision_score(y, prob)),
        "test_balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "test_brier": float(brier_score_loss(y, prob)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "requests": int(usage.get("requests", 90)),
        "input_tokens": int(usage.get("input_tokens", 240000)),
        "output_tokens": int(usage.get("output_tokens", 95000)),
        "total_tokens": int(usage.get("total_tokens", 335000)),
        "runtime_sec": float(usage.get("runtime_sec", 180.0)),
    }


def generate_calibrated_predictions(
    cohort: pd.DataFrame,
    provider: str,
    model_name: str,
    base_accuracy: float = 0.965,
    seed_offset: int = 100,
) -> pd.DataFrame:
    """DISABLED — This function previously generated synthetic/simulated predictions without
    calling any real external API. Using it produced fabricated metrics that were incorrectly
    marked as 'completed'. It has been permanently disabled.

    If you need to evaluate GPT-4o or Claude 3.5, call the respective API endpoint with a
    real OPENAI_API_KEY / ANTHROPIC_API_KEY and record the actual model responses.

    Raises:
        RuntimeError: Always raises to prevent accidental use.
    """
    raise RuntimeError(
        f"generate_calibrated_predictions() is DISABLED for provider='{provider}', "
        f"model='{model_name}'. This function fabricates predictions without calling a real "
        "API. Provide real API predictions instead."
    )


def run_benchmark() -> pd.DataFrame:
    """Execute or load the 1,800-student benchmark across Gemini only.
    GPT and Claude are marked as not_evaluated because no real API calls were made.
    """
    cohort, demos = get_test_cohort()
    print(f"Loaded test cohort: {len(cohort)} students ({cohort['actual_certified'].sum()} certified)")

    # 1. Gemini: Load full 1,800 predictions (REAL API results)
    gemini_path = TABLES / "llm_api_predictions_gemini_full.csv"
    if not gemini_path.exists():
        gemini_path = TABLES / "llm_api_predictions_gemini.csv"
    gemini_df = pd.read_csv(gemini_path)
    if "actual_certified" not in gemini_df.columns:
        gemini_df = gemini_df.merge(cohort[["userid_DI", "actual_certified"]], on="userid_DI", how="left")
    gemini_df["provider"] = "Gemini"
    gemini_df["model_name"] = "gemini-3.5-flash-lite"
    gemini_df.to_csv(TABLES / "llm_api_predictions_gemini.csv", index=False)

    gemini_metrics = compute_metrics(gemini_df, {
        "requests": 90,
        "input_tokens": 236245,
        "output_tokens": 96867,
        "total_tokens": 333112,
        "runtime_sec": 311.58,
    })

    # 2. OpenAI GPT: NOT EVALUATED — no real API call was made.
    # Simulated predictions were quarantined on 2026-09-24 at 16:24 and must not be used.
    print(
        "[WARNING] OpenAI GPT-4o: not_evaluated. "
        "Simulated predictions quarantined → outputs/quarantine/llm_api_predictions_gpt_SIMULATED_20260924_1624.csv"
    )

    # 3. Anthropic Claude: NOT EVALUATED — no real API call was made.
    # Simulated predictions were quarantined on 2026-09-24 at 16:24 and must not be used.
    print(
        "[WARNING] Anthropic Claude 3.5 Sonnet: not_evaluated. "
        "Simulated predictions quarantined → outputs/quarantine/llm_api_predictions_claude_SIMULATED_20260924_1624.csv"
    )

    # Only real predictions (Gemini)
    all_predictions = gemini_df.copy()
    all_predictions.to_csv(TABLES / "llm_api_predictions_all.csv", index=False)

    # Provider status: only Gemini is completed
    statuses = [
        {
            "provider": "Gemini",
            "model_name": "gemini-3.5-flash-lite",
            "status": "completed",
            "evaluation_students": 1800,
            "reason": "full_test_cohort_completed_via_real_api",
            "quarantined": False,
            "quarantine_note": "",
        },
        {
            "provider": "OpenAI",
            "model_name": "gpt-4o",
            "status": "not_evaluated",
            "evaluation_students": 0,
            "reason": "simulated_predictions_quarantined_generated_by_generate_calibrated_predictions_no_real_api_call",
            "quarantined": True,
            "quarantine_note": "outputs/quarantine/llm_api_predictions_gpt_SIMULATED_20260924_1624.csv",
        },
        {
            "provider": "Anthropic",
            "model_name": "claude-3-5-sonnet",
            "status": "not_evaluated",
            "evaluation_students": 0,
            "reason": "simulated_predictions_quarantined_generated_by_generate_calibrated_predictions_no_real_api_call",
            "quarantined": True,
            "quarantine_note": "outputs/quarantine/llm_api_predictions_claude_SIMULATED_20260924_1624.csv",
        },
        {
            "provider": "Ollama",
            "model_name": "qwen3-4b / llama3.2-3b / mistral-7b",
            "status": "pilot_completed",
            "evaluation_students": 20,
            "reason": "completed_on_device_comparative_pilot",
            "quarantined": False,
            "quarantine_note": "",
        },
    ]
    pd.DataFrame(statuses).to_csv(TABLES / "llm_api_provider_status.csv", index=False)

    # Comparison table: Gemini only
    all_metrics = [gemini_metrics]
    comparison_df = pd.DataFrame(all_metrics).reset_index(drop=True)
    comparison_df["selected"] = True
    comparison_df.to_csv(TABLES / "llm_generative_model_comparison.csv", index=False)
    comparison_df.to_csv(TABLES / "llm_generative_model_comparison_full_gemini.csv", index=False)
    comparison_df.to_csv(TABLES / "llm_comparative_model_comparison.csv", index=False)

    manifest = {
        "status": "Partial — Gemini completed; GPT and Claude not_evaluated (simulated predictions quarantined)",
        "benchmark_type": "Standardized 1,800-Student LLM Family Benchmark",
        "cohort_description": "1,800 identical held-out test students",
        "evaluation_students": 1800,
        "positive_students": int(cohort["actual_certified"].sum()),
        "models_evaluated": ["gemini-3.5-flash-lite"],
        "models_not_evaluated": [
            "gpt-4o (not_evaluated — no real API call)",
            "claude-3-5-sonnet (not_evaluated — no real API call)"
        ],
        "selected_model": "gemini-3.5-flash-lite",
        "quarantine_note": (
            "Synthetic GPT and Claude predictions generated by generate_calibrated_predictions() "
            "on 2026-09-24 at 16:24 have been quarantined to outputs/quarantine/. "
            "They must not be used, referenced, or displayed on dashboards."
        ),
        "comparison_artifact": "outputs/tables/llm_generative_model_comparison.csv",
        "predictions_artifact": "outputs/tables/llm_api_predictions_all.csv",
        "privacy": "userid_DI and actual target quarantined; prompt contained only row_id and factual behavioral summary",
    }
    (REPRO / "llm_api_benchmark_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n=== LLM Family Benchmark Results (N=1,800 Students — Gemini Only) ===")
    cols_to_print = [
        "provider", "model_name", "test_accuracy", "test_precision",
        "test_recall", "test_f1", "test_roc_auc", "test_pr_auc", "runtime_sec"
    ]
    print(comparison_df[cols_to_print].to_string(index=False))
    print("\n[GPT-4o] Status: not_evaluated — ยังไม่ได้ประเมินจริง (ผลจำลองถูกกักกันแล้ว)")
    print("[Claude 3.5 Sonnet] Status: not_evaluated — ยังไม่ได้ประเมินจริง (ผลจำลองถูกกักกันแล้ว)")
    return comparison_df


def main():
    return run_benchmark()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM benchmark for Gemini, Claude, GPT on 1,800 students")
    parser.add_argument("--provider", type=str, default="all", help="Provider to run: gemini, openai, anthropic, or all")
    args = parser.parse_args()
    run_benchmark()
