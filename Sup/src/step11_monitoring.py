"""ขั้นตอนที่ 11: การติดตามโมเดลในการใช้งานจริง การตรวจจับการเลื่อนไหล (Drift Detection) และวงรอบการป้อนกลับ (Feedback Loop)."""

import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

STUDENTS_PATH = os.path.join("data", "processed", "students_cleaned.parquet")
PREDICTIONS_PATH = os.path.join("outputs", "data", "test_predictions.csv")
MONITORING_DIR = os.path.join("monitoring")
CONFIG_PATH = os.path.join("config", "project_config.json")


def calculate_baseline_distributions(df_students: pd.DataFrame, df_preds: pd.DataFrame) -> dict:
    """คำนวณการกระจายตัวอ้างอิงเชิงประจักษ์ (Empirical Reference Distributions) สำหรับการติดตามการเลื่อนไหลของข้อมูล."""
    numerical_cols = [
        "total_events",
        "total_active_days",
        "total_chapters",
        "total_video_plays",
        "total_forum_posts",
        "event_intensity",
        "video_play_ratio",
        "overall_span_days",
    ]

    baselines = {}
    for col in numerical_cols:
        series = df_students[col].dropna()
        baselines[col] = {
            "mean": float(round(series.mean(), 4)),
            "std": float(round(series.std(), 4)),
            "p10": float(round(series.quantile(0.10), 4)),
            "p25": float(round(series.quantile(0.25), 4)),
            "median": float(round(series.median(), 4)),
            "p75": float(round(series.quantile(0.75), 4)),
            "p90": float(round(series.quantile(0.90), 4)),
            "p99": float(round(series.quantile(0.99), 4)),
        }

    tier_dist = df_preds["risk_tier"].value_counts(normalize=True).to_dict()
    prob_col = "predicted_probability" if "predicted_probability" in df_preds.columns else "completion_probability"
    baselines["prediction_drift"] = {
        "mean_predicted_probability": float(round(df_preds[prob_col].mean(), 4)),
        "std_predicted_probability": float(round(df_preds[prob_col].std(), 4)),
        "tier_proportions": {k: float(round(v, 4)) for k, v in tier_dist.items()},
    }
    return baselines


def run_monitoring_setup():
    """สร้างค่าเกณฑ์อ้างอิงการติดตามโมเดล เกณฑ์แจ้งเตือน และรายงานการกำกับดูแล."""
    print("=" * 70)
    print("ขั้นตอนที่ 11: การติดตามโมเดลในการใช้งานจริงและวงรอบการป้อนกลับ")
    print("=" * 70)

    os.makedirs(MONITORING_DIR, exist_ok=True)

    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)

    df_students = pd.read_parquet(STUDENTS_PATH)
    df_preds = pd.read_csv(PREDICTIONS_PATH)

    baselines = calculate_baseline_distributions(df_students, df_preds)
    baseline_timestamp = datetime.now(timezone.utc).isoformat()

    monitoring_config = {
        "baseline_established_at": baseline_timestamp,
        "reference_student_count": len(df_students),
        "reference_test_scored": len(df_preds),
        "future_cohorts_evaluated": 0,
        "monitoring_status": "not_evaluated",
        "monitoring_status_reason": "สร้างชุดข้อมูลอ้างอิงเริ่มต้น ยังไม่มีข้อมูลรุ่นถัดไปส่งเข้ามาเพื่อประเมินการเลื่อนไหลจริง",
        "monitoring_cadence": "ตรวจสอบแบบแบทช์รายสัปดาห์ / เมื่อเริ่มเปิดรอบการสอนวิชาใหม่",
        "drift_thresholds": {
            "psi_warning_level": 0.10,
            "psi_critical_alarm": 0.25,
            "wasserstein_standardized_warning": 2.5,
            "tier_redistribution_alert_pct": 15.0,
            "data_quality_missingness_max_pct": 5.0,
        },
        "reference_distributions": baselines,
        "retraining_triggers": [
            "ค่าดัชนีเสถียรภาพประชากร (PSI) >= 0.25 บนฟีเจอร์ active_days หรือ chapters",
            "อัตราการสำเร็จการศึกษาจริงเบี่ยงเบนเกิน 25% จากความคาดหวังตามระดับความเสี่ยง",
            "โครงสร้างรายวิชามีการเปลี่ยนแปลงอย่างมีนัยสำคัญ (เช่น ความยาวหลักสูตร รูปแบบการให้คะแนน)",
            "ระยะเวลาการใช้งานจริงเกิน 6 เดือนโดยไม่มีการเทียบเคียงปรับจูนโมเดลใหม่",
        ],
    }

    config_out_path = os.path.join(MONITORING_DIR, "monitoring_config.json")
    with open(config_out_path, "w", encoding="utf-8") as handle:
        json.dump(monitoring_config, handle, indent=2, ensure_ascii=False)
    print(f"[+] บันทึกคอนฟิกการติดตามที่: {config_out_path}")

    # บันทึกประวัติการติดตาม
    history_records = [
        {
            "audit_timestamp": baseline_timestamp,
            "event_type": "baseline_established",
            "cohort_evaluated": "None — ค่าอ้างอิงเริ่มต้นเท่านั้น",
            "student_count": len(df_preds),
            "mean_pred_prob": baselines["prediction_drift"]["mean_predicted_probability"],
            "tier_3_high_risk_pct": baselines["prediction_drift"]["tier_proportions"].get("Tier 3: High Risk / Early Dropout", 0.0) * 100,
            "tier_2_mod_risk_pct": baselines["prediction_drift"]["tier_proportions"].get("Tier 2: Moderate Risk / Target for Nudge", 0.0) * 100,
            "tier_1_low_risk_pct": baselines["prediction_drift"]["tier_proportions"].get("Tier 1: Low Risk / Likely Completer", 0.0) * 100,
            "drift_status": "NOT_EVALUATED_NO_FUTURE_COHORT",
            "retraining_required": None,
        }
    ]
    df_history = pd.DataFrame(history_records)
    history_path = os.path.join(MONITORING_DIR, "monitoring_history.csv")
    df_history.to_csv(history_path, index=False)
    print(f"[+] บันทึกประวัติการติดตามที่: {history_path}")

    # บันทึกการตัดสินใจฝึกสอนซ้ำ (Retraining Decision)
    decision_record = {
        "evaluated_at": baseline_timestamp,
        "current_champion_status": "BASELINE_READY_NOT_EVALUATED",
        "drift_evaluation_status": "not_evaluated",
        "drift_detected": None,
        "performance_degradation_detected": None,
        "retraining_decision": "NOT_EVALUATED",
        "rationale": "สร้างชุดข้อมูลอ้างอิงเรียบร้อยแล้ว ยังไม่มีข้อมูลนักศึกษารุ่นใหม่ส่งเข้ามา ประสิทธิภาพบน Holdout Test จึงไม่ใช่หลักฐานของการไม่มี Drift",
        "next_action": "ประเมินและเปรียบเทียบข้อมูลนักศึกษารุ่นถัดไปเมื่อได้รับข้อมูลก่อนตัดสินใจ Retrain",
    }
    decision_path = os.path.join(MONITORING_DIR, "retraining_decision.json")
    with open(decision_path, "w", encoding="utf-8") as handle:
        json.dump(decision_record, handle, indent=2, ensure_ascii=False)
    print(f"[+] บันทึกผลการตัดสินใจฝึกสอนซ้ำที่: {decision_path}")

    # สร้างหน้ารายงานการติดตามผล HTML
    html_monitoring = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>การติดตามโมเดลในการใช้งานจริงและนโยบายการตรวจจับ Drift</title>
