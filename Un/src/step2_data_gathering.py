#!/usr/bin/env python3
"""Step 2: Load, validate, quarantine outcomes, and document MOOC raw data."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


CONFIG_PATH = Path("config/project_config.json")

PROCESSED_DIR = Path("data/processed")
QUARANTINE_DIR = Path("data/quarantine")

RAW_FEATURES_PATH = PROCESSED_DIR / "raw_features.parquet"
RAW_OUTCOMES_PATH = QUARANTINE_DIR / "raw_outcomes.parquet"
PROVENANCE_PATH = PROCESSED_DIR / "data_provenance.json"
SCHEMA_REPORT_PATH = PROCESSED_DIR / "raw_schema_report.json"


def sha256_file(path: Path) -> str:
    """Return SHA-256 for provenance and reproducibility."""
    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def require_columns(df: pd.DataFrame, expected_columns: list[str]) -> None:
    """Fail early if the source does not follow the declared data contract."""
    missing = sorted(set(expected_columns) - set(df.columns))

    if missing:
        raise ValueError(
            "The raw dataset is missing required columns: "
            + ", ".join(missing)
        )


def main() -> None:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing configuration file: {CONFIG_PATH}"
        )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    raw_path = Path(config["raw_data_path"])
    expected_columns = config["expected_raw_columns"]
    identifier_columns = config["record_identifier_columns"]
    outcome_columns = config["outcome_columns"]

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw MOOC dataset not found: {raw_path}"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("STEP 2: DATA GATHERING, SCHEMA VALIDATION, AND OUTCOME QUARANTINE")
    print("=" * 72)
    print(f"[Step 2] Loading raw file: {raw_path}")

    df_raw = pd.read_csv(raw_path, low_memory=False)

    require_columns(df_raw, expected_columns)

    duplicated_columns = df_raw.columns[df_raw.columns.duplicated()].tolist()
    if duplicated_columns:
        raise ValueError(
            "The raw dataset contains duplicate column names: "
            + ", ".join(duplicated_columns)
        )

    unknown_columns = sorted(set(df_raw.columns) - set(expected_columns))
    ordered_columns = [
        column for column in expected_columns
        if column in df_raw.columns
    ]

    df_raw = df_raw[ordered_columns].copy()

    feature_columns = [
        column for column in df_raw.columns
        if column not in outcome_columns
    ]

    missing_identifier_columns = [
        column for column in identifier_columns
        if column not in feature_columns
    ]
    if missing_identifier_columns:
        raise ValueError(
            "Identifier columns must remain in the non-outcome feature table: "
            + ", ".join(missing_identifier_columns)
        )

    outcome_export_columns = list(
        dict.fromkeys(identifier_columns + outcome_columns)
    )

    raw_features = df_raw[feature_columns].copy()
    raw_outcomes = df_raw[outcome_export_columns].copy()

    raw_features.to_parquet(RAW_FEATURES_PATH, index=False)
    raw_outcomes.to_parquet(RAW_OUTCOMES_PATH, index=False)

    source_hash = sha256_file(raw_path)
    source_size_bytes = raw_path.stat().st_size

    schema_report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_file": str(raw_path),
        "expected_columns": expected_columns,
        "observed_columns": df_raw.columns.tolist(),
        "unknown_columns_ignored": unknown_columns,
        "row_count": int(len(df_raw)),
        "column_count": int(df_raw.shape[1]),
        "dtypes": {
            column: str(dtype)
            for column, dtype in df_raw.dtypes.items()
        },
        "missing_values_by_column": {
            column: int(df_raw[column].isna().sum())
            for column in df_raw.columns
        },
        "record_identifier_columns": identifier_columns,
        "outcome_columns_quarantined": outcome_columns,
        "feature_columns_available_for_next_step": feature_columns
    }

    provenance = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(raw_path),
        "source_file_name": raw_path.name,
        "sha256": source_hash,
        "file_size_bytes": int(source_size_bytes),
        "record_count": int(len(df_raw)),
        "raw_column_count": int(df_raw.shape[1]),
        "unit_of_analysis_at_source": (
            "One row per learner-course enrollment record."
        ),
        "dataset_source": config["dataset_source"],
        "outcome_quarantine": {
            "path": str(RAW_OUTCOMES_PATH),
            "columns": outcome_columns,
            "policy": config["outcome_policy"]
        },
        "non_outcome_feature_export": {
            "path": str(RAW_FEATURES_PATH),
            "column_count": int(len(feature_columns))
        }
    }

    SCHEMA_REPORT_PATH.write_text(
        json.dumps(schema_report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    PROVENANCE_PATH.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[Step 2] Raw rows loaded: {len(df_raw):,}")
    print(f"[Step 2] Raw columns validated: {len(df_raw.columns):,}")
    print(f"[Step 2] Non-outcome features exported: {RAW_FEATURES_PATH}")
    print(f"[Step 2] Outcome columns quarantined: {RAW_OUTCOMES_PATH}")
    print(f"[Step 2] Provenance written: {PROVENANCE_PATH}")
    print(f"[Step 2] SHA-256: {source_hash}")


if __name__ == "__main__":
    main()