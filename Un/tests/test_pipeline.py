"""Validation tests for the MOOC unsupervised clustering workflow."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

CONFIG_PATH = ROOT_DIR / "config/project_config.json"
RAW_DATA_PATH = (
    ROOT_DIR / "data/raw/big_student_clear_third_version.csv"
)

STUDENTS_PATH = (
    ROOT_DIR / "data/processed/students_cleaned.parquet"
)
FEATURE_MATRIX_PATH = (
    ROOT_DIR / "data/processed/feature_matrix.parquet"
)
RAW_BEHAVIOR_PATH = (
    ROOT_DIR / "data/processed/behavior_features_unscaled.parquet"
)

K_METRICS_PATH = (
    ROOT_DIR / "outputs/tables/k_selection_metrics.csv"
)
ASSIGNMENTS_PATH = (
    ROOT_DIR / "outputs/data/cluster_assignments.csv"
)
PROFILES_PATH = (
    ROOT_DIR / "outputs/tables/cluster_profiles.csv"
)
GRADE_AUDIT_PATH = (
    ROOT_DIR / "outputs/tables/grade_outcome_audit.csv"
)

PIPELINE_PATH = (
    ROOT_DIR / "models/final/clustering_pipeline.joblib"
)
INPUT_SCHEMA_PATH = (
    ROOT_DIR / "models/final/input_schema.json"
)
MODEL_LOCK_PATH = (
    ROOT_DIR / "models/final/model_lock.json"
)
REPORT_PATH = (
    ROOT_DIR / "reports/student_segmentation_report.html"
)
MONITORING_REPORT_PATH = (
    ROOT_DIR / "monitoring/monitoring_report.json"
)


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_config_has_exactly_four_behavioral_features():
    config = load_config()

    assert config["task_type"] == "unsupervised_clustering"
    assert len(config["behavior_features"]) == 4

    expected_features = [
        "mean_course_events_percentile",
        "mean_course_active_days_percentile",
        "mean_course_chapters_percentile",
        "mean_course_forum_posts_percentile"
    ]

    assert config["behavior_features"] == expected_features


def test_config_quarantines_all_outcomes():
    config = load_config()

    expected_outcomes = {
        "certified",
        "grade",
        "viewed",
        "explored",
        "incomplete_flag"
    }

    assert set(config["outcome_columns"]) == expected_outcomes
    assert "quarantined" in config["outcome_policy"].lower()
    assert 197757 in config["video_policy"]["sentinel_values"]
    assert "not replace them with zero" in (
    config["video_policy"]["sentinel_handling"].lower()
    )


def test_raw_data_matches_expected_schema():
    config = load_config()

    assert RAW_DATA_PATH.exists()

    raw_sample = pd.read_csv(RAW_DATA_PATH, nrows=10)

    assert set(config["expected_raw_columns"]).issubset(
        raw_sample.columns
    )

    assert "userid_DI" in raw_sample.columns
    assert "course_id" in raw_sample.columns
    assert "nplay_video" in raw_sample.columns
    assert "grade" in raw_sample.columns
    assert "certified" in raw_sample.columns


def test_cleaned_student_table_has_no_outcome_leakage():
    config = load_config()

    assert STUDENTS_PATH.exists(), (
        "Run `python run_project.py` before executing generated-artifact tests."
    )

    students = pd.read_parquet(STUDENTS_PATH)

    assert "userid_DI" in students.columns
    assert students["userid_DI"].is_unique

    leaked_outcomes = set(config["outcome_columns"]).intersection(
        students.columns
    )

    assert not leaked_outcomes, (
        f"Outcome leakage found in students_cleaned.parquet: "
        f"{sorted(leaked_outcomes)}"
    )

    assert set(config["behavior_features"]).issubset(
        students.columns
    )


def test_feature_matrix_contains_only_identifier_and_four_features():
    config = load_config()

    assert FEATURE_MATRIX_PATH.exists()
    assert RAW_BEHAVIOR_PATH.exists()

    feature_matrix = pd.read_parquet(FEATURE_MATRIX_PATH)
    raw_behavior = pd.read_parquet(RAW_BEHAVIOR_PATH)

    expected_columns = [
        "userid_DI",
        *config["behavior_features"]
    ]

    assert feature_matrix.columns.tolist() == expected_columns
    assert raw_behavior.columns.tolist() == expected_columns

    assert feature_matrix["userid_DI"].is_unique
    assert raw_behavior["userid_DI"].is_unique

    assert not feature_matrix[
        config["behavior_features"]
    ].isna().any().any()

    assert set(config["outcome_columns"]).isdisjoint(
        feature_matrix.columns
    )

    profile_columns_excluding_identifier = set(
        config["profile_columns"]
    ) - {"userid_DI"}

    assert profile_columns_excluding_identifier.isdisjoint(
        feature_matrix.columns
    )


def test_feature_matrix_values_are_numeric_and_scaled():
    config = load_config()

    feature_matrix = pd.read_parquet(FEATURE_MATRIX_PATH)

    for feature in config["behavior_features"]:
        assert pd.api.types.is_numeric_dtype(
            feature_matrix[feature]
        )
        assert feature_matrix[feature].notna().all()


def test_k_selection_uses_all_four_metrics():
    assert K_METRICS_PATH.exists()

    metrics = pd.read_csv(K_METRICS_PATH)

    required_columns = {
        "k",
        "silhouette",
        "davies_bouldin",
        "calinski_harabasz",
        "resample_ari_mean",
        "gap_statistic",
        "gap_standard_error",
        "mean_metric_rank",
        "selected_k"
    }

    assert required_columns.issubset(metrics.columns)
    assert metrics["selected_k"].astype(bool).sum() == 1
    assert metrics["k"].between(2, 10).all()

    selected = metrics.loc[
        metrics["selected_k"].astype(bool)
    ].iloc[0]

    assert bool(selected["eligible_for_selection"])
    assert bool(selected["selected_by_gap_one_se"])


def test_cluster_assignments_match_feature_matrix():
    assert ASSIGNMENTS_PATH.exists()

    feature_matrix = pd.read_parquet(FEATURE_MATRIX_PATH)
    assignments = pd.read_csv(ASSIGNMENTS_PATH)

    assert assignments.columns.tolist() == [
        "userid_DI",
        "cluster"
    ]

    assert assignments["userid_DI"].is_unique
    assert len(assignments) == len(feature_matrix)
    assert set(assignments["userid_DI"]) == set(
        feature_matrix["userid_DI"]
    )

    assert assignments["cluster"].nunique() >= 2


def test_cluster_profiles_cover_all_clusters():
    assert PROFILES_PATH.exists()
    assert ASSIGNMENTS_PATH.exists()

    profiles = pd.read_csv(PROFILES_PATH)
    assignments = pd.read_csv(ASSIGNMENTS_PATH)

    required_columns = {
        "cluster",
        "cluster_name",
        "student_count",
        "student_pct",
        "relative_behavior_level"
    }

    assert required_columns.issubset(profiles.columns)
    assert profiles["cluster"].is_unique

    assert set(profiles["cluster"]) == set(
        assignments["cluster"]
    )

    assert int(profiles["student_count"].sum()) == len(assignments)

    assert abs(profiles["student_pct"].sum() - 100.0) < 0.01


def test_grade_audit_flags_outcomes_without_changing_raw_data():
    assert GRADE_AUDIT_PATH.exists()

    grade_audit = pd.read_csv(GRADE_AUDIT_PATH)

    required_columns = {
        "certified",
        "grade_numeric",
        "grade_missing_flag",
        "grade_out_of_range_flag",
        "certified_grade_zero_flag",
        "certified_grade_missing_flag",
        "requires_outcome_review"
    }

    assert required_columns.issubset(grade_audit.columns)

    certified_grade_zero = (
        grade_audit["certified"].eq(1)
        & grade_audit["grade_numeric"].eq(0)
    )

    assert (
        grade_audit.loc[
            certified_grade_zero,
            "certified_grade_zero_flag"
        ].eq(1).all()
    )


def test_deployment_pipeline_and_schema_are_compatible():
    config = load_config()

    assert PIPELINE_PATH.exists()
    assert INPUT_SCHEMA_PATH.exists()
    assert MODEL_LOCK_PATH.exists()

    pipeline = joblib.load(PIPELINE_PATH)

    schema = json.loads(
        INPUT_SCHEMA_PATH.read_text(encoding="utf-8")
    )

    model_lock = json.loads(
        MODEL_LOCK_PATH.read_text(encoding="utf-8")
    )

    assert schema["input_contract"]["required_feature_order"] == (
        config["behavior_features"]
    )

    assert schema["input_contract"]["required_feature_count"] == 4

    assert model_lock["behavior_features"] == (
        config["behavior_features"]
    )

    raw_behavior = pd.read_parquet(RAW_BEHAVIOR_PATH)

    sample = raw_behavior[
        config["behavior_features"]
    ].head(5)

    predictions = pipeline.predict(sample)

    assert len(predictions) == len(sample)

    known_clusters = set(
        schema["output_contract"]["known_cluster_values"]
    )

    assert set(predictions.astype(int)).issubset(known_clusters)


def test_dashboard_and_monitoring_artifacts_exist():
    assert REPORT_PATH.exists()
    assert MONITORING_REPORT_PATH.exists()

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    monitoring_report = json.loads(
        MONITORING_REPORT_PATH.read_text(encoding="utf-8")
    )

    assert "MOOC Learner Behaviour Dashboard" in report_text
    assert "K Selection" in report_text
    assert "Outcome leakage blocked" in report_text

    assert monitoring_report["status"] in {
        "not_evaluated",
        "normal",
        "warning",
        "action_required"
    }
