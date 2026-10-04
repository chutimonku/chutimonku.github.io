"""ขั้นตอนที่ 2: การรวบรวมข้อมูลและการแยกเลเบลเป้าหมายเพื่อป้องกันข้อมูลรั่วไหล (Anti-Leakage)."""

import hashlib
import json
import os
import pandas as pd

CONFIG_PATH = os.path.join("config", "project_config.json")
LABELS_DIR = os.path.join("data", "labels")
PROCESSED_DIR = os.path.join("data", "processed")


def catalog_fields(df: pd.DataFrame) -> dict:
    """จัดทำพจนานุกรมฟิลด์ข้อมูล กำหนดประเภท บทบาทในการวิเคราะห์ และคำอธิบาย."""
    field_catalog = {
        "Unnamed: 0": {"type": "integer", "role": "metadata_index", "description": "ดัชนีแถวดั้งเดิมของการส่งออกไฟล์"},
        "institute": {"type": "categorical", "role": "course_context", "description": "สถาบันผู้จัดการเรียนการสอน (HarvardX, MITx)"},
        "course_id": {"type": "categorical", "role": "course_context", "description": "รหัสประจำรายวิชา (เช่น 6.00x, CS50x)"},
        "year": {"type": "integer", "role": "course_context", "description": "ปีการศึกษา (2012, 2013)"},
        "semester": {"type": "categorical", "role": "course_context", "description": "ภาคการศึกษา (Spring, Fall, Summer)"},
        "userid_DI": {"type": "string", "role": "entity_identifier", "description": "รหัสประจำตัวนักศึกษาที่ผ่านการปกปิดตัวตน"},
        "viewed": {"type": "binary", "role": "observational_engagement", "description": "1 หากนักศึกษาเคยเข้าดูเนื้อหาในรายวิชา"},
        "explored": {"type": "binary", "role": "target_auxiliary_label", "description": "ตัวแปรเป้าหมายเสริม: 1 หากเข้าเรียน >= 50% ของบทเรียนทั้งหมด"},
        "certified": {"type": "binary", "role": "target_primary_label", "description": "ตัวแปรเป้าหมายหลัก: 1 หากสำเร็จการศึกษาและได้รับใบประกาศนียบัตร"},
        "final_cc_cname_DI": {"type": "categorical", "role": "demographic", "description": "ประเทศต้นทางของนักศึกษา"},
        "LoE_DI": {"type": "categorical", "role": "demographic", "description": "ระดับการศึกษาสูงสุดของนักศึกษา"},
        "gender": {"type": "categorical", "role": "demographic", "description": "เพศสภาพของนักศึกษา (m, f, o, null)"},
        "grade": {"type": "float", "role": "target_auxiliary_label", "description": "ตัวแปรเป้าหมายเสริม: เกรดหรือคะแนนเฉลี่ยสุดท้ายที่ได้ (0.0 ถึง 1.0)"},
        "start_time_DI": {"type": "date", "role": "temporal_metadata", "description": "เวลาที่ลงทะเบียนเข้าเรียนครั้งแรก"},
        "last_event_DI": {"type": "date", "role": "temporal_metadata", "description": "เวลาที่มีปฏิสัมพันธ์ครั้งสุดท้าย"},
        "nevents": {"type": "integer", "role": "observational_engagement", "description": "จำนวนเหตุการณ์ปฏิสัมพันธ์ทั้งหมดที่บันทึกได้"},
        "ndays_act": {"type": "integer", "role": "observational_engagement", "description": "จำนวนวันที่มีการเข้าใช้งานแพลตฟอร์ม"},
        "nplay_video": {"type": "integer", "role": "observational_engagement", "description": "จำนวนครั้งที่เปิดดูวิดีโอ (มีค่า sentinel 197757)"},
        "nchapters": {"type": "integer", "role": "observational_engagement", "description": "จำนวนบทเรียนหรือโมดูลที่เข้าเรียน"},
        "nforum_posts": {"type": "integer", "role": "observational_engagement", "description": "จำนวนโพสต์ในเว็บบอร์ดกระดานสนทนา"},
        "incomplete_flag": {"type": "binary", "role": "target_auxiliary_label", "description": "ตัวแปรเป้าหมายเสริม: ตัวบ่งชี้สถานะเรียนไม่จบ"},
        "age": {"type": "integer", "role": "demographic", "description": "อายุของนักศึกษา"},
    }

    summary = {}
    for col in df.columns:
        summary[col] = {
            "catalog_info": field_catalog.get(col, {"type": "unknown", "role": "unknown", "description": "ไม่ได้ระบุในพจนานุกรม"}),
            "actual_dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_percentage": float(round(df[col].isnull().mean() * 100, 3)),
            "unique_values": int(df[col].nunique()),
        }
    return summary


