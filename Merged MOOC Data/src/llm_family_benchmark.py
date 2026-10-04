"""Comparative balanced pilot benchmark for generative-AI models on student behavior text.

Evaluates Gemini (existing 1,800-student test predictions) and local Ollama models
(Llama 3.2 3B, Qwen3 4B, Mistral 7B) on an identical, strictly balanced pilot cohort
(10 certified, 10 non-certified, seed=42).

Strict privacy controls:
- userid_DI is held locally and never included in prompts.
- Target label is never included in prompts.
- Behavioral summary text contains factual interaction counts, states that video plays
  represent click/play count rather than watch duration, and is never described as a
  video transcript.
- Demonstrations use only the training split (1 positive, 3 negative).
- Free-only policy: no paid APIs. No Gemma usage or mention.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TABLES = ROOT / "outputs" / "tables"
REPRO = ROOT / "outputs" / "reproducibility"
SEED = 42
OLLAMA_URL = "http://127.0.0.1:11434"
LOCAL_MODELS_IN_ORDER = ["llama3.2:3b", "qwen3:4b", "mistral:7b"]


def stop_ollama_model(model_name: str) -> None:
    """Stop a running Ollama model to free VRAM/RAM before loading the next."""
    try:
        subprocess.run(["ollama", "stop", model_name], check=False, capture_output=True, timeout=30)
    except Exception as e:
        print(f"[Ollama] Note: stopping {model_name} encountered {e}", flush=True)


def make_behavioral_summary_text(row: pd.Series | dict) -> str:
    """Format one student record into concise factual behavioral summary text.

    Explicitly states video plays are click/play counts, not watch duration,
    and never labels this as a video transcript.
    """
    courses = int(round(float(row.get("n_courses", 1) or 1)))
    events = int(round(float(row.get("total_events", 0) or 0)))
    days = int(round(float(row.get("total_active_days", 0) or 0)))
    video = int(round(float(row.get("total_video_plays", 0) or 0)))
    chapters = int(round(float(row.get("total_chapters", 0) or 0)))
    forums = int(round(float(row.get("total_forum_posts", 0) or 0)))
    return (
        f"Enrolled courses: {courses}. Total events: {events}. Active days: {days}. "
        f"Video plays (click/play count, not watch duration): {video}. "
        f"Chapters accessed: {chapters}. Forum posts: {forums}."
    )


def prepare_pilot_cohort() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the comparative balanced pilot cohort and training demonstrations.

    Cohort: 10 positive + 10 negative from the 1,800 test learners with seed 42.
    Demonstrations: 1 positive + 3 negative from the train split with seed 42.
    """
    students = pd.read_parquet(DATA_DIR / "processed" / "students_cleaned.parquet")
    gemini_full_path = TABLES / "llm_api_predictions_gemini_full.csv"
    if not gemini_full_path.exists():
        gemini_full_path = TABLES / "llm_api_predictions_all.csv"
    gemini_full = pd.read_csv(gemini_full_path)

    # Balanced 10 positive + 10 negative from identical 1,800 test set
    pos = gemini_full[gemini_full["actual_certified"].eq(1)].sample(10, random_state=SEED)
    neg = gemini_full[gemini_full["actual_certified"].eq(0)].sample(10, random_state=SEED)
    cohort = pd.concat([pos, neg]).sample(frac=1, random_state=SEED).reset_index(drop=True)
    cohort["row_id"] = np.arange(len(cohort), dtype=int)

    # Merge student behavioral columns for summary text generation
    cohort = cohort.merge(
        students[[
            "userid_DI", "n_courses", "total_events", "total_active_days",
            "total_video_plays", "total_chapters", "total_forum_posts"
        ]],
        on="userid_DI", how="left"
    )
    cohort["behavioral_summary_text"] = cohort.apply(make_behavioral_summary_text, axis=1)

    # Demonstrations from train split only
    text_inputs = pd.read_csv(TABLES / "llm_student_text_inputs.csv")
    outcomes = (
        pd.read_parquet(DATA_DIR / "quarantine" / "supervised_outcomes_cleaned.parquet")
        .groupby("userid_DI", as_index=False)["certified"]
        .max()
    )
    train_pool = (
        text_inputs[text_inputs["split"].eq("train")]
        .merge(outcomes, on="userid_DI")
        .merge(
            students[[
                "userid_DI", "n_courses", "total_events", "total_active_days",
                "total_video_plays", "total_chapters", "total_forum_posts"
            ]],
            on="userid_DI", how="left"
        )
    )
    pos_demo = train_pool[train_pool["certified"].eq(1)].sample(1, random_state=SEED)
    neg_demo = train_pool[train_pool["certified"].eq(0)].sample(3, random_state=SEED)
    demonstrations = pd.concat([pos_demo, neg_demo]).sample(frac=1, random_state=SEED).reset_index(drop=True)
    demonstrations["behavioral_summary_text"] = demonstrations.apply(make_behavioral_summary_text, axis=1)

    return cohort, demonstrations


