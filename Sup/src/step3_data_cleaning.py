"""ขั้นตอนที่ 3: การทำความสะอาดข้อมูลและการรวมข้อมูลระดับนักศึกษา (ป้องกันข้อมูลรั่วไหลอย่างเคร่งครัด)."""

import json
import os
import numpy as np
import pandas as pd

RAW_FEATURES_PATH = os.path.join("data", "processed", "raw_features.parquet")
RAW_TARGETS_PATH = os.path.join("data", "labels", "raw_targets.parquet")
OUTPUT_STUDENTS_PATH = os.path.join("data", "processed", "students_cleaned.parquet")
OUTPUT_LABELS_PATH = os.path.join("data", "labels", "student_labels.parquet")
RULES_PATH = os.path.join("data", "processed", "cleaning_rules.json")
AUDIT_PATH = os.path.join("data", "processed", "cleaning_audit.json")
CONFIG_PATH = os.path.join("config", "project_config.json")

# ลำดับชั้นระดับการศึกษาสำหรับการแปลงเป็นตัวเลขเปรียบเทียบ
LOE_HIERARCHY = {
    "Doctorate": 5,
    "Master's": 4,
    "Bachelor's": 3,
    "Secondary": 2,
    "Less than Secondary": 1,
    "Unknown": 0,
}
LOE_REVERSE = {v: k for k, v in LOE_HIERARCHY.items()}