def get_file_sha256(filepath: str) -> str:
    """คำนวณค่าแฮช SHA-256 ของไฟล์ข้อมูลดิบเพื่อการตรวจสอบย้อนกลับ (Data Provenance)."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_data_gathering():
    """นำเข้าข้อมูลดิบ ตรวจสอบความถูกต้อง และแยกคอลัมน์ผลลัพธ์เพื่อป้องกันข้อมูลรั่วไหลอย่างเคร่งครัด."""
    print("=" * 70)
    print("ขั้นตอนที่ 2: การรวบรวมข้อมูลและการแยกเลเบลเป้าหมาย (Anti-Leakage)")
    print("=" * 70)

    os.makedirs(LABELS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)

    raw_data_path = config["raw_data_path"]
    outcome_columns = config["outcome_columns"]
    unit_column = config["unit_of_analysis"]
    course_column = config["course_identifier"]

    if not os.path.exists(raw_data_path):
        raise FileNotFoundError(f"ไม่พบไฟล์ชุดข้อมูลดิบที่: {raw_data_path}")

    print(f"[+] กำลังนำเข้าข้อมูลดิบจาก: {raw_data_path}")
    df_raw = pd.read_csv(raw_data_path)

    missing_columns = sorted(set(config["expected_raw_columns"]).difference(df_raw.columns))
    unexpected_columns = sorted(set(df_raw.columns).difference(config["expected_raw_columns"]))
    if missing_columns or unexpected_columns:
        raise ValueError(
            "โครงสร้างข้อมูลดิบไม่ตรงกับ config/project_config.json "
            f"คอลัมน์ที่ขาด={missing_columns}; คอลัมน์ที่ไม่คาดคิด={unexpected_columns}"
        )

    total_records = len(df_raw)
    total_cols = len(df_raw.columns)
    unique_students = df_raw[unit_column].nunique()

    print(f"    จำนวนระเบียนข้อมูลดิบ: {total_records:,} แถว")
    print(f"    จำนวนคอลัมน์ดิบ:       {total_cols} คอลัมน์")
    print(f"    จำนวนนักศึกษาที่ไม่ซ้ำกัน: {unique_students:,} คน")
    print(f"    อัตราส่วนการลงทะเบียน:  {total_records / unique_students:.3f} รายวิชา/คน")

    raw_hash = get_file_sha256(raw_data_path)
    file_size_mb = os.path.getsize(raw_data_path) / (1024 * 1024)

    field_summary = catalog_fields(df_raw)

    dict_rows = []
    for col, info in field_summary.items():
        dict_rows.append({
            "column_name": col,
            "logical_type": info["catalog_info"]["type"],
            "analytical_role": info["catalog_info"]["role"],
            "is_target_variable": col in outcome_columns,
            "actual_dtype": info["actual_dtype"],
            "null_count": info["null_count"],
            "null_pct": info["null_percentage"],
            "unique_values": info["unique_values"],
            "description": info["catalog_info"]["description"],
        })
    df_dict = pd.DataFrame(dict_rows)
    dict_path = os.path.join(PROCESSED_DIR, "data_dictionary.csv")
    df_dict.to_csv(dict_path, index=False)
    print(f"[+] บันทึกพจนานุกรมข้อมูล (Data Dictionary) เรียบร้อยที่: {dict_path}")

    # การแยกตัวแปรเพื่อป้องกันข้อมูลรั่วไหล (Anti-Leakage Separation)
    print("[+] ดำเนินการแยกตัวแปรผลลัพธ์ออกจากฟีเจอร์นำเข้าเพื่อความปลอดภัยสูงสุด...")
    non_target_cols = [c for c in df_raw.columns if c not in outcome_columns]

    df_features = df_raw[non_target_cols].copy()
    raw_features_path = os.path.join(PROCESSED_DIR, "raw_features.parquet")
    df_features.to_parquet(raw_features_path, index=False)
    print(f"    ฟีเจอร์ตั้งต้นที่ไม่รวมผลลัพธ์ ({len(non_target_cols)} คอลัมน์) -> {raw_features_path}")

    # จัดเก็บคอลัมน์ผลลัพธ์ในพื้นที่กักกันที่แยกต่างหาก
    target_cols = [unit_column, course_column] + outcome_columns
    df_targets = df_raw[target_cols].copy()
    raw_targets_path = os.path.join(LABELS_DIR, "raw_targets.parquet")
    df_targets.to_parquet(raw_targets_path, index=False)
    print(f"    เลเบลผลลัพธ์ความจริงพื้นฐาน ({len(target_cols)} คอลัมน์) -> {raw_targets_path}")

    # ตรวจสอบยืนยันความปลอดภัยว่าไม่มีตัวแปรผลลัพธ์หลุดเข้าไปในที่เก็บฟีเจอร์
    for col in outcome_columns:
        assert col not in df_features.columns, f"เกิดการรั่วไหลของข้อมูล: พบ {col} ในที่เก็บฟีเจอร์!"

    provenance = {
        "dataset_name": "HarvardX-MITx Person-Course Academic Year 2013",
        "dataset_source": config["dataset_source"],
        "raw_file_name": os.path.basename(raw_data_path),
        "raw_file_sha256": raw_hash,
        "raw_file_size_mb": round(file_size_mb, 2),
        "total_records": total_records,
        "total_columns": total_cols,
        "unique_students": unique_students,
        "unit_of_analysis": config["unit_of_analysis"],
        "target_variables_isolated": outcome_columns,
        "anti_leakage_policy": config["anti_leakage_constraint"],
    }
    prov_path = os.path.join(PROCESSED_DIR, "data_provenance.json")
    with open(prov_path, "w", encoding="utf-8") as handle:
        json.dump(provenance, handle, indent=2, ensure_ascii=False)
    print(f"[+] บันทึกประวัติและแหล่งกำเนิดข้อมูลที่: {prov_path}")


if __name__ == "__main__":
    run_data_gathering()
