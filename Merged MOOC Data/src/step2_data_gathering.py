"""Step 2: audit and harmonize each raw source without merging it."""

from __future__ import annotations

import json
import os

import pandas as pd

from src.data_quality_audit import (
    append_processing_log,
    build_source_inventory,
    file_checksum,
    profile_columns,
    profile_value_counts,
)

CONFIG = os.path.join("config", "project_config.json")
INTERIM = os.path.join("data", "interim")
PROCESSED = os.path.join("data", "processed")
TABLES = os.path.join("outputs", "tables")
LOG = os.path.join("outputs", "logs", "data_processing_log.csv")

COMMON_COLUMNS = [
    "source_dataset", "source_priority", "source_record_id", "institute", "course_id", "year", "semester",
    "userid_DI", "viewed", "explored", "certified", "final_cc_cname_DI", "LoE_DI", "gender", "grade",
    "start_time_DI", "last_event_DI", "nevents", "ndays_act", "nplay_video", "nchapters", "nforum_posts",
    "incomplete_flag", "age",
]


def _harmonize_hxpc(frame: pd.DataFrame) -> pd.DataFrame:
    parts = frame["course_id"].astype(str).str.split("/", expand=True)
    institute = parts[0]
    course_id = parts[1]
    term = parts[2]
    
    # Extract year (4 digits)
    year = pd.to_numeric(term.str.extract(r"(\d{4})")[0], errors="coerce")
    
    # Extract semester (letters like Spring, Fall, Summer; default to 'Unknown' if missing instead of NaN)
    semester_extracted = term.str.extract(r"([A-Za-z]+)")[0]
    semester = semester_extracted.fillna("Unknown")
    
    result = pd.DataFrame({
        "source_dataset": "HXPC13_DI_v3_11-13-2019.csv",
        "source_priority": 0,
        "source_record_id": frame.index.astype("int64"),
        "institute": institute,
        "course_id": course_id,
        "year": year,
        "semester": semester,
        "userid_DI": frame["userid_DI"],
        "viewed": frame["viewed"], "explored": frame["explored"], "certified": frame["certified"],
        "final_cc_cname_DI": frame["final_cc_cname_DI"], "LoE_DI": frame["LoE_DI"], "gender": frame["gender"],
        "grade": frame["grade"], "start_time_DI": frame["start_time_DI"], "last_event_DI": frame["last_event_DI"],
        "nevents": frame["nevents"], "ndays_act": frame["ndays_act"], "nplay_video": frame["nplay_video"],
        "nchapters": frame["nchapters"], "nforum_posts": frame["nforum_posts"],
        "incomplete_flag": frame["incomplete_flag"],
        "age": year - pd.to_numeric(frame["YoB"], errors="coerce"),
    })
    return result[COMMON_COLUMNS]


def _harmonize_big(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.drop(columns=["Unnamed: 0"], errors="ignore").copy()
    result.insert(0, "source_record_id", frame.index.astype("int64"))
    result.insert(0, "source_priority", 1)
    result.insert(0, "source_dataset", "big_student_clear_third_version.csv")
    for column in COMMON_COLUMNS:
        if column not in result:
            result[column] = pd.NA
    return result[COMMON_COLUMNS]


def run_data_gathering():
    os.makedirs(INTERIM, exist_ok=True)
    os.makedirs(PROCESSED, exist_ok=True)
    os.makedirs(TABLES, exist_ok=True)
    with open(CONFIG, encoding="utf-8") as handle:
        config = json.load(handle)
    raw_paths = config["raw_data_files"]
    raw_frames = {os.path.basename(path): pd.read_csv(path) for path in raw_paths}

    inventory = build_source_inventory(raw_paths, raw_frames, config.get("data_sources", {}))
    inventory.to_csv(os.path.join(TABLES, "source_file_inventory.csv"), index=False)
    profile_columns(raw_frames).to_csv(os.path.join(TABLES, "raw_column_profile.csv"), index=False)
    profile_value_counts(raw_frames).to_csv(os.path.join(TABLES, "raw_column_value_counts.csv"), index=False)

    hxpc = _harmonize_hxpc(raw_frames["HXPC13_DI_v3_11-13-2019.csv"])
    big = _harmonize_big(raw_frames["big_student_clear_third_version.csv"])
    source_paths = {
        "HXPC13_DI_v3_11-13-2019.csv": os.path.join(INTERIM, "HXPC13_harmonized.parquet"),
        "big_student_clear_third_version.csv": os.path.join(INTERIM, "big_student_harmonized.parquet"),
    }
    hxpc.to_parquet(source_paths["HXPC13_DI_v3_11-13-2019.csv"], index=False)
    big.to_parquet(source_paths["big_student_clear_third_version.csv"], index=False)

    roles = {
        "source_dataset": "provenance", "source_priority": "provenance", "source_record_id": "identifier",
        "institute": "context", "course_id": "context", "year": "context", "semester": "context",
        "userid_DI": "identifier", "final_cc_cname_DI": "demographic", "LoE_DI": "demographic",
        "gender": "demographic", "age": "demographic", "start_time_DI": "temporal", "last_event_DI": "temporal",
        "nevents": "behavior", "ndays_act": "behavior", "nplay_video": "behavior",
        "nchapters": "behavior", "nforum_posts": "behavior",
        "viewed": "outcome", "explored": "outcome", "certified": "outcome", "grade": "outcome",
        "incomplete_flag": "outcome",
    }
    pd.DataFrame([{"column": column, "role": roles[column]} for column in COMMON_COLUMNS]).to_csv(
        os.path.join(PROCESSED, "data_dictionary.csv"), index=False
    )
    provenance = {
        "processing_order": "Audit raw sources -> harmonize each source -> clean each source separately in Step 3 -> reconcile/merge -> aggregate students",
        "raw_records": int(sum(len(frame) for frame in raw_frames.values())),
        "source_count": len(raw_frames),
        "sources": inventory.to_dict(orient="records"),
        "interim_harmonized_files": source_paths,
        "merge_status": "NOT_MERGED_IN_STEP_2",
        "selection_rationale": {name: config["data_sources"][name]["selection_rationale"] for name in raw_frames},
        "limitations": {name: config["data_sources"][name]["known_limitations"] for name in raw_frames},
        "checksums": {path: file_checksum(path) for path in raw_paths},
    }
    with open(os.path.join(PROCESSED, "data_provenance.json"), "w", encoding="utf-8") as handle:
        json.dump(provenance, handle, indent=2, ensure_ascii=False)
    append_processing_log(LOG, [
        {"step": "2", "operation": "raw_source_audit", "rows_in": len(raw_frames[name]), "rows_out": len(raw_frames[name]), "details": name}
        for name in raw_frames
    ] + [
        {"step": "2", "operation": "harmonize_without_merge", "rows_in": len(hxpc) + len(big), "rows_out": len(hxpc) + len(big), "details": "Two interim source tables retained separately"}
    ])
    print(f"[+] Step 2 complete: {len(hxpc) + len(big):,} rows audited and harmonized; sources remain separate.")


if __name__ == "__main__":
    run_data_gathering()
