"""การจัดเตรียมข้อมูล MOOC สำหรับไปป์ไลน์การทำนายระดับนักศึกษาที่ผ่านการตรวจสอบความถูกต้อง."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from src.deployment import DataLeakageSecurityException, InputSchemaError
from src.step3_data_cleaning import (
    aggregate_features_to_student_level,
    clean_features_record_level,
)

# คอลัมน์ผลลัพธ์ที่ห้ามนำเข้าสู่ข้อมูลการทำนาย
FORBIDDEN_OUTCOMES = {"certified", "grade", "incomplete_flag", "explored"}

# คอลัมน์ข้อมูลดิบระดับรายวิชาที่จำเป็นต้องมี
RAW_REQUIRED_COLUMNS = [
    "institute",
    "course_id",
    "userid_DI",
    "viewed",
    "final_cc_cname_DI",
    "LoE_DI",
    "gender",
    "start_time_DI",
    "last_event_DI",
    "nevents",
    "ndays_act",
    "nplay_video",
    "nchapters",
    "nforum_posts",
    "age",
]

RAW_NUMERIC_COLUMNS = [
    "viewed",
    "nevents",
    "ndays_act",
    "nplay_video",
    "nchapters",
    "nforum_posts",
    "age",
]


def _reject_outcomes(frame: pd.DataFrame) -> None:
    """ปฏิเสธคอลัมน์ผลลัพธ์ปลายทางทันทีเพื่อป้องกันข้อมูลรั่วไหล."""
    leaked = sorted(FORBIDDEN_OUTCOMES.intersection(frame.columns))
    if leaked:
        raise DataLeakageSecurityException(
            f"ห้ามนำคอลัมน์ผลลัพธ์ปลายทางเข้าสู่กระบวนการทำนาย: {leaked}"
        )


def _validate_raw_records(frame: pd.DataFrame) -> None:
    """ตรวจสอบความถูกต้องของโครงสร้างระเบียนข้อมูลดิบ."""
    missing = sorted(set(RAW_REQUIRED_COLUMNS).difference(frame.columns))
    if missing:
        raise InputSchemaError(f"คอลัมน์ข้อมูลดิบที่จำเป็นสูญหาย: {missing}")

    identifiers = frame["userid_DI"]
    if identifiers.isna().any() or identifiers.astype(str).str.strip().eq("").any():
        raise InputSchemaError("userid_DI ต้องไม่เป็นค่าว่างสำหรับทุกแถวข้อมูลดิบ")

    for column in RAW_NUMERIC_COLUMNS:
        if not is_numeric_dtype(frame[column]):
            raise InputSchemaError(
                f"คอลัมน์ข้อมูลดิบ '{column}' ต้องเป็นตัวเลข แต่พบประเภท {frame[column].dtype}"
            )
        if np.isinf(frame[column].to_numpy(dtype=float, na_value=np.nan)).any():
            raise InputSchemaError(f"คอลัมน์ข้อมูลดิบ '{column}' มีค่าที่เป็นอนันต์")

    if not frame["viewed"].dropna().isin([0, 1]).all():
        raise InputSchemaError("คอลัมน์ข้อมูลดิบ 'viewed' ต้องมีค่าเฉพาะ 0 หรือ 1 เท่านั้น")
    for column in ["nevents", "ndays_act", "nchapters", "nforum_posts"]:
        if (frame[column].dropna() < 0).any():
            raise InputSchemaError(f"คอลัมน์กิจกรรม '{column}' ต้องไม่มีค่าติดลบ")
    invalid_video = (frame["nplay_video"].dropna() < 0) & (
        frame["nplay_video"].dropna() != 197757
    )
    if invalid_video.any():
        raise InputSchemaError(
            "คอลัมน์ 'nplay_video' ต้องไม่ติดลบ และรองรับเฉพาะ 197757 เป็นค่าแทนสูญหายเท่านั้น"
        )


def prepare_prediction_input(
    frame: pd.DataFrame,
    pipeline,
    input_mode: str = "auto",
) -> tuple[pd.DataFrame, dict]:
    """จัดเตรียมโปรไฟล์นักศึกษาที่ถูกต้องตาม Schema และส่งคืนผลการตรวจสอบ.

    โหมดการทำงาน:
    - ``student_profile``: ข้อมูล 1 แถวต่อนักศึกษา 1 คน ตรงตามสคีมาการติดตั้งใช้งาน
    - ``raw_records``: ข้อมูลระดับคน-รายวิชาที่ต้องผ่านการทำความสะอาดและรวมตามกฎขั้นตอนที่ 3
    - ``auto``: ตรวจจับโหมดที่เหมาะสมโดยอัตโนมัติจากคอลัมน์ที่มีอยู่
    """
    if frame.empty:
        raise InputSchemaError("ข้อมูลนำเข้าสำหรับการทำนายว่างเปล่า")
    _reject_outcomes(frame)

    profile_columns = {"userid_DI", *pipeline.required_input_features}
    raw_columns = set(RAW_REQUIRED_COLUMNS)

    if input_mode == "auto":
        if profile_columns.issubset(frame.columns):
            input_mode = "student_profile"
        elif raw_columns.issubset(frame.columns):
            input_mode = "raw_records"
        else:
            missing_profile = sorted(profile_columns.difference(frame.columns))
            missing_raw = sorted(raw_columns.difference(frame.columns))
            raise InputSchemaError(
                "ข้อมูลนำเข้าไม่ตรงกับสคีมาที่รองรับทั้งสองรูปแบบ "
                f"คอลัมน์ระดับโปรไฟล์ที่ขาด: {missing_profile}; คอลัมน์ระดับข้อมูลดิบที่ขาด: {missing_raw}"
            )

    if input_mode == "student_profile":
        prepared = pipeline.validate_student_profiles(frame)
        audit = {
            "input_mode": "student_profile",
            "input_rows": int(len(frame)),
            "output_students": int(len(prepared)),
            "duplicates_removed": 0,
            "invalid_age_records": 0,
            "date_inversion_records": int(prepared["date_inversion_records"].sum()),
        }
        return prepared, audit

    if input_mode != "raw_records":
        raise InputSchemaError(f"ไม่รองรับโหมดนำเข้า: {input_mode}")

    _validate_raw_records(frame)
    cleaned, cleaning_audit = clean_features_record_level(frame)
    prepared = aggregate_features_to_student_level(cleaned)
    prepared = pipeline.validate_student_profiles(prepared)
    audit = {
        "input_mode": "raw_records",
        "input_rows": int(len(frame)),
        "output_students": int(len(prepared)),
        "duplicates_removed": int(cleaning_audit["exact_duplicates_removed"]),
        "invalid_age_records": int(cleaning_audit["invalid_age_count"]),
        "date_inversion_records": int(cleaning_audit["inverted_dates_count"]),
        "video_sentinel_records": int(cleaning_audit["video_sentinel_count"]),
    }
    return prepared, audit
