"""Step 9: package and verify the active analysis-track models."""

from __future__ import annotations

import json
import os
import time

import joblib
import numpy as np
import pandas as pd


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models", "tracks")
REPRO = os.path.join(ROOT, "outputs", "reproducibility")
TABLES = os.path.join(ROOT, "outputs", "tables")
EXAMPLES = os.path.join(ROOT, "examples")
STUDENTS = os.path.join(ROOT, "data", "processed", "students_cleaned.parquet")


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def run_track_deployment():
    """Validate saved pipelines on clean student rows and publish contracts."""
    os.makedirs(EXAMPLES, exist_ok=True)
    students = pd.read_parquet(STUDENTS)
    unsup = joblib.load(os.path.join(MODELS, "unsupervised_pipeline.joblib"))
    supervised = joblib.load(os.path.join(MODELS, "supervised_certification_pipeline.joblib"))
    deep_classifier = joblib.load(os.path.join(MODELS, "deep_certification_pipeline.joblib"))
    with open(os.path.join(REPRO, "supervised_track_manifest.json"), encoding="utf-8") as handle:
        sup_manifest = json.load(handle)
    with open(os.path.join(REPRO, "deep_learning_track_manifest.json"), encoding="utf-8") as handle:
        deep_manifest = json.load(handle)
    unsupervised_features = list(unsup["features"])
    supervised_inputs = list(sup_manifest["source_features"])

    sample = students.iloc[: min(5000, len(students))].copy()
    runtimes = []

    start = time.perf_counter()
    X_unsup = unsup["preprocessor"].transform(sample[unsupervised_features])
    unsup_labels = unsup["model"].predict(X_unsup)
    elapsed = time.perf_counter() - start
    runtimes.append({"track": "Traditional Unsupervised", "rows": len(sample), "runtime_sec": elapsed,
                     "rows_per_second": len(sample) / elapsed})

    start = time.perf_counter()
    deep_probabilities = deep_classifier.predict_proba(sample[supervised_inputs])[:, 1]
    elapsed = time.perf_counter() - start
    deep_threshold = float(deep_manifest["selected_threshold"])
    runtimes.append({"track": "Deep Learning", "rows": len(sample), "runtime_sec": elapsed,
                     "rows_per_second": len(sample) / elapsed})

    start = time.perf_counter()
    probabilities = supervised.predict_proba(sample[supervised_inputs])[:, 1]
    elapsed = time.perf_counter() - start
    threshold = float(sup_manifest["selected_threshold"])
    runtimes.append({"track": "Supervised Learning", "rows": len(sample), "runtime_sec": elapsed,
                     "rows_per_second": len(sample) / elapsed})
    pd.DataFrame(runtimes).to_csv(os.path.join(TABLES, "deployment_runtime.csv"), index=False)

    input_example = sample[["userid_DI"] + sorted(set(unsupervised_features + supervised_inputs))].head(10)
    input_example.to_csv(os.path.join(EXAMPLES, "track_student_input.csv"), index=False)
    pd.DataFrame({
        "userid_DI": sample["userid_DI"].head(10),
        "unsupervised_cluster": np.asarray(unsup_labels)[:10],
        "deep_certification_probability": deep_probabilities[:10],
        "deep_certification_prediction": (deep_probabilities[:10] >= deep_threshold).astype(int),
        "certification_probability": probabilities[:10],
        "certification_prediction": (probabilities[:10] >= threshold).astype(int),
    }).to_csv(os.path.join(EXAMPLES, "track_model_output.csv"), index=False)

    contract = {
        "unit_of_analysis": "one row per student (userid_DI must be unique)",
        "outcome_policy": "Outcome columns are prohibited from unsupervised inputs; supervised and deep classification use certified only as a governed target.",
        "traditional_unsupervised": {
            "artifact": "models/tracks/unsupervised_pipeline.joblib",
            "required_features": unsupervised_features,
            "output": "cluster label",
        },
        "deep_learning": {
            "artifact": "models/tracks/deep_certification_pipeline.joblib",
            "required_features": supervised_inputs,
            "threshold": deep_threshold,
            "output": "certification probability and binary prediction from neural-network classifier",
        },
        "supervised_learning": {
            "artifact": "models/tracks/supervised_certification_pipeline.joblib",
            "required_features": supervised_inputs,
            "threshold": threshold,
            "output": "certification probability and binary prediction",
        },
        "generative_llm": {
            "artifact": "outputs/tables/llm_video_text_inputs.csv",
            "required_inputs": [
                "cleaned student-level video columns",
                "structured text generated from video columns",
            ],
            "output": "LLM/NLP-ready text from video behavior columns plus method availability/results",
        },
    }
    _write_json(os.path.join(MODELS, "input_contract.json"), contract)

    cards = [
        "# Active model cards",
        "",
        "## Traditional Unsupervised",
        f"Uses {len(unsupervised_features)} behavioral features selected from the reconciled clean data and returns a student cluster. Outcomes are excluded.",
        "",
        "## Deep Learning",
        f"Uses a neural-network classifier on {len(supervised_inputs)} governed pre-outcome inputs to predict certification probability. This is classification, not clustering.",
        "",
        "## Supervised Learning",
        f"Predicts certification probability from {len(supervised_inputs)} data-selected governed inputs. The saved decision threshold is {threshold:.6f}.",
        "",
        "## Generative LLM",
        "Converts cleaned video behavior columns into structured text before LLM/NLP representation. This is not raw spoken-video transcription; it is a text representation of the available video columns.",
        "",
        "Runtime values are machine-dependent and are recorded in `outputs/tables/deployment_runtime.csv`.",
    ]
    with open(os.path.join(MODELS, "model_cards.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(cards) + "\n")
    print("[+] Step 9 track deployment packages and runtime checks completed.")


if __name__ == "__main__":
    run_track_deployment()
