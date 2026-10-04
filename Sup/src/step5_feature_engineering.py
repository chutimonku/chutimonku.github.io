"""ขั้นตอนที่ 5: การสร้างฟีเจอร์และไปป์ไลน์การแปลงข้อมูล (ตามหลักความเคร่งครัดของการแบ่งข้อมูล Train/Val/Test)."""

import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler

STUDENTS_PATH = os.path.join("data", "processed", "students_cleaned.parquet")
LABELS_PATH = os.path.join("data", "labels", "student_labels.parquet")
CONFIG_PATH = os.path.join("config", "project_config.json")
PROCESSED_DIR = os.path.join("data", "processed")
LABELS_DIR = os.path.join("data", "labels")
MODELS_DIR = os.path.join("models")
TABLES_DIR = os.path.join("outputs", "tables")
REPRO_DIR = os.path.join("outputs", "reproducibility")

from src.feature_transformer import Log1pTransformer


def run_feature_engineering():
    """ดำเนินกระบวนการแบ่งชุดข้อมูลแบบแบ่งชั้น (Stratified Split) และสร้างไปป์ไลน์แปลงฟีเจอร์."""
    print("=" * 70)
    print("ขั้นตอนที่ 5: วิศวกรรมฟีเจอร์และไปป์ไลน์การแปลงข้อมูล")
    print("=" * 70)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(LABELS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(TABLES_DIR, exist_ok=True)
    os.makedirs(REPRO_DIR, exist_ok=True)

    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)

    split_cfg = config["split_strategy"]
    seed = split_cfg["random_seed"]

    df_students = pd.read_parquet(STUDENTS_PATH)
    df_labels = pd.read_parquet(LABELS_PATH)

    # ตรวจสอบการเรียงตรงกันของรหัสนักศึกษา
    assert (df_students["userid_DI"] == df_labels["userid_DI"]).all()

    target_series = df_labels["certified_student"]

    # 1. การแบ่งชุดข้อมูลแบบแบ่งชั้น (Stratified Partitioning: Train 70%, Val 15%, Test 15%)
    print("[+] ดำเนินการแบ่งข้อมูลแบบแบ่งชั้น (Train 70%, Val 15%, Test 15%)...")
    indices = np.arange(len(df_students))
    train_idx, temp_idx = train_test_split(
        indices,
        test_size=0.30,
        random_state=seed,
        stratify=target_series,
    )
    val_rel_ratio = 0.50  # 0.50 ของ 0.30 เท่ากับ 0.15
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=val_rel_ratio,
        random_state=seed,
        stratify=target_series.iloc[temp_idx],
    )

    print(f"    ขนาด Train: {len(train_idx):,} ({len(train_idx)/len(indices)*100:.1f}%)")
    print(f"    ขนาด Val:   {len(val_idx):,} ({len(val_idx)/len(indices)*100:.1f}%)")
    print(f"    ขนาด Test:  {len(test_idx):,} ({len(test_idx)/len(indices)*100:.1f}%)")

    train_pos_rate = float(target_series.iloc[train_idx].mean() * 100)
    val_pos_rate = float(target_series.iloc[val_idx].mean() * 100)
    test_pos_rate = float(target_series.iloc[test_idx].mean() * 100)

    print(f"    สัดส่วนคลาสบวก: Train={train_pos_rate:.2f}%, Val={val_pos_rate:.2f}%, Test={test_pos_rate:.2f}%")

    split_summary = {
        "random_seed": seed,
        "stratification_variable": "certified_student",
        "train_students": len(train_idx),
        "val_students": len(val_idx),
        "test_students": len(test_idx),
        "train_positive_rate": train_pos_rate,
        "val_positive_rate": val_pos_rate,
        "test_positive_rate": test_pos_rate,
        "anti_leakage_note": "แบ่งชุดข้อมูลก่อนการฟิตไปป์ไลน์การแปลงฟีเจอร์ใดๆ อย่างเคร่งครัด",
    }
    with open(os.path.join(REPRO_DIR, "split_summary.json"), "w", encoding="utf-8") as handle:
        json.dump(split_summary, handle, indent=2, ensure_ascii=False)

    # 2. แยกฟีเจอร์และเลเบลตามพาร์ติชัน
    X_train_df = df_students.iloc[train_idx].copy()
    X_val_df = df_students.iloc[val_idx].copy()
    X_test_df = df_students.iloc[test_idx].copy()

    y_train_df = df_labels.iloc[train_idx].copy()
    y_val_df = df_labels.iloc[val_idx].copy()
    y_test_df = df_labels.iloc[test_idx].copy()

    # กำหนดกลุ่มฟีเจอร์ตามพฤติกรรมการแจกแจง
    skewed_features = [
        "total_events",
        "mean_events_per_course",
        "max_events_single_course",
        "total_active_days",
        "mean_active_days_per_course",
        "max_active_days_single_course",
        "total_video_plays",
        "total_chapters",
        "mean_chapters_per_course",
        "max_chapters_single_course",
        "total_forum_posts",
        "overall_span_days",
        "event_intensity",
    ]

    standard_features = [
        "n_courses",
        "unique_courses",
        "n_institutes",
        "view_rate",
        "total_courses_viewed",
        "video_data_available_rate",
        "age",
        "age_missing_records",
        "overall_span_missing",
        "video_play_ratio",
        "chapter_intensity",
        "has_forum_activity",
        "has_multiple_courses",
        "date_inversion_records",
    ]

    categorical_features = ["gender", "LoE_DI", "country"]

    all_model_features = skewed_features + standard_features + categorical_features

    # จัดทำเอกสารข้อกำหนดฟีเจอร์ (Feature Definitions)
    feature_defs = []
    for feat in skewed_features:
        feature_defs.append({
            "feature_name": feat,
            "type": "skewed_numeric",
            "preprocessing": "SimpleImputer(median) -> Log1p -> RobustScaler",
            "rationale": "ข้อมูลมีความเบ้ขวาสูงและมีหางยาว จำเป็นต้องบีบอัดด้วย log และปรับสเกลแบบ robust",
        })
    for feat in standard_features:
        feature_defs.append({
            "feature_name": feat,
            "type": "standard_numeric",
            "preprocessing": "SimpleImputer(median) -> StandardScaler",
            "rationale": "ตัวแปรอัตราส่วนหรือตัวบ่งชี้ที่มีขอบเขต ปรับสเกลด้วยค่าเฉลี่ยและส่วนเบี่ยงเบนมาตรฐาน",
        })
    for feat in categorical_features:
        feature_defs.append({
            "feature_name": feat,
            "type": "categorical",
            "preprocessing": "SimpleImputer(constant='Unknown') -> OneHotEncoder(min_freq=0.01, ignore_unknown)",
            "rationale": "ข้อมูลกลุ่มประชากรศาสตร์ที่มีความเบาบาง แปลงเป็น One-Hot พร้อมคัดกรองความถี่ขั้นต่ำ 1%",
        })
    pd.DataFrame(feature_defs).to_csv(os.path.join(PROCESSED_DIR, "feature_definitions.csv"), index=False)
    print(f"[+] บันทึกข้อกำหนดฟีเจอร์เรียบร้อยที่: {os.path.join(PROCESSED_DIR, 'feature_definitions.csv')}")

    # สร้างไปป์ไลน์การแปลงข้อมูล
    skewed_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("log1p", Log1pTransformer()),
        ("scaler", RobustScaler()),
    ])

    standard_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=0.01)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("skew", skewed_pipe, skewed_features),
            ("std", standard_pipe, standard_features),
            ("cat", categorical_pipe, categorical_features),
        ],
        remainder="drop",
    )

    # 3. ฟิตไปป์ไลน์เฉพาะบนชุด Train เท่านั้น (Anti-Leakage Discipline)
    print("[+] กำลังฟิตไปป์ไลน์เฉพาะบนชุด X_train (ป้องกันข้อมูลรั่วไหล)...")
    preprocessor.fit(X_train_df[all_model_features])

    cat_feature_names = preprocessor.named_transformers_["cat"].named_steps["ohe"].get_feature_names_out(categorical_features)
    transformed_feature_names = skewed_features + standard_features + list(cat_feature_names)
    print(f"    จำนวนฟีเจอร์หลังการแปลง One-Hot: {len(transformed_feature_names)} ฟีเจอร์")

    # 4. แปลงข้อมูลในแต่ละพาร์ติชัน
    X_train_trans = preprocessor.transform(X_train_df[all_model_features])
    X_val_trans = preprocessor.transform(X_val_df[all_model_features])
    X_test_trans = preprocessor.transform(X_test_df[all_model_features])

    # บันทึกเมทริกซ์ฟีเจอร์ในรูปแบบ Parquet
    df_train_proc = pd.DataFrame(X_train_trans, columns=transformed_feature_names)
    df_train_proc.insert(0, "userid_DI", X_train_df["userid_DI"].values)

    df_val_proc = pd.DataFrame(X_val_trans, columns=transformed_feature_names)
    df_val_proc.insert(0, "userid_DI", X_val_df["userid_DI"].values)

    df_test_proc = pd.DataFrame(X_test_trans, columns=transformed_feature_names)
    df_test_proc.insert(0, "userid_DI", X_test_df["userid_DI"].values)

    df_train_proc.to_parquet(os.path.join(PROCESSED_DIR, "train_features.parquet"), index=False)
    df_val_proc.to_parquet(os.path.join(PROCESSED_DIR, "val_features.parquet"), index=False)
    df_test_proc.to_parquet(os.path.join(PROCESSED_DIR, "test_features.parquet"), index=False)

    y_train_df.to_parquet(os.path.join(LABELS_DIR, "train_labels.parquet"), index=False)
    y_val_df.to_parquet(os.path.join(LABELS_DIR, "val_labels.parquet"), index=False)
    y_test_df.to_parquet(os.path.join(LABELS_DIR, "test_labels.parquet"), index=False)

    # บันทึกไฟล์ Artifact ของไปป์ไลน์การแปลงข้อมูล
    pipeline_save_path = os.path.join(MODELS_DIR, "preprocessing_pipeline.joblib")
    joblib.dump({
        "preprocessor": preprocessor,
        "feature_names": transformed_feature_names,
        "input_features": all_model_features,
    }, pipeline_save_path)
    print(f"[+] บันทึกไปป์ไลน์การแปลงข้อมูลที่: {pipeline_save_path}")

    # 5. สร้างตารางเปรียบเทียบผลการแปลงฟีเจอร์
    comp_records = []
    for col in skewed_features[:5]:
        raw_vals = X_train_df[col].dropna()
        comp_records.append({
            "feature": col,
            "raw_skewness": float(round(raw_vals.skew(), 2)),
            "transformed_skewness": float(round(np.log1p(np.maximum(raw_vals, 0)).skew(), 2)),
            "raw_range": f"[{raw_vals.min():.0f}, {raw_vals.max():.0f}]",
            "transformation": "Log1p + RobustScaler",
        })
    df_comp = pd.DataFrame(comp_records)
    df_comp.to_csv(os.path.join(TABLES_DIR, "feature_engineering_comparison.csv"), index=False)
    print(f"[+] บันทึกตารางเปรียบเทียบการแปลงฟีเจอร์ที่: {os.path.join(TABLES_DIR, 'feature_engineering_comparison.csv')}")


if __name__ == "__main__":
    run_feature_engineering()
