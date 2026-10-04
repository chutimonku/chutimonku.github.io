#!/usr/bin/env python3
"""Step 5: Build the four-feature behavioural matrix for clustering.

Only the four approved behavioural percentile features enter the clustering
matrix. Profile fields, identifiers, and quarantined outcomes are excluded.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


CONFIG_PATH = Path("config/project_config.json")
STUDENTS_PATH = Path("data/processed/students_cleaned.parquet")

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models/preprocessing_candidates")
TABLES_DIR = Path("outputs/tables")

RAW_BEHAVIOR_PATH = PROCESSED_DIR / "behavior_features_unscaled.parquet"
FEATURE_MATRIX_PATH = PROCESSED_DIR / "feature_matrix.parquet"
FEATURE_DEFINITIONS_PATH = PROCESSED_DIR / "feature_definitions.csv"
PREPROCESSOR_PATH = MODELS_DIR / "behavioral_preprocessor.joblib"
TRANSFORMATION_AUDIT_PATH = TABLES_DIR / "feature_engineering_audit.json"


def main() -> None:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing configuration: {CONFIG_PATH}")

    if not STUDENTS_PATH.exists():
        raise FileNotFoundError(
            f"Missing cleaned student table: {STUDENTS_PATH}. "
            "Run Step 3 first."
        )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    behavior_features = config["behavior_features"]
    outcome_columns = config["outcome_columns"]
    profile_columns = config["profile_columns"]

    if len(behavior_features) != 4:
        raise ValueError(
            "Exactly four behavioural features are required for this workflow."
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("STEP 5: FOUR-BEHAVIOURAL-FEATURE ENGINEERING")
    print("=" * 72)

    students = pd.read_parquet(STUDENTS_PATH)

    if "userid_DI" not in students.columns:
        raise ValueError(
            "students_cleaned.parquet must contain userid_DI."
        )

    missing_features = [
        column
        for column in behavior_features
        if column not in students.columns
    ]

    if missing_features:
        raise ValueError(
            "Required behavioural features are missing from the student table: "
            + ", ".join(missing_features)
        )

    leaked_outcomes = [
        column
        for column in outcome_columns
        if column in students.columns
    ]

    if leaked_outcomes:
        raise RuntimeError(
            "Outcome leakage detected in students_cleaned.parquet: "
            + ", ".join(leaked_outcomes)
        )

    profile_columns_present = [
        column
        for column in profile_columns
        if column in students.columns
    ]

    # Keep the learner identifier only for linking cluster assignments later.
    # It is never passed to the preprocessing pipeline or clustering model.
    raw_behavior = students[
        ["userid_DI", *behavior_features]
    ].copy()

    for feature in behavior_features:
        raw_behavior[feature] = pd.to_numeric(
            raw_behavior[feature],
            errors="coerce"
        )

    # Percentile features must remain inside the [0, 1] range.
    # Out-of-range values are treated as invalid/missing for imputation.
    out_of_range_counts: dict[str, int] = {}

    for feature in behavior_features:
        invalid_mask = (
            raw_behavior[feature].lt(0)
            | raw_behavior[feature].gt(1)
        )

        out_of_range_counts[feature] = int(invalid_mask.sum())

        raw_behavior.loc[invalid_mask, feature] = pd.NA

    # Save the unscaled feature table for transparent audit and dashboard use.
    raw_behavior.to_parquet(RAW_BEHAVIOR_PATH, index=False)

    # All four inputs are already comparable within-course percentiles on the
    # same bounded [0, 1] scale. Scaling them again would reweight sparse
    # features by their IQR; in this dataset it inflated forum activity by
    # roughly two orders of magnitude and made the clusters describe forum
    # outliers rather than balanced behaviour. Keep the percentile geometry.
    preprocessor = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    keep_empty_features=True
                )
            )
        ]
    )

    transformed_values = preprocessor.fit_transform(
        raw_behavior[behavior_features]
    )

    transformed_features = pd.DataFrame(
        transformed_values,
        columns=behavior_features,
        index=raw_behavior.index
    )

    feature_matrix = pd.concat(
        [
            raw_behavior[["userid_DI"]],
            transformed_features
        ],
        axis=1
    )

    if feature_matrix[behavior_features].isna().any().any():
        incomplete_features = feature_matrix.columns[
            feature_matrix.isna().any()
        ].tolist()

        raise RuntimeError(
            "Missing values remain after preprocessing: "
            + ", ".join(incomplete_features)
        )

    feature_matrix.to_parquet(FEATURE_MATRIX_PATH, index=False)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)

    feature_definitions = pd.DataFrame(
        [
            {
                "feature_name": feature,
                "feature_group": "behavioral",
                "source_level": "student",
                "source_definition": (
                    "Mean within-course behavioural percentile across all "
                    "enrollments belonging to the learner."
                ),
                "range_before_preprocessing": "0 to 1",
                "missing_value_handling": (
                    "Median imputation fitted on the clustering cohort."
                ),
                "scaling": "None: all selected inputs are already bounded percentiles on [0, 1].",
                "used_for_clustering": True,
                "used_for_profile_reporting": True,
                "profile_or_demographic_feature": False,
                "outcome_or_label_feature": False,
                "reason_for_inclusion": (
                    "Observed learning behaviour; not learner identity, "
                    "demographic profile, or educational outcome."
                )
            }
            for feature in behavior_features
        ]
    )

    feature_definitions.to_csv(
        FEATURE_DEFINITIONS_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    imputer = preprocessor.named_steps["imputer"]

    transformation_audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": str(STUDENTS_PATH),
        "raw_behavior_output": str(RAW_BEHAVIOR_PATH),
        "feature_matrix_output": str(FEATURE_MATRIX_PATH),
        "preprocessor_output": str(PREPROCESSOR_PATH),
        "student_count": int(len(raw_behavior)),
        "feature_count": int(len(behavior_features)),
        "selected_behavior_features": behavior_features,
        "excluded_profile_columns_present_in_source": profile_columns_present,
        "excluded_outcome_columns": outcome_columns,
        "outcomes_detected_in_source": leaked_outcomes,
        "identifier_excluded_from_model_input": "userid_DI",
        "missing_count_before_imputation": {
            feature: int(raw_behavior[feature].isna().sum())
            for feature in behavior_features
        },
        "out_of_range_values_converted_to_missing": out_of_range_counts,
        "median_imputation_statistics": {
            feature: float(value)
            for feature, value in zip(
                behavior_features,
                imputer.statistics_
            )
        },
        "preprocessing_geometry": "median imputation followed by identity transform on bounded percentile inputs",
        "robust_scaler_center": {feature: 0.0 for feature in behavior_features},
        "robust_scaler_scale": {feature: 1.0 for feature in behavior_features},
        "output_contains_missing_values": bool(
            feature_matrix[behavior_features].isna().any().any()
        ),
        "outcome_leakage_prevented": len(leaked_outcomes) == 0
    }

    TRANSFORMATION_AUDIT_PATH.write_text(
        json.dumps(transformation_audit, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[Step 5] Raw behavioural features: {RAW_BEHAVIOR_PATH}")
    print(f"[Step 5] Scaled feature matrix: {FEATURE_MATRIX_PATH}")
    print(f"[Step 5] Preprocessor: {PREPROCESSOR_PATH}")
    print(f"[Step 5] Feature definitions: {FEATURE_DEFINITIONS_PATH}")
    print(f"[Step 5] Transformation audit: {TRANSFORMATION_AUDIT_PATH}")
    print(
        "[Step 5] Clustering input features: "
        + ", ".join(behavior_features)
    )


if __name__ == "__main__":
    main()
