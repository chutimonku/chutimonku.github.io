#!/usr/bin/env python3
"""Step 9: Package, validate, and lock the clustering deployment artifact.

The deployment pipeline accepts only the four approved behavioural features.
It rejects identifiers, profile fields, and outcome columns as model inputs.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


CONFIG_PATH = Path("config/project_config.json")

RAW_BEHAVIOR_PATH = Path("data/processed/behavior_features_unscaled.parquet")
PROFILES_PATH = Path("outputs/tables/cluster_profiles.csv")
VALIDATION_SUMMARY_PATH = Path(
    "outputs/tables/cluster_validation_summary.json"
)

FINAL_DIR = Path("models/final")
PIPELINE_PATH = FINAL_DIR / "clustering_pipeline.joblib"
MODEL_PATH = FINAL_DIR / "cluster_model.joblib"

INPUT_SCHEMA_PATH = FINAL_DIR / "input_schema.json"
MODEL_LOCK_PATH = FINAL_DIR / "model_lock.json"
DEPLOYMENT_CHECK_PATH = FINAL_DIR / "deployment_check.json"


def sha256_file(path: Path) -> str:
    """Compute SHA-256 for reproducible artifact locking."""
    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def validate_inference_input(
    frame: pd.DataFrame,
    behavior_features: list[str],
    outcome_columns: list[str],
    profile_columns: list[str]
) -> pd.DataFrame:
    """Validate a future student-level inference input.

    Expected input:
    - one row per learner
    - exactly the four behavioural percentile features
    - values must be numeric and within [0, 1] when present
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("Inference input must be a pandas DataFrame.")

    forbidden_columns = sorted(
        set(frame.columns).intersection(
            set(outcome_columns + profile_columns)
        )
    )

    # userid_DI is allowed only as an external join key and is removed before
    # calling the model. Other profile fields and all outcomes are forbidden.
    forbidden_columns = [
        column
        for column in forbidden_columns
        if column != "userid_DI"
    ]

    if forbidden_columns:
        raise ValueError(
            "Inference input contains forbidden profile/outcome columns: "
            + ", ".join(forbidden_columns)
        )

    missing_features = [
        column
        for column in behavior_features
        if column not in frame.columns
    ]

    if missing_features:
        raise ValueError(
            "Inference input is missing required behavioural features: "
            + ", ".join(missing_features)
        )

    unexpected_features = [
        column
        for column in frame.columns
        if column not in behavior_features + ["userid_DI"]
    ]

    if unexpected_features:
        raise ValueError(
            "Inference input contains unexpected columns: "
            + ", ".join(unexpected_features)
        )

    cleaned = frame[behavior_features].copy()

    for feature in behavior_features:
        cleaned[feature] = pd.to_numeric(
            cleaned[feature],
            errors="coerce"
        )

        invalid_range = (
            cleaned[feature].notna()
            & (
                cleaned[feature].lt(0)
                | cleaned[feature].gt(1)
            )
        )

        if invalid_range.any():
            raise ValueError(
                f"Feature '{feature}' contains values outside the allowed "
                "percentile range [0, 1]."
            )

    if len(cleaned) == 0:
        raise ValueError("Inference input must contain at least one row.")

    return cleaned


