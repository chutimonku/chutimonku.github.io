#!/usr/bin/env python3
"""Step 3: Clean MOOC enrollment records and build a student-level table.

This step:
1. Keeps raw input unchanged.
2. Cleans only non-outcome fields.
3. Quarantines outcomes from all clustering inputs.
4. Converts nplay_video sentinel values to missing and retains an audit flag.
5. Corrects reversed valid date pairs by swapping them and retains an audit flag.
6. Builds course-normalized behavioural percentiles for student-level analysis.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


CONFIG_PATH = Path("config/project_config.json")

RAW_FEATURES_PATH = Path("data/processed/raw_features.parquet")
RAW_OUTCOMES_PATH = Path("data/quarantine/raw_outcomes.parquet")

PROCESSED_DIR = Path("data/processed")
TABLES_DIR = Path("outputs/tables")

ENROLLMENTS_PATH = PROCESSED_DIR / "enrollments_cleaned.parquet"
STUDENTS_PATH = PROCESSED_DIR / "students_cleaned.parquet"
AUDIT_PATH = PROCESSED_DIR / "cleaning_audit.json"
DICTIONARY_PATH = PROCESSED_DIR / "data_dictionary.csv"


NUMERIC_ACTIVITY_COLUMNS = [
    "nevents",
    "ndays_act",
    "nplay_video",
    "nchapters",
    "nforum_posts",
]

TEXT_COLUMNS = [
    "institute",
    "course_id",
    "year",
    "semester",
    "gender",
    "LoE_DI",
    "final_cc_cname_DI",
]

PERCENTILE_SOURCE_COLUMNS = {
    "nevents_clean": "mean_course_events_percentile",
    "ndays_act_clean": "mean_course_active_days_percentile",
    "nchapters_clean": "mean_course_chapters_percentile",
    "nforum_posts_clean": "mean_course_forum_posts_percentile",
}


def require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Raise a clear error if a required source column is absent."""
    missing = sorted(set(columns) - set(df.columns))

    if missing:
        raise ValueError(
            "Missing required columns for cleaning: " + ", ".join(missing)
        )


def normalize_text(series: pd.Series, unknown_label: str = "Unknown") -> pd.Series:
    """Standardize text while retaining an explicit unknown category."""
    cleaned = series.astype("string").str.strip()
    cleaned = cleaned.mask(cleaned.isna() | cleaned.eq(""), unknown_label)
    return cleaned.fillna(unknown_label)


def safe_mean(series: pd.Series) -> float | None:
    """Return a JSON-safe mean or None when no non-missing values exist."""
    non_missing = series.dropna()

    if non_missing.empty:
        return None

    return float(non_missing.mean())


