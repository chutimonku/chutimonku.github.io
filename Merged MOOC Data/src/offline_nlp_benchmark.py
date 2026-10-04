"""Offline Behavioral NLP Benchmark — No external API required.

Runs 6 classifiers on the student_behavior_text field from llm_student_text_inputs.csv:
  1. TF-IDF Unigram + Logistic Regression
  2. TF-IDF Bigram + Logistic Regression
  3. TF-IDF + Linear SVM
  4. Sentence Transformer + Logistic Regression
  5. DistilBERT Embeddings + Logistic Regression
  6. MiniLM Embeddings + Logistic Regression
  7. DistilGPT2 Embeddings + Logistic Regression (open-weight GPT-style decoder)

Rules:
- train/validation/test split is read from the existing llm_student_text_inputs.csv (split column)
- All preprocessing and classifier fitting ONLY on train split
- Threshold selection from validation set (maximises F1)
- No target, certified, grade, userid_DI in features or in text used for training
- Results are saved ONLY from real model runs; simulated/fabricated numbers are forbidden
- If any transformer model fails to load or run, it is recorded as Pending with the real error
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
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
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
REPRO = ROOT / "outputs" / "reproducibility"
DATA_DIR = ROOT / "data"
SEED = 42
CHECKPOINT_PATH = REPRO / "llm_offline_checkpoint.json"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """Load text inputs and outcomes; enforce strict leakage rules."""
    text_inputs = pd.read_csv(TABLES / "llm_student_text_inputs.csv")

    # Load ground-truth labels — stored separately in quarantine as required
    outcome_path = DATA_DIR / "quarantine" / "supervised_outcomes_cleaned.parquet"
    try:
        outcomes = (
            pd.read_parquet(outcome_path)
            .groupby("userid_DI", as_index=False)["certified"]
            .max()[["userid_DI", "certified"]]
        )
    except ImportError:
        # Portable fallback for environments without pyarrow. Read only the
        # quarantined outcome fields from the two immutable raw sources.
        raw_parts = []
        for raw_name in ["HXPC13_DI_v3_11-13-2019.csv", "big_student_clear_third_version.csv"]:
            raw = pd.read_csv(
                DATA_DIR / "raw" / raw_name,
                usecols=lambda c: c in {"userid_DI", "certified"},
                low_memory=False,
            )
            raw["certified"] = pd.to_numeric(raw["certified"], errors="coerce")
            raw_parts.append(raw.dropna(subset=["userid_DI", "certified"]))
        outcomes = (
            pd.concat(raw_parts, ignore_index=True)
            .groupby("userid_DI", as_index=False)["certified"]
            .max()[["userid_DI", "certified"]]
        )

    merged = text_inputs.merge(outcomes, on="userid_DI", how="left")
    merged["certified"] = merged["certified"].fillna(0).astype(int)

    # Split
    train_df = merged[merged["split"] == "train"].copy().reset_index(drop=True)
    val_df = merged[merged["split"] == "validation"].copy().reset_index(drop=True)
    test_df = merged[merged["split"] == "test"].copy().reset_index(drop=True)

    # Feature: ONLY student_behavior_text — no userid_DI, certified, grade, target in features
    X_train = train_df["student_behavior_text"].astype(str).values
    X_val = val_df["student_behavior_text"].astype(str).values
    X_test = test_df["student_behavior_text"].astype(str).values

    y_train = train_df["certified"].values
    y_val = val_df["certified"].values
    y_test = test_df["certified"].values

    # Store test userid_DI for predictions output (identifier only, not used as feature)
    test_df["actual_certified"] = y_test

    print(f"Train: {len(train_df)} rows, {y_train.sum()} positive")
    print(f"Val:   {len(val_df)} rows, {y_val.sum()} positive")
    print(f"Test:  {len(test_df)} rows, {y_test.sum()} positive")

    return train_df, val_df, test_df, X_train, X_val, X_test, y_train, y_val, y_test


def select_threshold(y_val: np.ndarray, proba_val: np.ndarray) -> float:
    """Select the threshold on the validation set that maximises F1 score."""
    best_thresh = 0.5
    best_f1 = 0.0
    for t in np.arange(0.05, 0.95, 0.01):
        preds = (proba_val >= t).astype(int)
        f1 = f1_score(y_val, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = float(t)
    return best_thresh


def compute_test_metrics(
    model_id: str,
    model_name: str,
    representation: str,
    y_test: np.ndarray,
    proba_test: np.ndarray,
    threshold: float,
    runtime_sec: float,
) -> dict:
    """Compute all required metrics from real model predictions."""
    pred = (proba_test >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
    return {
        "model_id": model_id,
        "model_name": model_name,
        "representation": representation,
        "runtime_sec": round(runtime_sec, 4),
        "threshold_from_validation": round(threshold, 4),
        "test_pr_auc": float(average_precision_score(y_test, proba_test)),
        "test_roc_auc": float(roc_auc_score(y_test, proba_test)),
        "test_brier": float(brier_score_loss(y_test, proba_test)),
        "test_accuracy": float(accuracy_score(y_test, pred)),
        "test_balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
        "test_precision": float(precision_score(y_test, pred, zero_division=0)),
        "test_recall": float(recall_score(y_test, pred, zero_division=0)),
        "test_f1": float(f1_score(y_test, pred, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "status": "completed",
        "error": "",
    }


def load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    return {}


def save_checkpoint(data: dict) -> None:
    CHECKPOINT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Model runners
# ---------------------------------------------------------------------------

def run_tfidf_logistic_unigram(X_train, X_val, X_test, y_train, y_val):
    """TF-IDF Unigram + Logistic Regression."""
    t0 = time.perf_counter()
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 1), max_features=10000, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, random_state=SEED, class_weight="balanced")),
    ])
    pipe.fit(X_train, y_train)
    proba_val = pipe.predict_proba(X_val)[:, 1]
    threshold = select_threshold(y_val, proba_val)
    proba_test = pipe.predict_proba(X_test)[:, 1]
    runtime = time.perf_counter() - t0
    return proba_test, threshold, runtime


def run_tfidf_logistic_bigram(X_train, X_val, X_test, y_train, y_val):
    """TF-IDF Bigram (1-2gram) + Logistic Regression."""
    t0 = time.perf_counter()
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=20000, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, random_state=SEED, class_weight="balanced")),
    ])
    pipe.fit(X_train, y_train)
    proba_val = pipe.predict_proba(X_val)[:, 1]
    threshold = select_threshold(y_val, proba_val)
    proba_test = pipe.predict_proba(X_test)[:, 1]
    runtime = time.perf_counter() - t0
    return proba_test, threshold, runtime


def run_tfidf_linear_svm(X_train, X_val, X_test, y_train, y_val):
    """TF-IDF + Linear SVM (calibrated for probabilities)."""
    t0 = time.perf_counter()
    base = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=20000, sublinear_tf=True)),
        ("svm", LinearSVC(max_iter=3000, random_state=SEED, class_weight="balanced")),
    ])
    # Calibrate to get probability estimates
    cal = CalibratedClassifierCV(base, cv=3)
    cal.fit(X_train, y_train)
    proba_val = cal.predict_proba(X_val)[:, 1]
    threshold = select_threshold(y_val, proba_val)
    proba_test = cal.predict_proba(X_test)[:, 1]
    runtime = time.perf_counter() - t0
    return proba_test, threshold, runtime


def run_sentence_transformer(X_train, X_val, X_test, y_train, y_val, model_name_hf: str):
    """Sentence Transformer embeddings + Logistic Regression."""
    from sentence_transformers import SentenceTransformer
    t0 = time.perf_counter()
    model = SentenceTransformer(model_name_hf)
    # Fit preprocessing only on train (embeddings are frozen — no train leakage from val/test)
    emb_train = model.encode(X_train.tolist(), batch_size=64, show_progress_bar=False, convert_to_numpy=True)
    emb_val = model.encode(X_val.tolist(), batch_size=64, show_progress_bar=False, convert_to_numpy=True)
    emb_test = model.encode(X_test.tolist(), batch_size=64, show_progress_bar=False, convert_to_numpy=True)

    clf = LogisticRegression(max_iter=1000, random_state=SEED, class_weight="balanced")
    clf.fit(emb_train, y_train)

    proba_val = clf.predict_proba(emb_val)[:, 1]
    threshold = select_threshold(y_val, proba_val)
    proba_test = clf.predict_proba(emb_test)[:, 1]
    runtime = time.perf_counter() - t0
    return proba_test, threshold, runtime


def run_distilbert_embeddings(X_train, X_val, X_test, y_train, y_val):
    """DistilBERT frozen CLS embedding + Logistic Regression."""
    import torch
    from transformers import AutoTokenizer, AutoModel

    t0 = time.perf_counter()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name_hf = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name_hf)
    model = AutoModel.from_pretrained(model_name_hf).to(device)
    model.eval()

    def encode_texts(texts, batch_size=32):
        all_emb = []
        for i in range(0, len(texts), batch_size):
            batch = list(texts[i: i + batch_size])
            enc = tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt").to(device)
            with torch.no_grad():
                out = model(**enc)
            cls_emb = out.last_hidden_state[:, 0, :].cpu().numpy()
            all_emb.append(cls_emb)
        return np.vstack(all_emb)

    emb_train = encode_texts(X_train)
    emb_val = encode_texts(X_val)
    emb_test = encode_texts(X_test)

    clf = LogisticRegression(max_iter=1000, random_state=SEED, class_weight="balanced")
    clf.fit(emb_train, y_train)

    proba_val = clf.predict_proba(emb_val)[:, 1]
    threshold = select_threshold(y_val, proba_val)
    proba_test = clf.predict_proba(emb_test)[:, 1]
    runtime = time.perf_counter() - t0
    return proba_test, threshold, runtime


def run_minilm_embeddings(X_train, X_val, X_test, y_train, y_val):
    """MiniLM embeddings (via sentence-transformers) + Logistic Regression."""
    return run_sentence_transformer(
        X_train, X_val, X_test, y_train, y_val,
        "sentence-transformers/all-MiniLM-L6-v2"
    )


def run_distilgpt2_embeddings(X_train, X_val, X_test, y_train, y_val):
    """DistilGPT2 frozen mean-pooled embeddings + Logistic Regression.

    DistilGPT2 is an open-weight GPT-style decoder model. It is not OpenAI GPT-4
    and is not presented as a substitute for a proprietary GPT/Claude API.
    """
    import torch
    from transformers import AutoTokenizer, AutoModel

    t0 = time.perf_counter()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name_hf = "distilgpt2"
    tokenizer = AutoTokenizer.from_pretrained(model_name_hf)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModel.from_pretrained(model_name_hf).to(device)
    model.eval()

    def encode_texts(texts, batch_size=24):
        pooled = []
        for i in range(0, len(texts), batch_size):
            batch = list(texts[i:i + batch_size])
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            ).to(device)
            with torch.no_grad():
                hidden = model(**enc).last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1).to(hidden.dtype)
            mean_pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            pooled.append(mean_pooled.cpu().numpy())
        return np.vstack(pooled)

    emb_train = encode_texts(X_train)
    emb_val = encode_texts(X_val)
    emb_test = encode_texts(X_test)
    clf = LogisticRegression(max_iter=1000, random_state=SEED, class_weight="balanced")
    clf.fit(emb_train, y_train)
    proba_val = clf.predict_proba(emb_val)[:, 1]
    threshold = select_threshold(y_val, proba_val)
    proba_test = clf.predict_proba(emb_test)[:, 1]
    runtime = time.perf_counter() - t0
    return proba_test, threshold, runtime


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

MODEL_SPECS = [
    {
        "model_id": "tfidf_unigram_logistic",
        "model_name": "TF-IDF Unigram + Logistic Regression",
        "representation": "lexical NLP baseline",
        "runner": run_tfidf_logistic_unigram,
        "needs_transformer": False,
    },
    {
        "model_id": "tfidf_bigram_logistic",
        "model_name": "TF-IDF (1-2 grams) + Logistic Regression",
        "representation": "lexical NLP baseline",
        "runner": run_tfidf_logistic_bigram,
        "needs_transformer": False,
    },
    {
        "model_id": "tfidf_linear_svm",
        "model_name": "TF-IDF + Linear SVM",
        "representation": "lexical NLP baseline",
        "runner": run_tfidf_linear_svm,
        "needs_transformer": False,
    },
    {
        "model_id": "sentence_transformer_logistic",
        "model_name": "Sentence Transformer + Logistic Regression",
        "representation": "frozen sentence transformer",
        "runner": lambda Xtr, Xv, Xte, ytr, yv: run_sentence_transformer(
            Xtr, Xv, Xte, ytr, yv,
            "sentence-transformers/all-mpnet-base-v2"
        ),
        "needs_transformer": True,
    },
    {
        "model_id": "distilbert_logistic",
        "model_name": "DistilBERT Embeddings + Logistic Regression",
        "representation": "frozen transformer encoder",
        "runner": run_distilbert_embeddings,
        "needs_transformer": True,
    },
    {
        "model_id": "minilm_logistic",
        "model_name": "MiniLM Embeddings + Logistic Regression",
        "representation": "frozen sentence transformer",
        "runner": run_minilm_embeddings,
        "needs_transformer": True,
    },
    {
        "model_id": "distilgpt2_logistic",
        "model_name": "DistilGPT2 Embeddings + Logistic Regression",
        "representation": "open-weight GPT-style frozen decoder",
        "runner": run_distilgpt2_embeddings,
        "needs_transformer": True,
    },
]


def main():
    print("=" * 70)
    print("Offline Behavioral NLP Benchmark — No External API")
    print("=" * 70)

    REPRO.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    # Load data
    train_df, val_df, test_df, X_train, X_val, X_test, y_train, y_val, y_test = load_data()

    # Load checkpoint (if any)
    checkpoint = load_checkpoint()
    print(f"Checkpoint: {list(checkpoint.keys())} models already done.\n")

    all_metrics = []
    all_cm = []
    all_preds_frames = []

    for spec in MODEL_SPECS:
        mid = spec["model_id"]
        mname = spec["model_name"]

        if mid in checkpoint and checkpoint[mid].get("status") == "completed":
            print(f"[SKIP — already done] {mname}")
            row = checkpoint[mid]
            all_metrics.append(row)
            cm_row = {
                "model_id": mid,
                "model_name": mname,
                "tn": row["tn"],
                "fp": row["fp"],
                "fn": row["fn"],
                "tp": row["tp"],
            }
            all_cm.append(cm_row)
            # Load predictions from saved file if available
            pred_path = TABLES / f"llm_offline_predictions_{mid}.csv"
            if pred_path.exists():
                all_preds_frames.append(pd.read_csv(pred_path))
            continue

        print(f"\n--- Running: {mname} ---")
        try:
            proba_test, threshold, runtime = spec["runner"](X_train, X_val, X_test, y_train, y_val)
            metrics = compute_test_metrics(
                mid, mname, spec["representation"],
                y_test, proba_test, threshold, runtime
            )
            print(f"  PR-AUC={metrics['test_pr_auc']:.4f}  ROC-AUC={metrics['test_roc_auc']:.4f}  "
                  f"F1={metrics['test_f1']:.4f}  Threshold={threshold:.4f}  Time={runtime:.2f}s")

            all_metrics.append(metrics)
            cm_row = {
                "model_id": mid,
                "model_name": mname,
                "tn": metrics["tn"],
                "fp": metrics["fp"],
                "fn": metrics["fn"],
                "tp": metrics["tp"],
            }
            all_cm.append(cm_row)

            # Per-student prediction frame
            pred_arr = (proba_test >= threshold).astype(int)
            preds_df = pd.DataFrame({
                "model_id": mid,
                "model_name": mname,
                "userid_DI": test_df["userid_DI"].values,
                "actual_certified": y_test,
                "predicted_certified": pred_arr,
                "predicted_probability": np.round(proba_test, 6),
            })
            preds_df.to_csv(TABLES / f"llm_offline_predictions_{mid}.csv", index=False)
            all_preds_frames.append(preds_df)

            checkpoint[mid] = metrics
            save_checkpoint(checkpoint)

        except Exception as exc:
            err_msg = traceback.format_exc()
            print(f"  [PENDING] {mname} failed: {exc}")
            row = {
                "model_id": mid,
                "model_name": mname,
                "representation": spec["representation"],
                "runtime_sec": None,
                "threshold_from_validation": None,
                "test_pr_auc": None,
                "test_roc_auc": None,
                "test_brier": None,
                "test_accuracy": None,
                "test_balanced_accuracy": None,
                "test_precision": None,
                "test_recall": None,
                "test_f1": None,
                "tn": None,
                "fp": None,
                "fn": None,
                "tp": None,
                "status": "pending",
                "error": str(exc),
            }
            all_metrics.append(row)
            checkpoint[mid] = row
            save_checkpoint(checkpoint)

    # ---------------------------------------------------------------------------
    # Save combined outputs
    # ---------------------------------------------------------------------------

    # 1. Comparison table
    comp_df = pd.DataFrame(all_metrics)
    # Mark best by PR-AUC among completed models
    completed = comp_df[comp_df["status"] == "completed"]
    comp_df["selected"] = False
    if len(completed) > 0:
        best_idx = completed["test_pr_auc"].astype(float).idxmax()
        comp_df.loc[best_idx, "selected"] = True
    comp_df.to_csv(TABLES / "llm_offline_model_comparison.csv", index=False)
    print("\n[SAVED] llm_offline_model_comparison.csv")

    # 2. Confusion matrices
    cm_df = pd.DataFrame(all_cm) if all_cm else pd.DataFrame(columns=["model_id", "model_name", "tn", "fp", "fn", "tp"])
    cm_df.to_csv(TABLES / "llm_offline_confusion_matrices.csv", index=False)
    print("[SAVED] llm_offline_confusion_matrices.csv")

    # 3. Combined predictions
    if all_preds_frames:
        all_preds = pd.concat(all_preds_frames, ignore_index=True)
        all_preds.to_csv(TABLES / "llm_offline_predictions.csv", index=False)
        print("[SAVED] llm_offline_predictions.csv")

    # 4. Manifest
    completed_models = [r["model_name"] for r in all_metrics if r["status"] == "completed"]
    pending_models = [
        {"model_name": r["model_name"], "error": r["error"]}
        for r in all_metrics if r["status"] == "pending"
    ]
    best_model_row = comp_df[comp_df["selected"] == True]
    best_name = best_model_row["model_name"].values[0] if len(best_model_row) > 0 else "N/A"
    best_prauc = float(best_model_row["test_pr_auc"].values[0]) if len(best_model_row) > 0 else None

    manifest = {
        "status": "completed" if len(pending_models) == 0 else "partial",
        "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
        "seed": SEED,
        "benchmark_type": "Offline Behavioral NLP — No External API",
        "text_field": "student_behavior_text",
        "leakage_controls": [
            "No target/certified/grade/userid_DI in features or text",
            "All preprocessing and classifiers fitted on train split only",
            "Threshold selected from validation set only",
            "Test labels loaded from quarantine — not used for fitting",
        ],
        "train_students": int(len(train_df)),
        "val_students": int(len(val_df)),
        "test_students": int(len(test_df)),
        "positive_test_students": int(y_test.sum()),
        "models_attempted": [s["model_name"] for s in MODEL_SPECS],
        "models_completed": completed_models,
        "models_pending": pending_models,
        "best_model": best_name,
        "best_pr_auc": best_prauc,
        "comparison_artifact": "outputs/tables/llm_offline_model_comparison.csv",
        "confusion_matrix_artifact": "outputs/tables/llm_offline_confusion_matrices.csv",
        "predictions_artifact": "outputs/tables/llm_offline_predictions.csv",
    }
    (REPRO / "llm_offline_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("[SAVED] llm_offline_manifest.json")

    # Summary
    print("\n" + "=" * 70)
    print("OFFLINE NLP BENCHMARK — FINAL RESULTS")
    print("=" * 70)
    display_cols = [
        "model_name", "test_pr_auc", "test_roc_auc", "test_f1",
        "test_accuracy", "test_brier", "threshold_from_validation", "status"
    ]
    print(comp_df[display_cols].to_string(index=False))
    print(f"\nBest model by PR-AUC: {best_name} (PR-AUC={best_prauc})")
    if pending_models:
        print(f"\nPending ({len(pending_models)}):")
        for p in pending_models:
            print(f"  - {p['model_name']}: {p['error'][:120]}")

    return comp_df


if __name__ == "__main__":
    main()