def main() -> None:
    required_paths = [
        CONFIG_PATH,
        RAW_BEHAVIOR_PATH,
        PROFILES_PATH,
        VALIDATION_SUMMARY_PATH,
        PIPELINE_PATH,
        MODEL_PATH
    ]

    for required_path in required_paths:
        if not required_path.exists():
            raise FileNotFoundError(
                f"Missing deployment prerequisite: {required_path}. "
                "Run Steps 5–8 first."
            )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    validation_summary = json.loads(
        VALIDATION_SUMMARY_PATH.read_text(encoding="utf-8")
    )

    behavior_features = config["behavior_features"]
    outcome_columns = config["outcome_columns"]
    profile_columns = config["profile_columns"]

    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("STEP 9: DEPLOYMENT PACKAGING AND INPUT SCHEMA VALIDATION")
    print("=" * 72)

    pipeline = joblib.load(PIPELINE_PATH)
    profiles = pd.read_csv(PROFILES_PATH)
    raw_behavior = pd.read_parquet(RAW_BEHAVIOR_PATH)

    if len(behavior_features) != 4:
        raise ValueError(
            "Deployment requires exactly four behavioural input features."
        )

    if "cluster" not in profiles.columns:
        raise ValueError(
            "cluster_profiles.csv must contain a cluster column."
        )

    sample_input = raw_behavior[
        ["userid_DI", *behavior_features]
    ].head(20).copy()

    validated_sample = validate_inference_input(
        frame=sample_input,
        behavior_features=behavior_features,
        outcome_columns=outcome_columns,
        profile_columns=profile_columns
    )

    predicted_clusters = pipeline.predict(validated_sample)

    known_clusters = set(profiles["cluster"].astype(int))
    unknown_predictions = sorted(
        set(pd.Series(predicted_clusters).astype(int)) - known_clusters
    )

    if unknown_predictions:
        raise RuntimeError(
            "Deployment pipeline produced unknown cluster values: "
            + ", ".join(map(str, unknown_predictions))
        )

    cluster_metadata = {
        str(int(row.cluster)): {
            "cluster_name": str(row.cluster_name),
            "relative_behavior_level": str(
                row.relative_behavior_level
            ),
            "student_count_at_training": int(row.student_count),
            "student_pct_at_training": float(row.student_pct)
        }
        for row in profiles.itertuples()
    }

    schema = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "scikit_learn_pipeline",
        "task_type": "unsupervised_clustering",
        "unit_of_analysis": "one row per userid_DI",
        "pipeline_path": str(PIPELINE_PATH),
        "input_contract": {
            "optional_identifier_column": "userid_DI",
            "required_feature_order": behavior_features,
            "required_feature_count": len(behavior_features),
            "feature_data_type": "numeric",
            "allowed_range": {
                feature: {
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "missing_allowed": True,
                    "missing_handling": (
                        "Median imputation stored in the locked preprocessing pipeline."
                    )
                }
                for feature in behavior_features
            }
        },
        "forbidden_input_columns": {
            "outcomes": outcome_columns,
            "profiles": [
                column
                for column in profile_columns
                if column != "userid_DI"
            ]
        },
        "output_contract": {
            "column": "cluster",
            "data_type": "integer",
            "known_cluster_values": sorted(
                int(value)
                for value in profiles["cluster"].unique()
            ),
            "cluster_metadata": cluster_metadata
        },
        "validation_policy": {
            "reject_missing_required_columns": True,
            "reject_unknown_columns": True,
            "reject_outcome_columns": True,
            "reject_profile_columns": True,
            "reject_non_numeric_values_that_cannot_be_coerced": False,
            "reject_values_outside_zero_to_one": True
        },
        "model_limitations": validation_summary["limitations"]
    }

    INPUT_SCHEMA_PATH.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    deployment_check = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_rows_validated": int(len(validated_sample)),
        "required_feature_order": behavior_features,
        "predicted_clusters_from_sample": [
            int(value)
            for value in predicted_clusters
        ],
        "known_clusters": sorted(
            int(value)
            for value in profiles["cluster"].unique()
        ),
        "unknown_predictions": unknown_predictions,
        "schema_validation_passed": len(unknown_predictions) == 0,
        "outcome_columns_allowed_as_input": False,
        "profile_columns_allowed_as_input": False
    }

    DEPLOYMENT_CHECK_PATH.write_text(
        json.dumps(deployment_check, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    model_lock = {
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": config["project"],
        "task_type": config["task_type"],
        "random_seed": config["random_seed"],
        "selected_k": int(
            validation_summary["final_cluster_metrics"]["cluster_count"]
        ),
        "behavior_features": behavior_features,
        "outcome_columns_excluded": outcome_columns,
        "profile_columns_excluded": profile_columns,
        "pipeline_file": str(PIPELINE_PATH),
        "pipeline_sha256": sha256_file(PIPELINE_PATH),
        "model_file": str(MODEL_PATH),
        "model_sha256": sha256_file(MODEL_PATH),
        "input_schema_file": str(INPUT_SCHEMA_PATH),
        "input_schema_sha256": sha256_file(INPUT_SCHEMA_PATH),
        "cluster_profile_file": str(PROFILES_PATH),
        "cluster_profile_sha256": sha256_file(PROFILES_PATH),
        "model_status": "locked_for_compatible_student_level_inputs_only",
        "retraining_required_when": [
            "New data has different behavioural feature definitions.",
            "New data contains different course-normalisation rules.",
            "Required behavioural features are unavailable.",
            "The source data schema or outcome definitions change."
        ]
    }

    MODEL_LOCK_PATH.write_text(
        json.dumps(model_lock, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[Step 9] Input schema: {INPUT_SCHEMA_PATH}")
    print(f"[Step 9] Deployment validation: {DEPLOYMENT_CHECK_PATH}")
    print(f"[Step 9] Model lock: {MODEL_LOCK_PATH}")
    print("[Step 9] Deployment input schema validation passed.")


if __name__ == "__main__":
    main()