"""Reusable data-quality audit helpers for the MOOC data layer.

The raw files remain immutable.  This module writes compact, reviewable audit
tables that describe every source column without creating enormous value-count
files for identifiers and other high-cardinality fields.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping

import numpy as np
import pandas as pd


def file_checksum(path: str, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def _json_examples(series: pd.Series, limit: int = 5) -> str:
    examples = series.dropna().astype(str).drop_duplicates().head(limit).tolist()
    return json.dumps(examples, ensure_ascii=False)


def _numeric_summary(series: pd.Series) -> Mapping[str, float]:
    numeric = pd.to_numeric(series, errors="coerce")
    numeric_non_null = numeric.dropna()
    if numeric_non_null.empty:
        return {
            "numeric_parse_rate": 0.0,
            "zero_count": 0,
            "negative_count": 0,
            "minimum": np.nan,
            "median": np.nan,
            "mean": np.nan,
            "maximum": np.nan,
        }
    return {
        "numeric_parse_rate": float(numeric.notna().mean()),
        "zero_count": int(numeric_non_null.eq(0).sum()),
        "negative_count": int(numeric_non_null.lt(0).sum()),
        "minimum": float(numeric_non_null.min()),
        "median": float(numeric_non_null.median()),
        "mean": float(numeric_non_null.mean()),
        "maximum": float(numeric_non_null.max()),
    }


def profile_columns(raw_frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Return one quality-profile row for every source column."""
    rows: List[dict] = []
    for source_name, frame in raw_frames.items():
        row_count = len(frame)
        for position, column in enumerate(frame.columns, start=1):
            series = frame[column]
            missing_count = int(series.isna().sum())
            numeric = _numeric_summary(series)
            rows.append(
                {
                    "source_file": source_name,
                    "column_position": position,
                    "column_name": column,
                    "raw_dtype": str(series.dtype),
                    "records": row_count,
                    "non_missing_count": int(series.notna().sum()),
                    "missing_count": missing_count,
                    "missing_percent": (missing_count / row_count * 100.0) if row_count else 0.0,
                    "distinct_non_missing": int(series.nunique(dropna=True)),
                    "numeric_parse_rate": numeric["numeric_parse_rate"],
                    "zero_count": numeric["zero_count"],
                    "negative_count": numeric["negative_count"],
                    "minimum": numeric["minimum"],
                    "median": numeric["median"],
                    "mean": numeric["mean"],
                    "maximum": numeric["maximum"],
                    "example_values": _json_examples(series),
                }
            )
    return pd.DataFrame(rows)


def profile_value_counts(
    raw_frames: Mapping[str, pd.DataFrame],
    full_cardinality_limit: int = 100,
    top_n: int = 20,
) -> pd.DataFrame:
    """Profile category/class counts for every column.

    Low-cardinality columns retain every class.  High-cardinality columns retain
    the top values, an OTHER row, and an explicit MISSING row.  This keeps the
    audit complete at the column level without exporting hundreds of thousands
    of student IDs.
    """
    rows: List[dict] = []
    for source_name, frame in raw_frames.items():
        total = len(frame)
        for column in frame.columns:
            series = frame[column]
            non_missing_counts = series.dropna().astype(str).value_counts(dropna=False)
            cardinality = len(non_missing_counts)
            keep_all = cardinality <= full_cardinality_limit
            selected = non_missing_counts if keep_all else non_missing_counts.head(top_n)
            coverage = "all_values" if keep_all else f"top_{top_n}_plus_other"
            for rank, (value, count) in enumerate(selected.items(), start=1):
                rows.append(
                    {
                        "source_file": source_name,
                        "column_name": column,
                        "value": value,
                        "count": int(count),
                        "percent": (int(count) / total * 100.0) if total else 0.0,
                        "rank": rank,
                        "coverage": coverage,
                    }
                )
            if not keep_all:
                other_count = int(non_missing_counts.iloc[top_n:].sum())
                rows.append(
                    {
                        "source_file": source_name,
                        "column_name": column,
                        "value": "<OTHER_VALUES>",
                        "count": other_count,
                        "percent": (other_count / total * 100.0) if total else 0.0,
                        "rank": top_n + 1,
                        "coverage": coverage,
                    }
                )
            missing_count = int(series.isna().sum())
            rows.append(
                {
                    "source_file": source_name,
                    "column_name": column,
                    "value": "<MISSING>",
                    "count": missing_count,
                    "percent": (missing_count / total * 100.0) if total else 0.0,
                    "rank": 0,
                    "coverage": coverage,
                }
            )
    return pd.DataFrame(rows)


def build_source_inventory(
    raw_paths: Iterable[str],
    raw_frames: Mapping[str, pd.DataFrame],
    source_metadata: Mapping[str, Mapping[str, object]],
) -> pd.DataFrame:
    rows: List[dict] = []
    for path in raw_paths:
        filename = os.path.basename(path)
        frame = raw_frames[filename]
        metadata = source_metadata.get(filename, {})
        expected_md5 = metadata.get("expected_md5")
        local_md5 = file_checksum(path, "md5")

        if {"userid_DI", "institute", "course_id", "year", "semester"}.issubset(frame.columns):
            enrollment_key = ["userid_DI", "institute", "course_id", "year", "semester"]
            offerings = frame[["institute", "course_id", "year", "semester"]].drop_duplicates().shape[0]
        elif {"userid_DI", "course_id"}.issubset(frame.columns):
            enrollment_key = ["userid_DI", "course_id"]
            offerings = frame["course_id"].nunique(dropna=True)
        else:
            enrollment_key = []
            offerings = np.nan

        rows.append(
            {
                "filename": filename,
                "local_path": path,
                "source_url": metadata.get("source_url", ""),
                "source_title": metadata.get("source_title", ""),
                "source_authority": metadata.get("source_authority", ""),
                "source_verification": metadata.get("source_verification", ""),
                "selection_rationale": metadata.get("selection_rationale", ""),
                "known_limitations": metadata.get("known_limitations", ""),
                "records": len(frame),
                "columns": frame.shape[1],
                "exact_duplicate_rows": int(frame.duplicated().sum()),
                "duplicate_enrollment_rows": int(frame.duplicated(subset=enrollment_key, keep=False).sum()) if enrollment_key else np.nan,
                "unique_students": int(frame["userid_DI"].nunique(dropna=True)) if "userid_DI" in frame else np.nan,
                "distinct_course_offerings": int(offerings) if pd.notna(offerings) else np.nan,
                "file_size_bytes": os.path.getsize(path),
                "sha256": file_checksum(path, "sha256"),
                "md5": local_md5,
                "expected_md5": expected_md5 or "",
                "checksum_matches_published_source": bool(expected_md5 and local_md5 == expected_md5),
            }
        )
    return pd.DataFrame(rows)


def append_processing_log(path: str, entries: Iterable[Mapping[str, object]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    incoming = pd.DataFrame([{**entry, "timestamp_utc": timestamp} for entry in entries])
    if os.path.exists(path):
        existing = pd.read_csv(path)
        combined = pd.concat([existing, incoming], ignore_index=True)
    else:
        combined = incoming
    combined.to_csv(path, index=False)