def main() -> None:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing configuration: {CONFIG_PATH}")

    if not RAW_FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Missing input: {RAW_FEATURES_PATH}. Run Step 2 first."
        )

    if not RAW_OUTCOMES_PATH.exists():
        raise FileNotFoundError(
            f"Missing quarantine file: {RAW_OUTCOMES_PATH}. Run Step 2 first."
        )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    video_sentinels = config["video_policy"]["sentinel_values"]
    minimum_plausible_age = config["age_policy"]["minimum_plausible_age"]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("STEP 3: MOOC DATA CLEANING AND STUDENT-LEVEL AGGREGATION")
    print("=" * 72)

    raw = pd.read_parquet(RAW_FEATURES_PATH)

    require_columns(
        raw,
        [
            "userid_DI",
            "course_id",
            "institute",
            "start_time_DI",
            "last_event_DI",
            "age",
            *NUMERIC_ACTIVITY_COLUMNS,
            *TEXT_COLUMNS,
        ],
    )

    rows_before = int(len(raw))
    work = raw.copy()

    # The export index is not a behavioural feature. Keep it only as source traceability.
    if "Unnamed: 0" in work.columns:
        work = work.rename(columns={"Unnamed: 0": "source_row_id"})

    # Remove only true duplicate enrollment records.
    duplicate_basis = [
        column
        for column in work.columns
        if column != "source_row_id"
    ]
    duplicate_mask = work.duplicated(subset=duplicate_basis, keep="first")
    duplicate_rows_removed = int(duplicate_mask.sum())
    work = work.loc[~duplicate_mask].copy()

    # Standardize text fields. These are retained for reporting/profile only.
    for column in TEXT_COLUMNS:
        work[f"{column}_clean"] = normalize_text(work[column])

    # Convert activity columns safely to numeric and flag invalid negatives.
    invalid_negative_counts: dict[str, int] = {}

    for column in NUMERIC_ACTIVITY_COLUMNS:
        numeric = pd.to_numeric(work[column], errors="coerce")
        invalid_negative = numeric.lt(0)
        invalid_negative_counts[column] = int(invalid_negative.sum())

        numeric = numeric.mask(invalid_negative, np.nan)
        work[f"{column}_clean"] = numeric

    # 197757 is an encoded/sentinel video value, not an observed play count.
    # Keep its flag for the dashboard; video is audit-only and never imputed
    # or used as a clustering feature.
    sentinel_mask = work["nplay_video_clean"].isin(video_sentinels)
    sentinel_video_count = int(sentinel_mask.sum())
    work["video_sentinel_flag"] = sentinel_mask.astype("int8")
    work["nplay_video_clean"] = work["nplay_video_clean"].mask(
        sentinel_mask,
        np.nan
    )
    work["video_missing_flag"] = (
        work["nplay_video_clean"].isna()
    ).astype("int8")

    # Age is profile-only. Values below the earliest plausible school-entry age
    # are invalid; no upper cutoff is imposed because older MOOC learners are valid.
    age_numeric = pd.to_numeric(work["age"], errors="coerce")
    invalid_age_mask = age_numeric.lt(minimum_plausible_age)
    work["age_clean"] = age_numeric.mask(invalid_age_mask, np.nan)
    work["age_invalid_flag"] = invalid_age_mask.astype("int8")
    work["age_missing_flag"] = work["age_clean"].isna().astype("int8")

    # Parse dates. Raw source fields stay untouched; reversed valid date pairs
    # are corrected in the derived *_dt fields by swapping them.
    work["start_dt"] = pd.to_datetime(
        work["start_time_DI"],
        errors="coerce",
        utc=True
    )
    work["last_event_dt"] = pd.to_datetime(
        work["last_event_DI"],
        errors="coerce",
        utc=True
    )

    work["start_date_missing_flag"] = work["start_dt"].isna().astype("int8")
    work["last_event_date_missing_flag"] = (
        work["last_event_dt"].isna()
    ).astype("int8")

    date_inversion_mask = (
        work["start_dt"].notna()
        & work["last_event_dt"].notna()
        & work["last_event_dt"].lt(work["start_dt"])
    )

    work["date_inversion_flag"] = date_inversion_mask.astype("int8")
    work["date_inversion_corrected_flag"] = date_inversion_mask.astype("int8")
    original_start = work.loc[date_inversion_mask, "start_dt"].copy()
    work.loc[date_inversion_mask, "start_dt"] = work.loc[
        date_inversion_mask, "last_event_dt"
    ].to_numpy()
    work.loc[date_inversion_mask, "last_event_dt"] = original_start.to_numpy()

    # Valid pairs include corrected inversions; missing dates remain NaN.
    work["activity_span_days"] = (
        work["last_event_dt"] - work["start_dt"]
    ).dt.total_seconds() / 86400.0

    # Create within-course behavioural percentiles.
    # These normalize behaviour so courses with different scales do not dominate.
    for source_column, percentile_column in PERCENTILE_SOURCE_COLUMNS.items():
        work[percentile_column] = (
            work.groupby("course_id_clean")[source_column]
            .rank(method="average", pct=True)
            .astype("float64")
        )

    # Build one row per student.
    grouped = work.groupby("userid_DI", dropna=False)

    students = grouped.agg(
        n_enrollments=("course_id_clean", "size"),
        n_courses=("course_id_clean", "nunique"),
        n_institutes=("institute_clean", "nunique"),
        first_start_dt=("start_dt", "min"),
        last_event_dt=("last_event_dt", "max"),
        total_events=("nevents_clean", "sum"),
        total_active_days=("ndays_act_clean", "sum"),
        total_video_plays=("nplay_video_clean", "sum"),
        total_forum_posts=("nforum_posts_clean", "sum"),
        total_chapters=("nchapters_clean", "sum"),
        mean_course_events_percentile=(
            "mean_course_events_percentile",
            "mean"
        ),
        mean_course_active_days_percentile=(
            "mean_course_active_days_percentile",
            "mean"
        ),
        mean_course_chapters_percentile=(
            "mean_course_chapters_percentile",
            "mean"
        ),
        mean_course_forum_posts_percentile=(
            "mean_course_forum_posts_percentile",
            "mean"
        ),
        video_missing_records=("video_missing_flag", "sum"),
        video_sentinel_records=("video_sentinel_flag", "sum"),
        date_inversion_records=("date_inversion_flag", "sum"),
        date_inversion_corrected_records=(
            "date_inversion_corrected_flag",
            "sum"
        ),
        age_invalid_records=("age_invalid_flag", "sum"),
        age_missing_records=("age_missing_flag", "sum"),
        profile_gender=("gender_clean", lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"),
        profile_education=("LoE_DI_clean", lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"),
        profile_country=("final_cc_cname_DI_clean", lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"),
        profile_institutes=("institute_clean", lambda s: " + ".join(sorted(s.dropna().unique()))),
    ).reset_index()

    students["overall_span_days"] = (
        students["last_event_dt"] - students["first_start_dt"]
    ).dt.total_seconds() / 86400.0

    students.loc[
        students["overall_span_days"].lt(0),
        "overall_span_days"
    ] = np.nan

    students["video_data_available_rate"] = (
        1
        - students["video_missing_records"]
        / students["n_enrollments"].clip(lower=1)
    )

    students["event_intensity"] = (
        students["total_events"]
        / students["total_active_days"].clip(lower=1)
    )

    # Do not write outcome columns into this student feature table.
    forbidden_outcomes = set(config["outcome_columns"])
    leaked_outcomes = sorted(
        forbidden_outcomes.intersection(students.columns)
    )

    if leaked_outcomes:
        raise RuntimeError(
            "Outcome leakage detected in students_cleaned.parquet: "
            + ", ".join(leaked_outcomes)
        )

    work.to_parquet(ENROLLMENTS_PATH, index=False)
    students.to_parquet(STUDENTS_PATH, index=False)

    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": str(RAW_FEATURES_PATH),
        "rows_before_cleaning": rows_before,
        "rows_after_duplicate_removal": int(len(work)),
        "duplicate_rows_removed": duplicate_rows_removed,
        "outcome_columns_present_in_cleaned_student_table": leaked_outcomes,
        "video_sentinel_values": video_sentinels,
        "video_sentinel_rows_converted_to_missing": sentinel_video_count,
        "video_missing_rows_after_cleaning": int(
            work["video_missing_flag"].sum()
        ),
        "invalid_negative_counts": invalid_negative_counts,
        "invalid_age_rows_flagged": int(work["age_invalid_flag"].sum()),
        "minimum_plausible_age": minimum_plausible_age,
        "age_missing_rows_after_cleaning": int(
            work["age_missing_flag"].sum()
        ),
        "start_date_missing_rows": int(
            work["start_date_missing_flag"].sum()
        ),
        "last_event_date_missing_rows": int(
            work["last_event_date_missing_flag"].sum()
        ),
        "date_inversion_rows_flagged": int(
            work["date_inversion_flag"].sum()
        ),
        "date_inversion_rows_corrected_by_swapping": int(
            work["date_inversion_corrected_flag"].sum()
        ),
        "student_count_after_aggregation": int(len(students)),
        "behaviour_feature_missing_rate": {
            column: float(students[column].isna().mean())
            for column in config["behavior_features"]
        },
        "action_summary": {
            "raw_data_changed": False,
            "duplicates_removed": duplicate_rows_removed,
            "sentinel_values_replaced_with_zero": False,
            "outcomes_used_as_features": False,
            "invalid_dates_removed": False,
            "invalid_dates_corrected_by_swapping": int(
                work["date_inversion_corrected_flag"].sum()
            )
        }
    }

    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    dictionary_rows = [
        {
            "column": column,
            "level": "student",
            "role": "behavioral_feature",
            "used_for_clustering": True,
            "description": (
                "Mean within-course percentile across the learner's enrollments."
            )
        }
        for column in config["behavior_features"]
    ]

    dictionary_rows.extend(
        [
            {
                "column": "video_missing_records",
                "level": "student",
                "role": "data_quality_flag",
                "used_for_clustering": False,
                "description": (
                    "Number of enrollment records with missing or sentinel "
                    "video-play values."
                )
            },
            {
                "column": "date_inversion_records",
                "level": "student",
                "role": "data_quality_flag",
                "used_for_clustering": False,
                "description": (
                    "Number of enrollment records where last event precedes "
                    "course start in the raw fields; the derived dates were swapped."
                )
            },
            {
                "column": "profile_gender",
                "level": "student",
                "role": "profile_only",
                "used_for_clustering": False,
                "description": "Profile field retained for descriptive reporting only."
            },
            {
                "column": "profile_education",
                "level": "student",
                "role": "profile_only",
                "used_for_clustering": False,
                "description": "Profile field retained for descriptive reporting only."
            },
            {
                "column": "profile_country",
                "level": "student",
                "role": "profile_only",
                "used_for_clustering": False,
                "description": "Profile field retained for descriptive reporting only."
            }
        ]
    )

    pd.DataFrame(dictionary_rows).to_csv(
        DICTIONARY_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"[Step 3] Clean enrollment records: {ENROLLMENTS_PATH}")
    print(f"[Step 3] Clean student table: {STUDENTS_PATH}")
    print(f"[Step 3] Student count: {len(students):,}")
    print(f"[Step 3] Cleaning audit: {AUDIT_PATH}")
    print(f"[Step 3] Data dictionary: {DICTIONARY_PATH}")


if __name__ == "__main__":
    main()
