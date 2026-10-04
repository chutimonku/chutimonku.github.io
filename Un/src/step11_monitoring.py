#!/usr/bin/env python3
"""Step 11: Create monitoring baselines and evaluate compatible new cohorts.

Baseline:
- Four behavioural features before scaling
- Cluster-size distribution from the locked model

Optional current cohort input:
monitoring/current_cohort_behavior_features.csv

The current cohort file may contain:
- userid_DI (optional)
- mean_course_events_percentile
- mean_course_active_days_percentile
- mean_course_chapters_percentile
- mean_course_forum_posts_percentile

It must not contain outcomes or profile columns.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


CONFIG_PATH = Path("config/project_config.json")

RAW_BEHAVIOR_PATH = Path("data/processed/behavior_features_unscaled.parquet")
ASSIGNMENTS_PATH = Path("outputs/data/cluster_assignments.csv")
INPUT_SCHEMA_PATH = Path("models/final/input_schema.json")
PIPELINE_PATH = Path("models/final/clustering_pipeline.joblib")

MONITORING_DIR = Path("monitoring")
CURRENT_COHORT_PATH = (
    MONITORING_DIR / "current_cohort_behavior_features.csv"
)

FEATURE_BASELINE_PATH = MONITORING_DIR / "feature_distribution_baseline.json"
CLUSTER_BASELINE_PATH = MONITORING_DIR / "cluster_distribution_baseline.csv"
MONITORING_CONFIG_PATH = MONITORING_DIR / "monitoring_config.json"
MONITORING_REPORT_PATH = MONITORING_DIR / "monitoring_report.json"
RETRAINING_DECISION_PATH = MONITORING_DIR / "retraining_decision.json"
MONITORING_HISTORY_PATH = MONITORING_DIR / "monitoring_history.csv"


def safe_proportions(values: np.ndarray) -> np.ndarray:
    """Return smoothed proportions so PSI never divides by zero."""
    values = np.asarray(values, dtype=float)
    values = values + 1e-6
    return values / values.sum()


def population_stability_index(
    expected_pct: np.ndarray,
    actual_pct: np.ndarray
) -> float:
    """Calculate PSI from expected and actual bin percentages."""
    expected = safe_proportions(expected_pct)
    actual = safe_proportions(actual_pct)

    return float(np.sum(
        (actual - expected) * np.log(actual / expected)
    ))


def create_feature_baseline(
    frame: pd.DataFrame,
    behavior_features: list[str]
) -> dict:
    """Create fixed monitoring bins and expected proportions."""
    baseline: dict[str, dict] = {}

    for feature in behavior_features:
        values = pd.to_numeric(
            frame[feature],
            errors="coerce"
        ).dropna()

        if values.empty:
            raise ValueError(
                f"Cannot create monitoring baseline: {feature} is all missing."
            )

        # Quantile bins make each baseline band comparable in population size.
        quantile_edges = np.quantile(
            values,
            np.linspace(0, 1, 11)
        )

        # Repeated values can create duplicate edges. Use unique edges and,
        # if needed, fall back to one broad bin.
        bin_edges = np.unique(quantile_edges)

        if len(bin_edges) < 2:
            minimum = float(values.min())
            maximum = float(values.max())

            if minimum == maximum:
                maximum = minimum + 1e-6

            bin_edges = np.array([minimum, maximum])

        bin_edges[0] = min(float(bin_edges[0]), 0.0)
        bin_edges[-1] = max(float(bin_edges[-1]), 1.0)

        counts, _ = np.histogram(values, bins=bin_edges)

        baseline[feature] = {
            "bin_edges": [float(value) for value in bin_edges],
            "expected_counts": [int(value) for value in counts],
            "expected_proportions": [
                float(value)
                for value in safe_proportions(counts)
            ],
            "baseline_non_missing_count": int(len(values)),
            "baseline_missing_count": int(frame[feature].isna().sum()),
            "baseline_min": float(values.min()),
            "baseline_median": float(values.median()),
            "baseline_max": float(values.max())
        }

    return baseline


def validate_current_input(
    frame: pd.DataFrame,
    behavior_features: list[str],
    outcome_columns: list[str],
    profile_columns: list[str]
) -> pd.DataFrame:
    """Validate current-cohort data against the locked deployment contract."""
    missing_features = [
        feature
        for feature in behavior_features
        if feature not in frame.columns
    ]

    if missing_features:
        raise ValueError(
            "Current cohort is missing required features: "
            + ", ".join(missing_features)
        )

    forbidden = sorted(
        set(frame.columns).intersection(
            set(outcome_columns + profile_columns)
        )
    )

    forbidden = [
        column
        for column in forbidden
        if column != "userid_DI"
    ]

    if forbidden:
        raise ValueError(
            "Current cohort contains forbidden outcome/profile columns: "
            + ", ".join(forbidden)
        )

    allowed = set(behavior_features + ["userid_DI"])
    unexpected = [
        column
        for column in frame.columns
        if column not in allowed
    ]

    if unexpected:
        raise ValueError(
            "Current cohort contains unexpected columns: "
            + ", ".join(unexpected)
        )

    validated = frame[behavior_features].copy()

    for feature in behavior_features:
        validated[feature] = pd.to_numeric(
            validated[feature],
            errors="coerce"
        )

        invalid_range = (
            validated[feature].notna()
            & (
                validated[feature].lt(0)
                | validated[feature].gt(1)
            )
        )

        if invalid_range.any():
            raise ValueError(
                f"Current cohort feature '{feature}' contains values outside [0, 1]."
            )

    if validated.empty:
        raise ValueError("Current cohort file contains zero rows.")

    return validated


def drift_status(max_psi: float) -> tuple[str, bool]:
    """Return human-readable monitoring status and retraining trigger."""
    if max_psi < 0.10:
        return "normal", False

    if max_psi < 0.25:
        return "warning", False

    return "action_required", True


def main() -> None:
    required_paths = [
        CONFIG_PATH,
        RAW_BEHAVIOR_PATH,
        ASSIGNMENTS_PATH,
        INPUT_SCHEMA_PATH,
        PIPELINE_PATH
    ]

    for required_path in required_paths:
        if not required_path.exists():
            raise FileNotFoundError(
                f"Missing monitoring prerequisite: {required_path}. "
                "Run Steps 5–9 first."
            )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    input_schema = json.loads(
        INPUT_SCHEMA_PATH.read_text(encoding="utf-8")
    )

    behavior_features = config["behavior_features"]
    outcome_columns = config["outcome_columns"]
    profile_columns = config["profile_columns"]

    MONITORING_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("STEP 11: MONITORING BASELINE AND NEW-COHORT DRIFT CHECK")
    print("=" * 72)

    baseline_behavior = pd.read_parquet(RAW_BEHAVIOR_PATH)
    assignments = pd.read_csv(ASSIGNMENTS_PATH)

    if baseline_behavior["userid_DI"].duplicated().any():
        raise ValueError(
            "Baseline behavioural table contains duplicate userid_DI."
        )

    if assignments["userid_DI"].duplicated().any():
        raise ValueError(
            "Cluster assignment table contains duplicate userid_DI."
        )

    baseline = create_feature_baseline(
        frame=baseline_behavior,
        behavior_features=behavior_features
    )

    FEATURE_BASELINE_PATH.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "unit_of_analysis": "one row per userid_DI",
                "behavior_features": behavior_features,
                "feature_baselines": baseline
            },
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    cluster_baseline = (
        assignments["cluster"]
        .value_counts()
        .sort_index()
        .rename_axis("cluster")
        .reset_index(name="student_count")
    )

    cluster_baseline["student_pct"] = (
        cluster_baseline["student_count"]
        / cluster_baseline["student_count"].sum()
        * 100
    )

    cluster_baseline.to_csv(
        CLUSTER_BASELINE_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    monitoring_config = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_feature_file": str(FEATURE_BASELINE_PATH),
        "baseline_cluster_file": str(CLUSTER_BASELINE_PATH),
        "current_cohort_input_path": str(CURRENT_COHORT_PATH),
        "input_contract": input_schema["input_contract"],
        "psi_thresholds": {
            "normal": "PSI < 0.10",
            "warning": "0.10 <= PSI < 0.25",
            "action_required": "PSI >= 0.25"
        },
        "retraining_rule": (
            "Retraining review is required when any behavioural feature "
            "has PSI >= 0.25 or when cluster-distribution PSI >= 0.25."
        ),
        "outcomes_allowed_for_monitoring_input": False,
        "profile_columns_allowed_for_monitoring_input": False
    }

    MONITORING_CONFIG_PATH.write_text(
        json.dumps(monitoring_config, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    if not CURRENT_COHORT_PATH.exists():
        report = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "not_evaluated",
            "reason": (
                "No current cohort file was supplied. "
                "Baseline artifacts were created successfully."
            ),
            "baseline_student_count": int(len(baseline_behavior)),
            "current_cohort_input_path": str(CURRENT_COHORT_PATH),
            "feature_baseline_path": str(FEATURE_BASELINE_PATH),
            "cluster_baseline_path": str(CLUSTER_BASELINE_PATH)
        }

        decision = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "not_evaluated",
            "retraining_triggered": False,
            "reason": (
                "No compatible current cohort data is available for drift evaluation."
            )
        }

        MONITORING_REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        RETRAINING_DECISION_PATH.write_text(
            json.dumps(decision, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print("[Step 11] Baselines created.")
        print("[Step 11] Current cohort not supplied.")
        print("[Step 11] Monitoring status: not_evaluated.")
        return

    current_raw = pd.read_csv(CURRENT_COHORT_PATH)

    current_features = validate_current_input(
        frame=current_raw,
        behavior_features=behavior_features,
        outcome_columns=outcome_columns,
        profile_columns=profile_columns
    )

    pipeline = joblib.load(PIPELINE_PATH)
    current_clusters = pipeline.predict(current_features)

    feature_rows = []

    for feature in behavior_features:
        feature_baseline = baseline[feature]
        bin_edges = np.asarray(
            feature_baseline["bin_edges"],
            dtype=float
        )

        current_values = pd.to_numeric(
            current_features[feature],
            errors="coerce"
        ).dropna()

        actual_counts, _ = np.histogram(
            current_values,
            bins=bin_edges
        )

        expected_proportions = np.asarray(
            feature_baseline["expected_proportions"],
            dtype=float
        )

        actual_proportions = safe_proportions(actual_counts)

        psi = population_stability_index(
            expected_pct=expected_proportions,
            actual_pct=actual_proportions
        )

        feature_rows.append({
            "feature": feature,
            "baseline_non_missing_count": int(
                feature_baseline["baseline_non_missing_count"]
            ),
            "current_non_missing_count": int(len(current_values)),
            "baseline_missing_count": int(
                feature_baseline["baseline_missing_count"]
            ),
            "current_missing_count": int(
                current_features[feature].isna().sum()
            ),
            "psi": float(psi)
        })

    feature_drift = pd.DataFrame(feature_rows)

    baseline_cluster_proportions = (
        cluster_baseline
        .set_index("cluster")["student_count"]
    )

    current_cluster_counts = (
        pd.Series(current_clusters)
        .value_counts()
        .sort_index()
    )

    all_clusters = sorted(
        set(baseline_cluster_proportions.index)
        .union(set(current_cluster_counts.index))
    )

    expected_cluster_counts = np.array([
        baseline_cluster_proportions.get(cluster, 0)
        for cluster in all_clusters
    ])

    actual_cluster_counts = np.array([
        current_cluster_counts.get(cluster, 0)
        for cluster in all_clusters
    ])

    cluster_psi = population_stability_index(
        expected_pct=expected_cluster_counts,
        actual_pct=actual_cluster_counts
    )

    max_feature_psi = float(feature_drift["psi"].max())
    max_psi = max(max_feature_psi, cluster_psi)

    status, retraining_triggered = drift_status(max_psi)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "baseline_student_count": int(len(baseline_behavior)),
        "current_student_count": int(len(current_features)),
        "feature_psi": feature_drift.to_dict(orient="records"),
        "cluster_distribution_psi": float(cluster_psi),
        "maximum_feature_psi": max_feature_psi,
        "maximum_observed_psi": float(max_psi),
        "thresholds": monitoring_config["psi_thresholds"],
        "retraining_triggered": retraining_triggered,
        "input_schema_validated": True,
        "outcomes_used_in_monitoring_input": False
    }

    decision = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "retraining_triggered": retraining_triggered,
        "decision": (
            "Review and retrain the model."
            if retraining_triggered
            else "No retraining trigger from PSI thresholds."
        ),
        "maximum_observed_psi": float(max_psi),
        "cluster_distribution_psi": float(cluster_psi)
    }

    MONITORING_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    RETRAINING_DECISION_PATH.write_text(
        json.dumps(decision, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    history_row = pd.DataFrame(
        [{
            "evaluated_at_utc": report["generated_at_utc"],
            "status": status,
            "baseline_student_count": report["baseline_student_count"],
            "current_student_count": report["current_student_count"],
            "maximum_feature_psi": max_feature_psi,
            "cluster_distribution_psi": float(cluster_psi),
            "maximum_observed_psi": float(max_psi),
            "retraining_triggered": retraining_triggered
        }]
    )

    if MONITORING_HISTORY_PATH.exists():
        history = pd.read_csv(MONITORING_HISTORY_PATH)
        history = pd.concat(
            [history, history_row],
            ignore_index=True
        )
    else:
        history = history_row

    history.to_csv(
        MONITORING_HISTORY_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"[Step 11] Monitoring report: {MONITORING_REPORT_PATH}")
    print(f"[Step 11] Retraining decision: {RETRAINING_DECISION_PATH}")
    print(f"[Step 11] Monitoring status: {status}")
    print(f"[Step 11] Maximum observed PSI: {max_psi:.4f}")


if __name__ == "__main__":
    main()
