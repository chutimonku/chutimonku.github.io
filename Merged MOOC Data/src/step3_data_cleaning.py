"""Step 3: clean each source first, then reconcile, merge, and aggregate."""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from src.data_quality_audit import append_processing_log, profile_columns

INTERIM_FILES = [
    os.path.join("data", "interim", "HXPC13_harmonized.parquet"),
    os.path.join("data", "interim", "big_student_harmonized.parquet"),
]
PROCESSED = os.path.join("data", "processed")
SOURCE_CLEAN = os.path.join(PROCESSED, "sources")
QUARANTINE = os.path.join("data", "quarantine")
TABLES = os.path.join("outputs", "tables")
FIGURES = os.path.join("outputs", "figures", "data_quality")
LOG = os.path.join("outputs", "logs", "data_processing_log.csv")
# One deduplicated enrollment means one student in one canonical course.
# The previous key included year/semester, which treated repeated course-runs
# as separate enrollments and inflated the cleaned enrollment table to 624,674.
KEY = ["userid_DI", "course_id"]
COURSE_CONTEXT = ["institute", "year", "semester"]
OUTCOMES = ["certified", "grade", "viewed", "explored", "incomplete_flag"]
BEHAVIORS = ["nevents", "ndays_act", "nplay_video", "nchapters", "nforum_posts"]

LOE_HIERARCHY = {"Unknown": 0, "Less than Secondary": 1, "Secondary": 2, "Bachelor's": 3, "Master's": 4, "Doctorate": 5}
LOE_REVERSE = {value: key for key, value in LOE_HIERARCHY.items()}


