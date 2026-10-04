"""Verification tests for the audited clean-data layer."""

import hashlib
import json
import os

import pandas as pd


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def project_path(*parts):
    return os.path.join(ROOT, *parts)


def md5(path):
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def test_official_harvard_source_checksum():
    path = project_path("data", "raw", "HXPC13_DI_v3_11-13-2019.csv")
    assert md5(path) == "53419b486c3b19c14d2f06612980f630"


def test_cleaned_enrollment_count_and_date_repair():
    with open(project_path("data", "processed", "cleaning_audit.json"), encoding="utf-8") as handle:
        audit = json.load(handle)
    raw = pd.read_parquet(project_path("data", "processed", "raw_non_outcomes.parquet"))
    cleaned = pd.read_parquet(project_path("data", "processed", "enrollments_cleaned.parquet"))
    assert len(cleaned) == len(raw) == audit["cleaned_enrollments"]
    assert int((cleaned["clean_last_dt"] < cleaned["clean_start_dt"]).fillna(False).sum()) == 0
    assert int(cleaned["date_inversion_flag"].sum()) > 0


def test_student_unit_and_outcome_quarantine():
    students = pd.read_parquet(project_path("data", "processed", "students_cleaned.parquet"))
    assert len(students) == students["userid_DI"].nunique() == 446_766
    for outcome in ["certified", "grade", "viewed", "explored", "incomplete_flag"]:
        assert outcome not in students.columns


def test_missing_gender_is_explicit_unknown():
    cleaned = pd.read_parquet(
        project_path("data", "processed", "enrollments_cleaned.parquet"),
        columns=["gender_clean"],
    )
    assert cleaned["gender_clean"].isna().sum() == 0
    assert cleaned["gender_clean"].eq("Unknown").sum() > 0


def test_every_harmonized_column_has_missing_value_decision():
    decisions = pd.read_csv(project_path("outputs", "tables", "missing_value_decisions.csv"))
    documented = set()
    for value in decisions["column_or_group"].astype(str):
        documented.update(part.strip() for part in value.split("/"))
    required_cleaning_rules = {
        "final_cc_cname_DI", "LoE_DI", "gender", "age", "start_time_DI", "last_event_DI",
        "nevents", "ndays_act", "nplay_video", "nchapters", "nforum_posts",
        "certified", "grade", "viewed", "explored", "incomplete_flag",
    }
    assert required_cleaning_rules.issubset(documented)


def test_definite_outcome_contradictions_removed_only_from_supervised_target_file():
    with open(project_path("data", "processed", "cleaning_audit.json"), encoding="utf-8") as handle:
        audit = json.load(handle)
    audited = pd.read_parquet(project_path("data", "quarantine", "outcome_quality_flags.parquet"))
    eligible = pd.read_parquet(project_path("data", "quarantine", "supervised_outcomes_cleaned.parquet"))
    assert int(audited["certified_below_documented_minimum"].sum()) in (1, 72)
    assert len(audited) - len(eligible) == audit["invalid_supervised_enrollments"]
    assert not eligible["certified_below_documented_minimum"].any()


def test_course_profile_covers_every_offering():
    profile = pd.read_csv(project_path("outputs", "tables", "course_offering_profile.csv"))
    cleaned = pd.read_parquet(project_path("data", "processed", "enrollments_cleaned.parquet"), columns=["userid_DI"])
    assert len(profile) >= 1
    assert profile["enrollments"].sum() == len(cleaned)


def run_all_tests():
    tests = [
        test_official_harvard_source_checksum,
        test_cleaned_enrollment_count_and_date_repair,
        test_student_unit_and_outcome_quarantine,
        test_missing_gender_is_explicit_unknown,
        test_every_harmonized_column_has_missing_value_decision,
        test_definite_outcome_contradictions_removed_only_from_supervised_target_file,
        test_course_profile_covers_every_offering,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