def clean_features_record_level(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """ทำความสะอาดข้อมูลฟีเจอร์ในระดับแถวลงทะเบียน: จัดการค่าผิดปกติ ค่า Sentinel และประเภทข้อมูล."""
    print("[+] กำลังทำความสะอาดข้อมูลระดับระเบียน: ค่าผิดปกติ ค่าแทนสูญหาย และประเภทข้อมูล...")
    df = df.copy()
    rows_before = len(df)

    substantive_columns = [col for col in df.columns if col != "Unnamed: 0"]
    exact_duplicate_mask = df.duplicated(subset=substantive_columns, keep="first")
    exact_duplicate_count = int(exact_duplicate_mask.sum())
    df = df.loc[~exact_duplicate_mask].copy()

    # จัดการค่า Sentinel ใน nplay_video (197757 เป็นค่า placeholder ในชุดข้อมูลส่งออกจาก Kaggle)
    sentinel_mask = df["nplay_video"] == 197757
    sentinel_count = int(sentinel_mask.sum())
    df["nplay_video_clean"] = df["nplay_video"].mask(sentinel_mask, np.nan)
    df["nplay_video_missing"] = df["nplay_video_clean"].isna().astype("int8")

    # ตรวจสอบและทำความสะอาดอายุ (ตัดค่า <= 0 หรือ > 100 เป็น NaN)
    invalid_age_mask = (df["age"] <= 0) | (df["age"] > 100)
    invalid_age_count = int(invalid_age_mask.sum())
    df["age_clean"] = df["age"].mask(invalid_age_mask, np.nan)
    df["age_missing"] = df["age_clean"].isna().astype("int8")

    # ทำความสะอาดข้อมูลข้อความ (ตัดช่องว่าง แปลงเป็นตัวพิมพ์เล็ก กำหนด Unknown หากเป็นค่าว่าง)
    missing_gender_count = int(df["gender"].isnull().sum())
    df["gender_clean"] = df["gender"].fillna("Unknown").astype(str).str.strip().str.lower()
    df["LoE_clean"] = df["LoE_DI"].fillna("Unknown").astype(str).str.strip()
    df["country_clean"] = df["final_cc_cname_DI"].fillna("Unknown").astype(str).str.strip()

    # ตรวจสอบข้อมูลวันที่และสลับลำดับเวลาผิดปกติ
    df["start_dt"] = pd.to_datetime(df["start_time_DI"], errors="coerce")
    df["last_dt"] = pd.to_datetime(df["last_event_DI"], errors="coerce")
    inverted_dates = df["last_dt"] < df["start_dt"]
    inverted_count = int(inverted_dates.sum())

    df["date_inversion_flag"] = inverted_dates.astype("int8")
    df["valid_start_dt"] = df["start_dt"].mask(inverted_dates)
    df["valid_last_dt"] = df["last_dt"].mask(inverted_dates)

    audit = {
        "rows_before_cleaning": rows_before,
        "rows_after_cleaning": len(df),
        "exact_duplicates_removed": exact_duplicate_count,
        "video_sentinel_count": sentinel_count,
        "video_sentinel_pct": float(round(sentinel_count / len(df) * 100, 2)),
        "invalid_age_count": invalid_age_count,
        "invalid_age_pct": float(round(invalid_age_count / len(df) * 100, 3)),
        "inverted_dates_count": inverted_count,
        "inverted_dates_pct": float(round(inverted_count / len(df) * 100, 3)),
        "missing_gender_count": missing_gender_count,
        "missing_gender_pct": float(round(missing_gender_count / len(df) * 100, 2)),
    }
    return df, audit


def aggregate_features_to_student_level(df: pd.DataFrame) -> pd.DataFrame:
    """รวมข้อมูลฟีเจอร์ให้อยู่ในระดับหน่วยวิเคราะห์นักศึกษา 1 คน (userid_DI)."""
    print("[+] กำลังรวมฟีเจอร์ให้อยู่ในระดับนักศึกษา (userid_DI)...")
    df["loe_rank"] = df["LoE_clean"].map(LOE_HIERARCHY).fillna(0)
    grouped = df.groupby("userid_DI")

    counts = grouped["course_id"].agg(n_courses="count", unique_courses="nunique")
    inst = grouped["institute"].agg(n_institutes="nunique")
    dates = grouped.agg(
        first_start_dt=("valid_start_dt", "min"),
        last_event_dt=("valid_last_dt", "max"),
        date_inversion_records=("date_inversion_flag", "sum"),
    )
    viewed = grouped["viewed"].agg(total_courses_viewed="sum", view_rate="mean")
    events = grouped["nevents"].agg(
        total_events="sum",
        mean_events_per_course="mean",
        max_events_single_course="max",
    )
    days = grouped["ndays_act"].agg(
        total_active_days="sum",
        mean_active_days_per_course="mean",
        max_active_days_single_course="max",
    )
    videos = grouped["nplay_video_clean"].agg(
        total_video_plays=lambda values: values.sum(min_count=1),
        mean_video_plays_per_course="mean",
    )
    video_availability = grouped["nplay_video_missing"].agg(
        video_missing_records="sum",
        video_data_available_rate=lambda values: 1.0 - values.mean(),
    )
    chapters = grouped["nchapters"].agg(
        total_chapters="sum",
        mean_chapters_per_course="mean",
        max_chapters_single_course="max",
    )
    forum = grouped["nforum_posts"].agg(total_forum_posts="sum")
    demog_age = grouped["age_clean"].agg(age="median")
    age_availability = grouped["age_missing"].agg(age_missing_records="sum")
    demog_loe = grouped["loe_rank"].agg(max_loe_rank="max")
    demog_gender = grouped["gender_clean"].agg(
        gender=lambda s: s.iloc[0] if (s == s.iloc[0]).all() else s.mode().iloc[0]
    )
    demog_country = grouped["country_clean"].agg(
        country=lambda s: s.iloc[0] if (s == s.iloc[0]).all() else s.mode().iloc[0]
    )

    students = pd.concat([
        counts, inst, dates, viewed, events, days, videos, video_availability,
        chapters, forum, demog_age, age_availability, demog_loe,
        demog_gender, demog_country
    ], axis=1).reset_index()

    students["LoE_DI"] = students["max_loe_rank"].map(LOE_REVERSE).fillna("Unknown")
    students.drop(columns=["max_loe_rank"], inplace=True)

    # ฟีเจอร์เชิงประกอบ (Composite Behavioral Features)
    students["overall_span_days"] = (
        students["last_event_dt"] - students["first_start_dt"]
    ).dt.days.astype("float64")
    students["overall_span_missing"] = students["overall_span_days"].isna().astype("int8")
    students["overall_span_days"] = students["overall_span_days"].fillna(0.0)

    students["event_intensity"] = students["total_events"] / np.maximum(students["total_active_days"], 1)
    clean_video_plays = students["total_video_plays"].fillna(0)
    students["video_play_ratio"] = clean_video_plays / np.maximum(students["total_events"], 1)
    students["chapter_intensity"] = students["total_chapters"] / np.maximum(students["total_active_days"], 1)
    students["has_forum_activity"] = (students["total_forum_posts"] > 0).astype("int8")
    students["has_multiple_courses"] = (students["n_courses"] > 1).astype("int8")

    students.drop(columns=["first_start_dt", "last_event_dt"], inplace=True)
    return students


def aggregate_targets_to_student_level(df_targets: pd.DataFrame) -> pd.DataFrame:
    """รวมตัวแปรเป้าหมายให้อยู่ในระดับนักศึกษา (หากได้ใบจบในวิชาใดวิชาหนึ่ง ถือว่า certified = 1)."""
    print("[+] กำลังรวมเลเบลผลลัพธ์ให้อยู่ในระดับนักศึกษา...")
    grouped = df_targets.groupby("userid_DI")
    target_agg = grouped.agg(
        certified_student=("certified", "max"),
        explored_student=("explored", "max"),
        max_grade=("grade", "max"),
        incomplete_any=("incomplete_flag", "max"),
    ).reset_index()

    target_agg["certified_student"] = target_agg["certified_student"].astype(int)
    target_agg["explored_student"] = target_agg["explored_student"].astype(int)

    # จำแนกกลุ่มผลลัพธ์ 3 ระดับสำหรับการวางแผนสนับสนุน:
    # Tier 1: ผู้ได้รับใบประกาศนียบัตร (certified == 1)
    # Tier 2: ผู้เข้าเรียนลึกซึ้งแต่ไม่จบ (certified == 0 และ explored == 1)
    # Tier 3: ผู้มีส่วนร่วมน้อย / ออกกลางคัน (certified == 0 และ explored == 0)
    conditions = [
        target_agg["certified_student"] == 1,
        (target_agg["certified_student"] == 0) & (target_agg["explored_student"] == 1),
    ]
    choices = [1, 2]
    target_agg["outcome_tier"] = np.select(conditions, choices, default=3)

    return target_agg


def run_data_cleaning():
    """ดำเนินกระบวนการทำความสะอาดข้อมูลและรวมผลในระดับนักศึกษา."""
    print("=" * 70)
    print("ขั้นตอนที่ 3: การทำความสะอาดข้อมูลและการรวมระดับนักศึกษา")
    print("=" * 70)

    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)

    # นำเข้าฟีเจอร์และเลเบลที่แยกกักกันไว้
    df_raw_features = pd.read_parquet(RAW_FEATURES_PATH)
    df_raw_targets = pd.read_parquet(RAW_TARGETS_PATH)

    # 1. ทำความสะอาดข้อมูลระดับระเบียน
    df_features_clean, audit_info = clean_features_record_level(df_raw_features)

    # 2. รวมฟีเจอร์ระดับนักศึกษา
    df_students = aggregate_features_to_student_level(df_features_clean)

    # 3. รวมตัวแปรเป้าหมายระดับนักศึกษา
    df_labels = aggregate_targets_to_student_level(df_raw_targets)

    # ตรวจสอบความสอดคล้องของรหัสนักศึกษา
    student_keys = set(df_students["userid_DI"])
    label_keys = set(df_labels["userid_DI"])
    assert student_keys == label_keys, "รหัสนักศึกษาในฟีเจอร์และเลเบลไม่ตรงกัน!"

    # จัดเรียงลำดับแถวให้ตรงกันอย่างสมบูรณ์
    df_students.sort_values("userid_DI", inplace=True)
    df_labels.sort_values("userid_DI", inplace=True)
    df_students.reset_index(drop=True, inplace=True)
    df_labels.reset_index(drop=True, inplace=True)

    # ตรวจสอบความปลอดภัยป้องกันข้อมูลรั่วไหลอย่างเข้มงวด
    forbidden_outcomes = config["outcome_columns"]
    for out in forbidden_outcomes:
        assert out not in df_students.columns, f"ข้อผิดพลาดร้ายแรง: พบตัวแปรผลลัพธ์ {out} ในที่เก็บฟีเจอร์!"

    print(f"[+] จำนวนนักศึกษาที่ผ่านการทำความสะอาดทั้งหมด: {len(df_students):,} คน")
    pos_count = int(df_labels["certified_student"].sum())
    total_count = len(df_labels)
    pos_rate = pos_count / total_count * 100
    print(f"    คลาสบวก (ผู้ได้รับใบประกาศนียบัตร): {pos_count:,} คน ({pos_rate:.2f}%)")
    print(f"    คลาสลบ (ผู้ไม่ได้รับใบจบ):           {total_count - pos_count:,} คน ({100 - pos_rate:.2f}%)")

    tier_dist = df_labels["outcome_tier"].value_counts().to_dict()
    print(f"    กลุ่มผลลัพธ์ 3 กลุ่ม: Tier 1 (สำเร็จ)={tier_dist.get(1, 0):,}, "
          f"Tier 2 (เข้าเรียนลึกซึ้ง)={tier_dist.get(2, 0):,}, "
          f"Tier 3 (ออกกลางคัน)={tier_dist.get(3, 0):,}")

    # บันทึกไฟล์ข้อมูลที่ทำความสะอาดแล้ว
    df_students.to_parquet(OUTPUT_STUDENTS_PATH, index=False)
    df_labels.to_parquet(OUTPUT_LABELS_PATH, index=False)
    print(f"[+] บันทึกฟีเจอร์นักศึกษาที่ทำความสะอาดแล้วที่: {OUTPUT_STUDENTS_PATH}")
    print(f"[+] บันทึกเลเบลผลลัพธ์นักศึกษาที่:             {OUTPUT_LABELS_PATH}")

    cleaning_rules = {
        "duplicate_records": "ลบระเบียนข้อมูลซ้ำซ้อนโดยเก็บแถวแรกไว้",
        "video_sentinel": "แปลงค่า 197757 ใน nplay_video เป็น NaN และสร้างตัวแปรอัตราความพร้อมของข้อมูลวิดีโอ",
        "age_sanitization": "แปลงอายุที่ผิดปกติ (<=0 หรือ >100) เป็น NaN พร้อมสร้างตัวบ่งชี้ age_missing",
        "date_coercion": "แปลงวันเวลาที่บันทึก ตรวจจับกรณีวันสลับลำดับ และคำนวณช่วงเวลาการเข้าเรียนทั้งหมด",
        "categorical_standardization": "ตัดช่องว่างข้อความและแทนที่ค่าสูญหายด้วย 'Unknown'",
        "student_aggregation": "รวมข้อมูลเหตุการณ์การเรียนระดับรายวิชาเป็นโปรไฟล์นักศึกษา 1 คน ต่อ 1 แถว",
        "target_aggregation": "รวมสถานะการได้รับใบจบระดับนักศึกษา: certified_student = max(certified)",
        "leakage_safeguard": "ตรวจสอบยืนยันว่าไม่มีตัวแปรผลลัพธ์ปลายทางหลุดเข้าไปในชุดฟีเจอร์ X",
    }
    with open(RULES_PATH, "w", encoding="utf-8") as handle:
        json.dump(cleaning_rules, handle, indent=2, ensure_ascii=False)

    audit_summary = {
        "record_level": audit_info,
        "student_level": {
            "total_students": len(df_students),
            "certified_completers": pos_count,
            "completion_rate_pct": float(round(pos_rate, 3)),
            "tier_1_completers": int(tier_dist.get(1, 0)),
            "tier_2_explored_noncompleters": int(tier_dist.get(2, 0)),
            "tier_3_disengaged_dropouts": int(tier_dist.get(3, 0)),
            "feature_count": len(df_students.columns) - 1,
        },
    }
    with open(AUDIT_PATH, "w", encoding="utf-8") as handle:
        json.dump(audit_summary, handle, indent=2, ensure_ascii=False)

    print(f"[+] บันทึกรายงานการตรวจสอบและกฎการทำความสะอาดที่: {AUDIT_PATH} และ {RULES_PATH}")


if __name__ == "__main__":
    run_data_cleaning()