def _standardize_text(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    return text.mask(text.isin(["", "nan", "None", "<NA>"]))


def clean_source(frame: pd.DataFrame):
    """Apply source-level rules before any cross-source reconciliation."""
    data = frame.copy()
    for column in OUTCOMES + BEHAVIORS + ["age", "year"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    sentinel = data["nplay_video"].eq(197757)
    data.loc[sentinel, "nplay_video"] = np.nan
    invalid_age = data["age"].le(10) | data["age"].gt(100)
    data.loc[invalid_age, "age"] = np.nan

    data["gender_merge"] = _standardize_text(data["gender"]).str.lower()
    data.loc[~data["gender_merge"].isin(["m", "f", "o"]), "gender_merge"] = pd.NA
    data["loe_merge"] = _standardize_text(data["LoE_DI"])
    data.loc[~data["loe_merge"].isin([value for value in LOE_HIERARCHY if value != "Unknown"]), "loe_merge"] = pd.NA
    data["country_merge"] = _standardize_text(data["final_cc_cname_DI"])

    data["original_start_time_DI"] = data["start_time_DI"]
    data["original_last_event_DI"] = data["last_event_DI"]
    start = pd.to_datetime(data["start_time_DI"], errors="coerce", format="mixed")
    last = pd.to_datetime(data["last_event_DI"], errors="coerce", format="mixed")
    inverted = start.notna() & last.notna() & last.lt(start)
    data["clean_start_dt"] = start.where(~inverted, last)
    data["clean_last_dt"] = last.where(~inverted, start)
    data["date_inversion_flag"] = inverted.astype("int8")
    data["date_missing_flag"] = (data["clean_start_dt"].isna() | data["clean_last_dt"].isna()).astype("int8")

    negative_counts = {}
    for column in BEHAVIORS:
        clean = pd.to_numeric(data[column], errors="coerce")
        negative = clean.lt(0).fillna(False)
        negative_counts[column] = int(negative.sum())
        data[f"{column}_clean"] = clean.mask(negative)

    source_stats = {
        "source_file": str(data["source_dataset"].iloc[0]),
        "records": int(len(data)),
        "video_sentinel_to_missing": int(sentinel.sum()),
        "invalid_age_to_missing": int(invalid_age.sum()),
        "date_pairs_swapped": int(inverted.sum()),
        "gender_missing_or_invalid": int(data["gender_merge"].isna().sum()),
        **{f"{column}_missing_after_clean": int(data[f"{column}_clean"].isna().sum()) for column in BEHAVIORS},
        **{f"{column}_negative_to_missing": count for column, count in negative_counts.items()},
    }
    return data, source_stats


def _first_non_null(series: pd.Series):
    values = series.dropna()
    return values.iloc[0] if len(values) else pd.NA


def reconcile_sources(clean_sources):
    """Coalesce duplicate enrollments only after both sources are cleaned."""
    combined = pd.concat(clean_sources, ignore_index=True).sort_values(["source_priority", "source_record_id"], kind="mergesort")
    membership = combined.groupby(KEY, dropna=False)["source_dataset"].agg(lambda s: " + ".join(sorted(set(s)))).rename("source_membership")
    source_count = combined.groupby(KEY, dropna=False)["source_dataset"].nunique().rename("source_count")

    conflict_rows = []
    inspect = COURSE_CONTEXT + ["gender_merge", "loe_merge", "country_merge", "age", "clean_start_dt", "clean_last_dt"] + [f"{c}_clean" for c in BEHAVIORS] + OUTCOMES
    duplicates = combined[combined.duplicated(KEY, keep=False)]
    for column in inspect:
        conflicts = duplicates.groupby(KEY, dropna=False)[column].nunique(dropna=True).gt(1)
        conflict_rows.append({"column": column, "overlapping_enrollments_with_conflict": int(conflicts.sum())})

    max_outcomes = {"viewed": "max", "explored": "max", "certified": "max", "incomplete_flag": "max"}
    other_inspect = [c for c in inspect if c not in max_outcomes]

    merged = combined.groupby(KEY, as_index=False, sort=False, dropna=False).agg({
        **{column: "first" for column in other_inspect},
        **max_outcomes,
        "date_inversion_flag": "max", "date_missing_flag": "min",
        "source_priority": "min", "source_record_id": "first",
    })
    merged = merged.merge(membership.reset_index(), on=KEY, how="left").merge(source_count.reset_index(), on=KEY, how="left")
    merged["source_dataset"] = merged["source_membership"]

    merged["gender_clean"] = merged["gender_merge"].fillna("Unknown")
    merged["LoE_clean"] = merged["loe_merge"].fillna("Unknown")
    merged["country_clean"] = merged["country_merge"].fillna("Unknown")
    merged["age_clean"] = pd.to_numeric(merged["age"], errors="coerce")
    merged["age_missing"] = merged["age_clean"].isna().astype("int8")
    for column in BEHAVIORS:
        merged[f"{column}_missing"] = merged[f"{column}_clean"].isna().astype("int8")
        merged[f"{column}_filled"] = merged[f"{column}_clean"].fillna(0)

    offering = ["institute", "course_id", "year", "semester"]
    for source, output in {
        "nevents_clean": "events_percentile_within_course",
        "ndays_act_clean": "active_days_percentile_within_course",
        "nplay_video_clean": "video_plays_percentile_within_course",
        "nchapters_clean": "chapters_percentile_within_course",
        "nforum_posts_clean": "forum_posts_percentile_within_course",
    }.items():
        merged[output] = merged.groupby(offering, dropna=False)[source].rank(method="average", pct=True)
    return merged, pd.DataFrame(conflict_rows), len(combined) - len(merged)


def audit_outcomes(outcomes: pd.DataFrame):
    data = outcomes.copy()
    for column in OUTCOMES:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["grade_out_of_range"] = ((data["grade"] < 0) | (data["grade"] > 1)).fillna(False)
    data["certified_with_zero_grade"] = (data["certified"].eq(1) & data["grade"].eq(0)).fillna(False)
    data["certified_below_documented_minimum"] = (data["certified"].eq(1) & data["grade"].notna() & data["grade"].lt(0.50)).fillna(False)
    data["certified_with_missing_grade"] = (data["certified"].eq(1) & data["grade"].isna()).fillna(False)
    data["eligible_for_supervised_target"] = ~data[["grade_out_of_range", "certified_below_documented_minimum", "certified_with_missing_grade"]].any(axis=1)
    summary = data.groupby(["institute", "course_id", "year", "semester"], dropna=False).agg(
        enrollment_records=("userid_DI", "size"), certified_records=("certified", lambda s: int(s.eq(1).sum())),
        grade_missing=("grade", lambda s: int(s.isna().sum())),
        certified_with_zero_grade=("certified_with_zero_grade", "sum"),
        certified_below_documented_minimum=("certified_below_documented_minimum", "sum"),
        certified_with_missing_grade=("certified_with_missing_grade", "sum"),
        grade_out_of_range=("grade_out_of_range", "sum"),
        supervised_eligible_records=("eligible_for_supervised_target", "sum"),
    ).reset_index()
    return data, summary


def aggregate_students(enrollments: pd.DataFrame) -> pd.DataFrame:
    data = enrollments.copy()
    data["loe_rank"] = data["LoE_clean"].map(LOE_HIERARCHY).fillna(0)
    # Ensure datetime columns are proper pandas datetime types to avoid mixed dtype errors in aggregation
    data["clean_start_dt"] = pd.to_datetime(data["clean_start_dt"], errors="coerce")
    data["clean_last_dt"] = pd.to_datetime(data["clean_last_dt"], errors="coerce")
    grouped = data.groupby("userid_DI", dropna=False)
    students = grouped.agg(
        n_enrollments=("course_id", "size"), unique_courses=("course_id", "nunique"), n_institutes=("institute", "nunique"),
        institutes_enrolled=("institute", lambda s: "Both" if s.nunique() > 1 else str(s.dropna().iloc[0]) if len(s.dropna()) else "Unknown"),
        date_inversion_records=("date_inversion_flag", "sum"),
        first_start_dt=("clean_start_dt", "min"), last_event_dt=("clean_last_dt", "max"),
        total_events=("nevents_filled", "sum"), mean_events_per_course=("nevents_filled", "mean"), max_events_single_course=("nevents_filled", "max"),
        total_active_days=("ndays_act_filled", "sum"), mean_active_days_per_course=("ndays_act_filled", "mean"), max_active_days_single_course=("ndays_act_filled", "max"),
        total_video_plays=("nplay_video_filled", "sum"), mean_video_plays_per_course=("nplay_video_filled", "mean"), video_missing_records=("nplay_video_missing", "sum"),
        total_chapters=("nchapters_filled", "sum"), mean_chapters_per_course=("nchapters_filled", "mean"), max_chapters_single_course=("nchapters_filled", "max"),
        total_forum_posts=("nforum_posts_filled", "sum"), mean_forum_posts_per_course=("nforum_posts_filled", "mean"), max_forum_posts_single_course=("nforum_posts_filled", "max"),
        mean_course_events_percentile=("events_percentile_within_course", "mean"),
        mean_course_active_days_percentile=("active_days_percentile_within_course", "mean"),
        mean_course_video_plays_percentile=("video_plays_percentile_within_course", "mean"),
        mean_course_chapters_percentile=("chapters_percentile_within_course", "mean"),
        mean_course_forum_posts_percentile=("forum_posts_percentile_within_course", "mean"),
        demog_age=("age_clean", "median"), age_missing_records=("age_missing", "sum"), demog_loe_rank=("loe_rank", "max"),
        demog_gender=("gender_clean", lambda s: s.mode().iloc[0] if len(s.mode()) else "Unknown"),
        demog_country=("country_clean", lambda s: s.mode().iloc[0] if len(s.mode()) else "Unknown"),
        source_membership=("source_membership", lambda s: " + ".join(sorted(set(s)))),
    ).reset_index()
    students["n_courses"] = students["n_enrollments"]
    students["video_data_available_rate"] = 1 - students["video_missing_records"] / students["n_enrollments"].clip(lower=1)
    students["demog_loe"] = students["demog_loe_rank"].map(LOE_REVERSE).fillna("Unknown")
    span = (students["last_event_dt"] - students["first_start_dt"]).dt.days.astype(float)
    students["overall_span_days"] = span.where(span.ge(0))
    students["overall_span_missing"] = students["overall_span_days"].isna().astype("int8")
    students["event_intensity"] = students["total_events"] / students["total_active_days"].clip(lower=1)
    students["video_intensity"] = students["total_video_plays"] / students["total_events"].clip(lower=1)
    students["chapters_per_day"] = students["total_chapters"] / students["total_active_days"].clip(lower=1)
    students["forum_posts_per_active_day"] = students["total_forum_posts"] / students["total_active_days"].clip(lower=1)
    students["has_forum_activity"] = students["total_forum_posts"].gt(0).astype("int8")
    students["has_multiple_courses"] = students["n_enrollments"].gt(1).astype("int8")
    students["is_cross_institution"] = students["n_institutes"].gt(1).astype("int8")
    return students


def build_missing_decisions(enrollments):
    actions = {
        "gender": "standardize; set missing/invalid to Unknown after reconciliation",
        "LoE_DI": "standardize; set missing/invalid to Unknown after reconciliation",
        "final_cc_cname_DI": "standardize; set missing to Unknown after reconciliation",
        "age": "values <=10 or >100 become missing; model-specific median imputation after split",
        "start_time_DI": "parse; swap valid reversed pairs; retain original and flag",
        "last_event_DI": "parse; swap valid reversed pairs; preserve missing",
        "nplay_video": "197757 sentinel and negative values become missing; preserve missingness indicator",
        "nevents": "negative/non-numeric becomes missing; zero-fill only for aggregation with indicator",
        "ndays_act": "negative/non-numeric becomes missing; zero-fill only for aggregation with indicator",
        "nchapters": "negative/non-numeric becomes missing; zero-fill only for aggregation with indicator",
        "nforum_posts": "negative/non-numeric becomes missing; zero-fill only for aggregation with indicator",
        "certified/grade/viewed/explored/incomplete_flag": "quarantine; never use in unsupervised feature selection",
    }
    return pd.DataFrame([{"column_or_group": key, "cleaning_action": value} for key, value in actions.items()])


def run_data_cleaning():
    for directory in [PROCESSED, SOURCE_CLEAN, QUARANTINE, TABLES, FIGURES]:
        os.makedirs(directory, exist_ok=True)
    if not all(os.path.exists(path) for path in INTERIM_FILES):
        raise FileNotFoundError("Run Step 2 first; source-specific harmonized files are missing.")

    cleaned_sources, source_rows = [], []
    for path in INTERIM_FILES:
        frame = pd.read_parquet(path)
        cleaned, stats = clean_source(frame)
        cleaned_sources.append(cleaned)
        source_rows.append(stats)
        out = os.path.join(SOURCE_CLEAN, os.path.basename(path).replace("_harmonized", "_cleaned"))
        cleaned.to_parquet(out, index=False)
    pd.DataFrame(source_rows).to_csv(os.path.join(TABLES, "source_cleaning_summary.csv"), index=False)
    profile_columns({row["source_file"]: frame for row, frame in zip(source_rows, cleaned_sources)}).to_csv(
        os.path.join(TABLES, "source_cleaned_column_profile.csv"), index=False
    )

    enrollments, conflicts, removed = reconcile_sources(cleaned_sources)
    conflicts.to_csv(os.path.join(TABLES, "source_reconciliation_conflicts.csv"), index=False)
    outcomes = enrollments[KEY + COURSE_CONTEXT + OUTCOMES].copy()
    audited, outcome_summary = audit_outcomes(outcomes)
    audited.to_parquet(os.path.join(QUARANTINE, "outcome_quality_flags.parquet"), index=False)
    audited.loc[audited["eligible_for_supervised_target"]].to_parquet(os.path.join(QUARANTINE, "supervised_outcomes_cleaned.parquet"), index=False)
    outcomes.to_parquet(os.path.join(QUARANTINE, "quarantined_enrollment_outcomes.parquet"), index=False)
    student_outcomes = outcomes.groupby("userid_DI", as_index=False).agg(
        ever_certified=("certified", "max"), n_courses_certified=("certified", "sum"), max_grade=("grade", "max"),
        mean_grade=("grade", "mean"), ever_viewed=("viewed", "max"), ever_explored=("explored", "max"),
        incomplete_status=("incomplete_flag", "max"),
    )
    student_outcomes.to_parquet(os.path.join(QUARANTINE, "quarantined_outcomes.parquet"), index=False)
    outcome_summary.to_csv(os.path.join(TABLES, "outcome_consistency_summary.csv"), index=False)

    # Retain enrollment-level data and export for full auditability
    feature_enrollments = enrollments.drop(columns=OUTCOMES + ["gender_merge", "loe_merge", "country_merge", "age"], errors="ignore")
    feature_enrollments.to_parquet(os.path.join(PROCESSED, "enrollments_cleaned.parquet"), index=False)
    feature_enrollments.to_csv(os.path.join(PROCESSED, "enrollments_cleaned.csv.gz"), index=False, compression="gzip")
    feature_enrollments.to_parquet(os.path.join(PROCESSED, "raw_non_outcomes.parquet"), index=False)

    students = aggregate_students(feature_enrollments)
    students.to_parquet(os.path.join(PROCESSED, "students_cleaned.parquet"), index=False)
    students.to_csv(os.path.join(PROCESSED, "students_cleaned.csv.gz"), index=False, compression="gzip")

    build_missing_decisions(enrollments).to_csv(os.path.join(TABLES, "missing_value_decisions.csv"), index=False)
    offering = ["institute", "course_id", "year", "semester"]
    enrollments.groupby(offering, dropna=False).agg(
        enrollments=("userid_DI", "size"), unique_students=("userid_DI", "nunique"), source_count=("source_count", "max"),
        gender_unknown=("gender_clean", lambda s: int(s.eq("Unknown").sum())), invalid_or_missing_age=("age_missing", "sum"),
        date_swaps=("date_inversion_flag", "sum"), missing_last_event=("clean_last_dt", lambda s: int(s.isna().sum())),
        median_events=("nevents_filled", "median"), median_active_days=("ndays_act_filled", "median"),
        median_video_plays=("nplay_video_filled", "median"), median_accessed_chapters=("nchapters_filled", "median"),
        median_forum_posts=("nforum_posts_filled", "median"),
    ).reset_index().to_csv(os.path.join(TABLES, "course_offering_profile.csv"), index=False)

    class_rows = []
    for level, frame, columns in [
        ("enrollment", audited, ["certified", "viewed", "explored", "incomplete_flag"]),
        ("student", student_outcomes, ["ever_certified", "ever_viewed", "ever_explored", "incomplete_status"]),
    ]:
        for column in columns:
            series = pd.to_numeric(frame[column], errors="coerce").dropna()
            c0, c1 = int(series.eq(0).sum()), int(series.eq(1).sum())
            class_rows.append({"analysis_level": level, "outcome": column, "class_0": c0, "class_1": c1,
                               "positive_rate": c1 / len(series), "majority_to_minority_ratio": max(c0, c1) / max(min(c0, c1), 1)})
    pd.DataFrame(class_rows).to_csv(os.path.join(TABLES, "class_balance_audit.csv"), index=False)

    summary = pd.DataFrame([
        {"issue_type": "Source-first cleaning", "decision": "Cleaned each source before reconciliation", "affected_records": sum(row["records"] for row in source_rows)},
        {"issue_type": "Cross-source overlap", "decision": "Official-source-first non-null coalescing by exact enrollment key", "affected_records": removed},
        {"issue_type": "Video sentinel", "decision": "197757 converted to missing before merge", "affected_records": sum(row["video_sentinel_to_missing"] for row in source_rows)},
        {"issue_type": "Invalid age", "decision": "Converted to missing before merge", "affected_records": sum(row["invalid_age_to_missing"] for row in source_rows)},
        {"issue_type": "Reversed dates", "decision": "Valid pairs swapped within each source before merge", "affected_records": sum(row["date_pairs_swapped"] for row in source_rows)},
        {"issue_type": "Outcome consistency", "decision": "Contradictions quarantined; invalid labels excluded only from supervised eligibility", "affected_records": int((~audited["eligible_for_supervised_target"]).sum())},
        {"issue_type": "Student aggregation", "decision": "One row per userid_DI after clean reconciliation", "affected_records": len(students)},
    ])
    summary.to_csv(os.path.join(TABLES, "cleaning_summary.csv"), index=False)
    with open(os.path.join(PROCESSED, "cleaning_rules.json"), "w", encoding="utf-8") as handle:
        json.dump({
            "order": "clean each source -> reconcile duplicate enrollments -> quarantine outcomes -> aggregate students",
            "enrollment_key": KEY,
            "source_precedence": "Verified Harvard Dataverse value first; fill its missing fields from the expanded source",
            "outcome_policy": "Outcomes excluded from unsupervised/deep data; certification allowed only as supervised target",
        }, handle, indent=2)
    audit = {
        "raw_rows": int(sum(row["records"] for row in source_rows)), "source_cleaning": source_rows,
        "cross_source_rows_removed": int(removed), "cleaned_enrollments": int(len(enrollments)),
        "cleaned_students": int(len(students)), "student_columns": students.columns.tolist(),
        "invalid_supervised_enrollments": int((~audited["eligible_for_supervised_target"]).sum()),
    }
    with open(os.path.join(PROCESSED, "cleaning_audit.json"), "w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False)
    with open(os.path.join(PROCESSED, "cleaning_summary.md"), "w", encoding="utf-8") as handle:
        handle.write(f"# Cleaning summary\n\nSources were cleaned separately before reconciliation. {audit['raw_rows']:,} raw rows became {len(enrollments):,} enrollment rows and {len(students):,} student rows.\n")
    append_processing_log(LOG, [
        {"step": "3", "operation": "source_cleaning", "rows_in": row["records"], "rows_out": row["records"], "details": row["source_file"]}
        for row in source_rows
    ] + [{"step": "3", "operation": "reconcile_and_aggregate", "rows_in": audit["raw_rows"], "rows_out": len(students), "details": f"{len(enrollments)} cleaned enrollments"}])
    print(f"[+] Step 3 complete: sources cleaned first, then merged to {len(enrollments):,} enrollments and {len(students):,} students.")


if __name__ == "__main__":
    run_data_cleaning()
