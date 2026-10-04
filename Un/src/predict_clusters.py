#!/usr/bin/env python3
"""Predict MOOC behavioural clusters using the locked deployment pipeline.

Example:
python -m src.predict_clusters \
  --input examples/sample_student_input.csv \
  --output outputs/data/new_cluster_predictions.csv
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd


CONFIG_PATH = Path("config/project_config.json")
PIPELINE_PATH = Path("models/final/clustering_pipeline.joblib")
SCHEMA_PATH = Path("models/final/input_schema.json")


def load_json(path: Path) -> dict:
    """Load a required JSON artifact."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def validate_input(
    frame: pd.DataFrame,
    behavior_features: list[str],
    outcome_columns: list[str],
    profile_columns: list[str]
) -> tuple[pd.DataFrame, pd.Series]:
    """Validate and prepare student-level behavioural input for prediction."""
    if frame.empty:
        raise ValueError("Input CSV contains zero rows.")

    missing_features = [
        feature
        for feature in behavior_features
        if feature not in frame.columns
    ]

    if missing_features:
        raise ValueError(
            "Input is missing required behavioural features: "
            + ", ".join(missing_features)
        )

    forbidden_columns = sorted(
        set(frame.columns).intersection(
            set(outcome_columns + profile_columns)
        )
    )

    forbidden_columns = [
        column
        for column in forbidden_columns
        if column != "userid_DI"
    ]

    if forbidden_columns:
        raise ValueError(
            "Input contains forbidden outcome/profile columns: "
            + ", ".join(forbidden_columns)
        )

    allowed_columns = set(behavior_features + ["userid_DI"])

    unexpected_columns = [
        column
        for column in frame.columns
        if column not in allowed_columns
    ]

    if unexpected_columns:
        raise ValueError(
            "Input contains unexpected columns: "
            + ", ".join(unexpected_columns)
        )

    if "userid_DI" in frame.columns:
        identifiers = frame["userid_DI"].astype("string")

        if identifiers.isna().any() or identifiers.eq("").any():
            raise ValueError(
                "userid_DI is present but contains missing or blank values."
            )

        if identifiers.duplicated().any():
            raise ValueError(
                "Input contains duplicate userid_DI values. "
                "Each row must represent one student."
            )
    else:
        identifiers = pd.Series(
            [f"input_row_{index + 1}" for index in range(len(frame))],
            name="userid_DI",
            dtype="string"
        )

    features = frame[behavior_features].copy()

    invalid_numeric_counts: dict[str, int] = {}

    for feature in behavior_features:
        original_non_missing = features[feature].notna()

        features[feature] = pd.to_numeric(
            features[feature],
            errors="coerce"
        )

        invalid_numeric_counts[feature] = int(
            original_non_missing.sum()
            - features[feature].notna().sum()
        )

        invalid_range = (
            features[feature].notna()
            & (
                features[feature].lt(0)
                | features[feature].gt(1)
            )
        )

        if invalid_range.any():
            invalid_values = features.loc[
                invalid_range,
                feature
            ].head(5).tolist()

            raise ValueError(
                f"Feature '{feature}' has values outside [0, 1]. "
                f"Examples: {invalid_values}"
            )

    features.attrs["invalid_numeric_counts"] = invalid_numeric_counts

    return features, identifiers


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Assign MOOC learners to behavioural clusters using the locked "
            "four-feature clustering pipeline."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help=(
            "CSV with optional userid_DI and the four required behavioural "
            "percentile features."
        )
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination CSV for cluster predictions."
    )

    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=None,
        help=(
            "Optional JSON metadata output. Defaults to a JSON file beside "
            "the prediction CSV."
        )
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if not args.input.exists():
        raise FileNotFoundError(f"Input CSV not found: {args.input}")

    config = load_json(CONFIG_PATH)
    schema = load_json(SCHEMA_PATH)

    if not PIPELINE_PATH.exists():
        raise FileNotFoundError(
            f"Locked pipeline not found: {PIPELINE_PATH}"
        )

    behavior_features = config["behavior_features"]
    outcome_columns = config["outcome_columns"]
    profile_columns = config["profile_columns"]

    schema_features = schema["input_contract"]["required_feature_order"]

    if behavior_features != schema_features:
        raise RuntimeError(
            "Configuration features do not match the locked deployment schema."
        )

    print("=" * 72)
    print("MOOC BEHAVIOURAL CLUSTER PREDICTION")
    print("=" * 72)
    print(f"Input: {args.input}")

    input_frame = pd.read_csv(args.input)

    model_input, identifiers = validate_input(
        frame=input_frame,
        behavior_features=behavior_features,
        outcome_columns=outcome_columns,
        profile_columns=profile_columns
    )

    pipeline = joblib.load(PIPELINE_PATH)
    predictions = pipeline.predict(model_input)

    cluster_metadata = schema["output_contract"]["cluster_metadata"]

    result = pd.DataFrame({
        "userid_DI": identifiers,
        "cluster": predictions.astype(int)
    })

    result["cluster_name"] = result["cluster"].map(
        lambda cluster: cluster_metadata[str(cluster)]["cluster_name"]
    )

    result["relative_behavior_level"] = result["cluster"].map(
        lambda cluster: cluster_metadata[str(cluster)][
            "relative_behavior_level"
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)

    result.to_csv(
        args.output,
        index=False,
        encoding="utf-8-sig"
    )

    metadata_output = args.metadata_output

    if metadata_output is None:
        metadata_output = args.output.with_suffix(".metadata.json")

    metadata_output.parent.mkdir(parents=True, exist_ok=True)

    prediction_metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": str(args.input),
        "output_path": str(args.output),
        "student_count": int(len(result)),
        "behavior_features": behavior_features,
        "cluster_counts": {
            str(cluster): int(count)
            for cluster, count in result["cluster"]
            .value_counts()
            .sort_index()
            .items()
        },
        "missing_values_in_input": {
            feature: int(model_input[feature].isna().sum())
            for feature in behavior_features
        },
        "non_numeric_values_converted_to_missing": (
            model_input.attrs["invalid_numeric_counts"]
        ),
        "outcomes_allowed_as_input": False,
        "profile_columns_allowed_as_input": False,
        "note": (
            "Missing behavioural values are handled by the median imputer "
            "stored inside the locked preprocessing pipeline."
        )
    }

    metadata_output.write_text(
        json.dumps(prediction_metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Predictions written to: {args.output}")
    print(f"Prediction metadata written to: {metadata_output}")
    print(f"Predicted students: {len(result):,}")


if __name__ == "__main__":
    main()