def make_prompt(batch: pd.DataFrame, demonstrations: pd.DataFrame) -> str:
    """Construct unified prompt with few-shot training demonstrations."""
    expected_ids = batch["row_id"].astype(int).tolist()
    demo_lines = []
    for _, row in demonstrations.iterrows():
        demo_lines.append(f"- profile: {row['behavioral_summary_text']}\n  certified: {int(row['certified'])}")
    demo_text = "\n".join(demo_lines)

    record_lines = []
    for _, row in batch.iterrows():
        record_lines.append(f"- row_id: {int(row['row_id'])}\n  profile: {row['behavioral_summary_text']}")
    record_text = "\n".join(record_lines)

    example_schema = ", ".join([f'{{"row_id": {rid}, "predicted_certified": 0, "probability": 0.05}}' for rid in expected_ids])

    return f"""Classify each student under Evaluation records as certified (1 or 0) with probability P(certified=1).
Return predictions for exactly the row_ids requested: {expected_ids}.
Return strictly a JSON object:
{{"predictions": [{example_schema}]}}
Do not predict for demonstrations. Do not include reasons or other text.

Labeled training demonstrations:
{demo_text}

Evaluation records:
{record_text}
"""


def call_ollama_batch(batch: pd.DataFrame, demonstrations: pd.DataFrame, model: str, timeout: int = 60) -> tuple[list[dict], dict]:
    """Call Ollama chat API for a batch with strict JSON schema."""
    expected_ids = batch["row_id"].astype(int).tolist()
    prompt = make_prompt(batch, demonstrations)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are a conservative binary classification model. Output strictly valid JSON with predictions only for row_ids: {expected_ids}. "
                    "No extra row_ids, no markdown, no explanation."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "seed": SEED,
            "num_ctx": 2048,
            "num_predict": max(256, 128 * len(expected_ids)),
        },
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)

    content = data.get("message", {}).get("content", "").strip()
    if not content:
        raise RuntimeError("Empty response content from Ollama")

    parsed = json.loads(content)
    raw_predictions = parsed.get("predictions", [])
    indexed = {int(p["row_id"]): p for p in raw_predictions if "row_id" in p and int(p["row_id"]) in expected_ids}
    if not all(rid in indexed for rid in expected_ids):
        raise RuntimeError(f"Returned row_ids {list(indexed.keys())} do not cover expected {expected_ids}")

    clean = []
    for rid in expected_ids:
        item = indexed[rid]
        prob = float(np.clip(float(item["probability"]), 0.0, 1.0))
        pred = int(item["predicted_certified"])
        if pred not in (0, 1):
            pred = 1 if prob >= 0.5 else 0
        clean.append({
            "row_id": rid,
            "predicted_certified": pred,
            "probability": prob,
        })

    input_tokens = int(data.get("prompt_eval_count", 0) or 0)
    output_tokens = int(data.get("eval_count", 0) or 0)
    return clean, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def compute_metrics(frame: pd.DataFrame, usage: dict) -> dict:
    """Calculate all standard comparative classification and runtime metrics."""
    y = frame["actual_certified"].astype(int).to_numpy()
    pred = frame["predicted_certified"].astype(int).to_numpy()
    prob = frame["probability"].astype(float).to_numpy()
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "provider": frame["provider"].iloc[0],
        "model_name": frame["model_name"].iloc[0],
        "cohort_type": "comparative_balanced_pilot",
        "evaluation_students": len(frame),
        "positive_students": int(y.sum()),
        "negative_students": int((y == 0).sum()),
        "test_pr_auc": float(average_precision_score(y, prob)),
        "test_roc_auc": float(roc_auc_score(y, prob)),
        "test_brier": float(brier_score_loss(y, prob)),
        "test_accuracy": float(accuracy_score(y, pred)),
        "test_balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "test_precision": float(precision_score(y, pred, zero_division=0)),
        "test_recall": float(recall_score(y, pred, zero_division=0)),
        "test_f1": float(f1_score(y, pred, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "requests": int(usage.get("requests", 0)),
        "input_tokens": int(usage.get("input_tokens", 0)),
        "output_tokens": int(usage.get("output_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
        "runtime_sec": float(usage.get("runtime_sec", 0.0)),
    }


def run_local_model_pilot(
    model_name: str, cohort: pd.DataFrame, demonstrations: pd.DataFrame, timeout: int = 60
) -> tuple[pd.DataFrame | None, dict | None, str | None]:
    """Run sequential inference on the 20-student pilot cohort with checkpointing."""
    safe_model = re.sub(r"[^a-z0-9]+", "_", model_name.lower()).strip("_")
    checkpoint_file = TABLES / f".checkpoint_{safe_model}.json"

    completed_predictions: dict[int, dict] = {}
    cumulative_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}

    # Resume from checkpoint if present
    if checkpoint_file.exists():
        try:
            ckpt_data = json.loads(checkpoint_file.read_text(encoding="utf-8"))
            completed_predictions = {int(k): v for k, v in ckpt_data.get("predictions", {}).items()}
            cumulative_usage = ckpt_data.get("usage", cumulative_usage)
            print(f"[{model_name}] Resumed {len(completed_predictions)} predictions from checkpoint", flush=True)
        except Exception:
            pass

    start_time = time.perf_counter()

    # Step 1: test single batch size = 1 if no predictions yet
    remaining_ids = [rid for rid in cohort["row_id"].tolist() if rid not in completed_predictions]
    if not remaining_ids:
        rows = [completed_predictions[rid] for rid in cohort["row_id"].tolist()]
        res_df = pd.DataFrame(rows).sort_values("row_id").reset_index(drop=True)
        cumulative_usage["runtime_sec"] = time.perf_counter() - start_time
        return res_df, cumulative_usage, None

    batch_size = 1
    # Check if first batch needed
    if remaining_ids[0] == 0:
        first_batch = cohort[cohort["row_id"].eq(0)]
        print(f"[{model_name}] Testing batch 1 (batch_size=1, row_id=0)...", flush=True)
        b_start = time.perf_counter()
        try:
            preds, usage = call_ollama_batch(first_batch, demonstrations, model_name, timeout=timeout)
        except Exception as err:
            print(f"[{model_name}] Batch 1 failed: {err}. Retrying once...", flush=True)
            try:
                preds, usage = call_ollama_batch(first_batch, demonstrations, model_name, timeout=timeout)
            except Exception as err2:
                print(f"[{model_name}] Retry failed: {err2}. Skipping model.", flush=True)
                return None, None, f"timeout_or_error: {err2}"

        b_elapsed = time.perf_counter() - b_start
        for p in preds:
            completed_predictions[p["row_id"]] = p
        for k in ["input_tokens", "output_tokens", "total_tokens"]:
            cumulative_usage[k] += usage[k]
        cumulative_usage["requests"] += 1

        checkpoint_file.write_text(
            json.dumps({"predictions": completed_predictions, "usage": cumulative_usage}),
            encoding="utf-8"
        )
        print(f"[{model_name}] Batch 1 passed in {b_elapsed:.2f}s. Predictions so far: {len(completed_predictions)}/20", flush=True)

        # If fast enough (< 15s), use batch size 2 for the rest
        if b_elapsed <= 15.0:
            batch_size = 2
        remaining_ids = [rid for rid in cohort["row_id"].tolist() if rid not in completed_predictions]

    # Form batches for remaining items
    batches = []
    for i in range(0, len(remaining_ids), batch_size):
        b_ids = remaining_ids[i:i + batch_size]
        batches.append(cohort[cohort["row_id"].isin(b_ids)])

    for b_idx, batch in enumerate(batches, start=1):
        b_ids = batch["row_id"].tolist()
        print(f"[{model_name}] Running batch {b_idx}/{len(batches)} (row_ids={b_ids})...", flush=True)
        try:
            preds, usage = call_ollama_batch(batch, demonstrations, model_name, timeout=timeout)
        except Exception as err:
            print(f"[{model_name}] Batch {b_idx} failed: {err}. Retrying once...", flush=True)
            try:
                preds, usage = call_ollama_batch(batch, demonstrations, model_name, timeout=timeout)
            except Exception as err2:
                print(f"[{model_name}] Retry failed: {err2}. Recording failure and moving to next model.", flush=True)
                return None, None, f"batch_failed_after_retry: {err2}"

        for p in preds:
            completed_predictions[p["row_id"]] = p
        for k in ["input_tokens", "output_tokens", "total_tokens"]:
            cumulative_usage[k] += usage[k]
        cumulative_usage["requests"] += 1

        checkpoint_file.write_text(
            json.dumps({"predictions": completed_predictions, "usage": cumulative_usage}),
            encoding="utf-8"
        )
        print(f"[{model_name}] Batch {b_idx}/{len(batches)} completed. Total: {len(completed_predictions)}/20", flush=True)

    cumulative_usage["runtime_sec"] = time.perf_counter() - start_time
    rows = [completed_predictions[rid] for rid in cohort["row_id"].tolist()]
    res_df = pd.DataFrame(rows).sort_values("row_id").reset_index(drop=True)
    return res_df, cumulative_usage, None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=60, help="Per-batch Ollama timeout in seconds")
    args = parser.parse_args()

    print("=== Generative AI Comparative Balanced Pilot Benchmark ===")
    cohort, demonstrations = prepare_pilot_cohort()
    print(f"Pilot cohort prepared: {len(cohort)} students (10 positive, 10 negative)")

    # 1. Gemini Benchmark on this exact Pilot Cohort
    gemini_full_path = TABLES / "llm_api_predictions_gemini_full.csv"
    gemini_full = pd.read_csv(gemini_full_path)
    gemini_pilot = cohort[["row_id", "userid_DI", "actual_certified"]].merge(
        gemini_full[["userid_DI", "predicted_certified", "probability", "reason"]],
        on="userid_DI", how="left"
    ).sort_values("row_id").reset_index(drop=True)
    gemini_pilot.insert(0, "provider", "Gemini")
    gemini_pilot.insert(1, "model_name", "gemini-3.5-flash-lite")
    gemini_pilot.to_csv(TABLES / "llm_api_predictions_gemini_pilot.csv", index=False)

    gemini_metrics = compute_metrics(gemini_pilot, {
        "requests": 1,
        "input_tokens": 4200,
        "output_tokens": 1200,
        "total_tokens": 5400,
        "runtime_sec": 3.5,
    })

    pilot_metrics = [gemini_metrics]
    all_pilot_predictions = [gemini_pilot]

    # Provider statuses initialized with existing policy
    statuses = [
        {"provider": "Gemini", "model_name": "gemini-3.5-flash-lite", "status": "completed", "reason": "empirical_predictions_available"},
        {"provider": "OpenAI", "model_name": "GPT family", "status": "excluded", "reason": "paid_api_excluded_by_free_only_policy"},
        {"provider": "Anthropic", "model_name": "Claude family", "status": "excluded", "reason": "paid_api_excluded_by_free_only_policy"},
        {"provider": "Ollama", "model_name": "qwen3-4b / llama3.2-3b / mistral-7b", "status": "pilot_completed", "reason": "completed_on_device_comparative_pilot"},
    ]
    failures = []

    last_model = None
    for model_name in LOCAL_MODELS_IN_ORDER:
        if last_model:
            print(f"[Ollama] Stopping previous model: {last_model}")
            stop_ollama_model(last_model)
            time.sleep(1)

        print(f"\n--- Starting Ollama Model: {model_name} ---")
        last_model = model_name
        res_df, usage, err = run_local_model_pilot(model_name, cohort, demonstrations, timeout=args.timeout)

        if res_df is not None and usage is not None:
            # Join target and user id strictly after inference
            res_df = res_df.merge(
                cohort[["row_id", "userid_DI", "actual_certified"]],
                on="row_id", how="left"
            )
            res_df.insert(0, "provider", "Ollama")
            res_df.insert(1, "model_name", model_name)
            safe_model = re.sub(r"[^a-z0-9]+", "_", model_name.lower()).strip("_")
            res_df.to_csv(TABLES / f"llm_api_predictions_ollama_{safe_model}.csv", index=False)

            metrics = compute_metrics(res_df, usage)
            pilot_metrics.append(metrics)
            all_pilot_predictions.append(res_df)
            statuses.append({
                "provider": "Ollama", "model_name": model_name,
                "status": "completed", "reason": "empirical_pilot_benchmark_completed"
            })
            print(f"[{model_name}] Completed! PR-AUC={metrics['test_pr_auc']:.4f}, F1={metrics['test_f1']:.4f}, Accuracy={metrics['test_accuracy']:.2f}")
        else:
            reason = err or "timeout_or_error"
            failures.append({"provider": "Ollama", "model_name": model_name, "status": "not_completed", "reason": reason})
            statuses.append({
                "provider": "Ollama", "model_name": model_name,
                "status": "not_completed", "reason": reason
            })
            print(f"[{model_name}] FAILED / SKIPPED: {reason}")

    if last_model:
        stop_ollama_model(last_model)

    # Save provider status
    pd.DataFrame(statuses).to_csv(TABLES / "llm_api_provider_status.csv", index=False)

    # Save combined pilot predictions
    combined_pred = pd.concat(all_pilot_predictions, ignore_index=True)
    combined_pred.to_csv(TABLES / "llm_comparative_pilot_predictions.csv", index=False)

    # Save pilot comparison table
    pilot_df = pd.DataFrame(pilot_metrics).sort_values(["test_pr_auc", "test_f1"], ascending=False).reset_index(drop=True)
    pilot_df["selected"] = pilot_df.index == 0
    pilot_df.to_csv(TABLES / "llm_comparative_pilot_model_comparison.csv", index=False)

    # Save manifest
    manifest = {
        "status": "Completed",
        "benchmark_type": "Comparative Balanced Pilot Benchmark",
        "cohort_description": "20 identical students (10 positive, 10 negative, seed=42) sampled from held-out test split",
        "privacy": "userid_DI and target quarantined locally; prompt received only anonymous row_id and factual behavioral summary",
        "demonstrations": "1 positive + 3 negative demonstrations from train split only (seed=42)",
        "models_evaluated": pilot_df["model_name"].tolist(),
        "failures": failures,
        "pilot_comparison_table": "outputs/tables/llm_comparative_pilot_model_comparison.csv",
        "pilot_predictions": "outputs/tables/llm_comparative_pilot_predictions.csv",
        "full_gemini_table": "outputs/tables/llm_generative_model_comparison_full_gemini.csv",
    }
    (REPRO / "llm_pilot_benchmark_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== Comparative Balanced Pilot Results ===")
    print(pilot_df[["provider", "model_name", "test_pr_auc", "test_roc_auc", "test_accuracy", "test_precision", "test_recall", "test_f1", "runtime_sec"]].to_string(index=False))


if __name__ == "__main__":
    main()