<style>
  body {{ font-family: "Thonburi", "Sukhumvit Set", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #F8FAFC; color: #1E293B; padding: 24px; line-height: 1.6; }}
  .container {{ max-width: 1000px; margin: 0 auto; background: #FFF; padding: 32px; border-radius: 10px; border: 1px solid #E2E8F0; }}
  h1 {{ color: #1E3A8A; font-size: 1.8rem; margin-bottom: 8px; }}
  h2 {{ color: #334155; font-size: 1.2rem; margin: 24px 0 12px 0; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.9rem; }}
  th, td {{ padding: 10px; border: 1px solid #E2E8F0; text-align: left; }}
  th {{ background: #F1F5F9; font-weight: 600; }}
  .status-tag {{ display: inline-block; padding: 4px 12px; background: #FEF3C7; color: #92400E; border-radius: 12px; font-weight: bold; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>การติดตามโมเดลในการใช้งานจริงและการกำกับดูแลการเลื่อนไหล (Model Governance)</h1>
  <p>สถานะ: <span class="status-tag">ค่าอ้างอิงพร้อมใช้งาน — รอข้อมูลรุ่นถัดไป</span> &bull; ประชากรอ้างอิง: {len(df_students):,} คน</p>
  <p>ชุดข้อมูลนี้สร้างขึ้นเป็นเกณฑ์เปรียบเทียบมาตรฐานสำหรับนักศึกษารุ่นถัดไป เมื่อมีข้อมูลจริงส่งเข้ามา ระบบจะตรวจสอบการเลื่อนไหลและแจ้งเตือนการ Retrain อัตโนมัติ</p>

  <h2>1. การกระจายตัวของฟีเจอร์อ้างอิง (Reference Feature Distributions)</h2>
  <table>
    <tr><th>ฟีเจอร์</th><th>ค่าเฉลี่ย (Mean)</th><th>ส่วนเบี่ยงเบน (Std)</th><th>มัธยฐาน (P50)</th><th>เปอร์เซ็นไทล์ 75</th><th>เปอร์เซ็นไทล์ 90</th></tr>
    {"".join(f"<tr><td><code>{k}</code></td><td>{v['mean']:,}</td><td>{v['std']:,}</td><td>{v['median']:,}</td><td>{v['p75']:,}</td><td>{v['p90']:,}</td></tr>" for k, v in baselines.items() if k != "prediction_drift")}
  </table>

  <h2>2. การกระจายตัวของผลการทำนายและระดับความเสี่ยงอ้างอิง</h2>
  <table>
    <tr><th>ตัวชี้วัด / ระดับความเสี่ยง</th><th>สัดส่วนหรือค่าอ้างอิงเริ่มต้น</th></tr>
    <tr><td>ค่าความน่าจะเป็นเฉลี่ยที่จะสำเร็จการศึกษา</td><td>{baselines['prediction_drift']['mean_predicted_probability']:.4f}</td></tr>
    {"".join(f"<tr><td>{tier}</td><td>{pct*100:.2f}%</td></tr>" for tier, pct in baselines['prediction_drift']['tier_proportions'].items())}
  </table>

  <h2>3. เงื่อนไขกระตุ้นการฝึกสอนโมเดลซ้ำ (Retraining Triggers)</h2>
  <ul>
    {"".join(f"<li>{trigger}</li>" for trigger in monitoring_config['retraining_triggers'])}
  </ul>
</div>
</body>
</html>
"""
    report_out_path = os.path.join(MONITORING_DIR, "monitoring_report.html")
    with open(report_out_path, "w", encoding="utf-8") as handle:
        handle.write(html_monitoring)
    print(f"[+] บันทึกรายงานการติดตามที่: {report_out_path}")


if __name__ == "__main__":
    run_monitoring_setup()
