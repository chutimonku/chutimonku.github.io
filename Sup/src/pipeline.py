"""ขั้นตอนที่ 9: การบรรจุส่งมอบไปป์ไลน์การติดตั้งใช้งาน สคีมา และเอกสารกำกับโมเดล (Model Card)."""

import json
import os
import joblib
import pandas as pd
from src.deployment import MoocStudentRiskPipeline
from src.feature_transformer import Log1pTransformer

MODELS_DIR = os.path.join("models")
FINAL_MODELS_DIR = os.path.join("models", "final")
CONFIG_PATH = os.path.join("config", "project_config.json")
EXAMPLES_DIR = os.path.join("examples")


def run_deployment_packaging():
    """ฟังก์ชันหลักสำหรับสร้างและส่งมอบอาร์ติแฟกต์ไปป์ไลน์การติดตั้งใช้งาน."""
    print("=" * 70)
    print("ขั้นตอนที่ 9: การบรรจุส่งมอบไปป์ไลน์และอาร์ติแฟกต์การติดตั้งใช้งาน")
    print("=" * 70)

    os.makedirs(FINAL_MODELS_DIR, exist_ok=True)
    os.makedirs(EXAMPLES_DIR, exist_ok=True)

    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)

    lock_path = os.path.join(FINAL_MODELS_DIR, "model_lock.json")
    if not os.path.exists(lock_path):
        raise FileNotFoundError(f"ไม่พบไฟล์ล็อกโมเดลที่ {lock_path} กรุณารันขั้นตอนที่ 8 ก่อน")

    with open(lock_path, encoding="utf-8") as handle:
        lock_meta = json.load(handle)

    preproc_bundle = joblib.load(os.path.join(MODELS_DIR, "preprocessing_pipeline.joblib"))
    preprocessor = preproc_bundle["preprocessor"]
    input_features = preproc_bundle["input_features"]

    champion_model = joblib.load(os.path.join(FINAL_MODELS_DIR, "supervised_model.joblib"))
    opt_threshold = lock_meta["optimal_decision_threshold"]

    pipeline = MoocStudentRiskPipeline(
        preprocessor=preprocessor,
        model=champion_model,
        optimal_threshold=opt_threshold,
        risk_tiers_config=config["risk_tiers"],
        input_features=input_features,
        forbidden_outcome_columns=config["outcome_columns"],
    )

    # บันทึกไฟล์ไปป์ไลน์การติดตั้งใช้งานแบบสมบูรณ์
    deploy_pipe_path = os.path.join(FINAL_MODELS_DIR, "deployment_pipeline.joblib")
    joblib.dump(pipeline, deploy_pipe_path)
    print(f"[+] บันทึกไปป์ไลน์การติดตั้งใช้งานเรียบร้อยที่: {deploy_pipe_path}")

    # สร้างข้อกำหนด Input Schema ระดับนักศึกษา
    # ฟีเจอร์อนุพันธ์ 5 ตัวจะถูกคำนวณใหม่โดยอัตโนมัติภายในคลาสไปป์ไลน์ จึงไม่ต้องระบุในไฟล์นำเข้า
    required_input_features = pipeline.required_input_features
    categorical_features = {"gender", "LoE_DI", "country"}
    rate_features = {"view_rate", "video_data_available_rate"}
    schema_properties = {
        "userid_DI": {"type": "string", "minLength": 1, "description": "รหัสประจำตัวนักศึกษาที่ไม่ซ้ำกัน"}
    }
    for feature in required_input_features:
        if feature in categorical_features:
            schema_properties[feature] = {
                "type": ["string", "null"],
                "description": "ฟีเจอร์เชิงกลุ่มระดับนักศึกษา หากมีค่าว่างจะถูกจัดการโดยกระบวนการแปลงข้อมูลที่เรียนรู้ไว้",
            }
        else:
            definition = {
                "type": ["number", "null"],
                "minimum": 0,
                "description": "ฟีเจอร์ตัวเลขรวมระดับนักศึกษาสำหรับใช้ในโมเดล",
            }
            if feature in rate_features:
                definition["maximum"] = 1
            if feature == "age":
                definition["exclusiveMinimum"] = 0
                definition["maximum"] = 100
            schema_properties[feature] = definition

    input_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "MoocStudentRiskInputSchema",
        "description": "ข้อกำหนดความถูกต้องของข้อมูลนำเข้าระดับนักศึกษาสำหรับระบบทำนายความเสี่ยง",
        "type": "object",
        "required": ["userid_DI", *required_input_features],
        "properties": schema_properties,
        "derived_by_pipeline": sorted(set(input_features).difference(required_input_features)),
        "forbidden_outcome_columns": config["outcome_columns"],
        "anti_leakage_guarantee": "ข้อมูลที่มีคอลัมน์ผลลัพธ์ปลายทางจะถูกปฏิเสธทันทีด้วย DataLeakageSecurityException เพื่อป้องกันข้อมูลรั่วไหล",
    }
    schema_path = os.path.join(FINAL_MODELS_DIR, "input_schema.json")
    with open(schema_path, "w", encoding="utf-8") as handle:
        json.dump(input_schema, handle, indent=2, ensure_ascii=False)
    print(f"[+] บันทึกข้อกำหนด Input Schema เรียบร้อยที่: {schema_path}")

    # สร้างเอกสารกำกับโมเดล (Model Card)
    cert_meta = lock_meta.get("predicted_certificate_metrics", {})
    model_card_content = f"""# เอกสารกำกับโมเดล (Model Card): ระบบทำนายความเสี่ยงและโอกาสสำเร็จการศึกษา MOOC

## รายละเอียดโมเดล (Model Details)
- **ชื่อโมเดล:** MoocStudentRiskClassifier ({lock_meta['champion_model_name']})
- **เวอร์ชัน:** 1.0.0
- **ประเภทโมเดล:** โมเดลการเรียนรู้แบบมีผู้สอน (Supervised Binary Classification with Calibrated Probability)
- **อัลกอริทึม:** {lock_meta['champion_model_name']} (คัดเลือกจากผลลัพธ์บนชุด Validation ก่อนประเมินบนชุด Holdout Test)
- **ที่อยู่ไฟล์โมเดล:** `models/final/deployment_pipeline.joblib`
- **ค่าแฮชตรวจสอบความสมบูรณ์ (SHA-256):** `{lock_meta['model_file_sha256']}`
- **จุดตัดการตัดสินใจที่เหมาะสมที่สุด (Optimal Threshold):** `{lock_meta['optimal_decision_threshold']}`
- **เฟรมเวิร์ก:** scikit-learn / Python 3.13

## วัตถุประสงค์และการนำไปใช้งาน (Intended Use)
- **กรณีการใช้งานหลัก:** ระบุนักศึกษาที่มีความเสี่ยงที่จะไม่สำเร็จการศึกษา เพื่อให้คำปรึกษาและส่งสัญญาณเตือนเชิงรุก (Academic Nudge)
- **ระดับความเสี่ยง 3 กลุ่ม (Operational Risk Tiers):**
  - **Tier 1 (ความเสี่ยงต่ำ / มีแนวโน้มได้รับใบจบ, p >= 0.50):** เสริมสร้างศักยภาพขั้นสูง กิจกรรมติวเพื่อนร่วมชั้น
  - **Tier 2 (ความเสี่ยงปานกลาง / กลุ่มเป้าหมายส่งสัญญาณหนุน, 0.15 <= p < 0.50):** แจ้งเตือนส่งงาน จับคู่กลุ่มติว ติดตามความก้าวหน้า
  - **Tier 3 (ความเสี่ยงสูง / เสี่ยงออกกลางคัน, p < 0.15):** ติดต่อเร่งด่วนจากอาจารย์ที่ปรึกษา ช่วยเหลือเทคนิค ปรับพื้นฐานความรู้
- **ข้อห้ามใช้เด็ดขาด:** ห้ามนำไปใช้ตัดสิทธิ์การเรียน ถอดถอนวิชา หรือลงโทษทางวิชาการโดยอัตโนมัติ

## สรุปประสิทธิภาพเชิงปริมาณ (Quantitative Performance)
- **Holdout ROC-AUC:** {lock_meta['test_metrics']['test_roc_auc']}
- **Holdout PR-AUC:** {lock_meta['test_metrics']['test_pr_auc']} (เทียบกับค่าฐานความชุก 0.0414)
- **Brier Score:** {lock_meta['test_metrics']['test_brier_score']} (ความเที่ยงตรงของความน่าจะเป็นสูงมาก)
- **Accuracy รวม:** {lock_meta['test_metrics']['test_accuracy_optimal'] * 100:.2f}%
- **Precision (ความแม่นยำกลุ่มจบ):** {lock_meta['test_metrics']['test_precision_optimal'] * 100:.2f}%
- **Recall (อัตราตรวจพบกลุ่มจบ):** {lock_meta['test_metrics']['test_recall_optimal'] * 100:.2f}%
- **F1-Score (ที่จุดตัด Max-F1):** {lock_meta['test_metrics']['test_f1_optimal'] * 100:.2f}%
- **คาดการณ์จำนวนผู้ได้รับใบจบในชุดทดสอบ:** {cert_meta.get('predicted_certificate_count', 'N/A')} คน ({cert_meta.get('predicted_certificate_pct', 'N/A')}%) จากทั้งหมด {cert_meta.get('holdout_test_size', 'N/A')} คน
"""
    model_card_path = os.path.join(FINAL_MODELS_DIR, "model_card.md")
    with open(model_card_path, "w", encoding="utf-8") as handle:
        handle.write(model_card_content)
    print(f"[+] บันทึก Model Card เรียบร้อยที่: {model_card_path}")

    # สร้างข้อมูลตัวอย่างที่ครอบคลุมทั้ง 3 ระดับความเสี่ยง (Tier 1, Tier 2, Tier 3)
    print("[+] กำลังสร้างชุดข้อมูลตัวอย่างนักศึกษาและทดสอบการทำนายผล...")
    profiles = pd.read_parquet(os.path.join("data", "processed", "students_cleaned.parquet"))
    labels = pd.read_parquet(os.path.join("data", "labels", "student_labels.parquet"))
    merged_prof = pd.merge(profiles, labels, on="userid_DI")

    # สุ่มเลือกตัวแทนนักศึกษา 3 รูปแบบ
    # 1. กลุ่มตั้งใจเรียนสูง/จบจริง (Tier 1)
    t1_cands = merged_prof[(merged_prof["certified_student"] == 1) & (merged_prof["total_events"] > 3000)]
    idx_t1 = t1_cands.index[0] if not t1_cands.empty else profiles.index[0]

    # 2. กลุ่มระดับปานกลาง (Tier 2)
    t2_cands = merged_prof[(merged_prof["certified_student"] == 0) & (merged_prof["total_events"] > 1000) & (merged_prof["total_events"] < 2500)]
    idx_t2 = t2_cands.index[0] if not t2_cands.empty else profiles.index[len(profiles) // 2]

    # 3. กลุ่มกิจกรรมน้อย/ออกกลางคัน (Tier 3)
    t3_cands = merged_prof[(merged_prof["certified_student"] == 0) & (merged_prof["total_events"] < 50)]
    idx_t3 = t3_cands.index[0] if not t3_cands.empty else profiles.index[-1]

    sample_students = profiles.loc[
        [idx_t1, idx_t2, idx_t3], ["userid_DI", *required_input_features]
    ].copy().reset_index(drop=True)
    sample_students["userid_DI"] = ["SAMPLE_TIER1_COMPLETER", "SAMPLE_TIER2_NUDGE", "SAMPLE_TIER3_DROPOUT"]

    sample_in_path = os.path.join(EXAMPLES_DIR, "sample_student_input.csv")
    sample_students.to_csv(sample_in_path, index=False)

    sample_predictions = pipeline.predict_risk_tiers(sample_students)
    sample_out_path = os.path.join(EXAMPLES_DIR, "sample_prediction_output.csv")
    sample_predictions.to_csv(sample_out_path, index=False)
    print(f"[+] บันทึกไฟล์ข้อมูลนำเข้าตัวอย่างที่:  {sample_in_path}")
    print(f"[+] บันทึกไฟล์ผลการทำนายตัวอย่างที่: {sample_out_path}")
    print(sample_predictions[["userid_DI", "completion_probability", "predicted_completion", "risk_tier", "recommended_support_action"]])


if __name__ == "__main__":
    run_deployment_packaging()
