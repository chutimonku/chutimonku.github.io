"""Step 11: create honest monitoring baselines without fabricating future data."""

from __future__ import annotations

import json
import os

import pandas as pd


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONITORING = os.path.join(ROOT, "monitoring")
STUDENTS = os.path.join(ROOT, "data", "processed", "students_cleaned.parquet")
ASSIGNMENTS = os.path.join(ROOT, "outputs", "data", "unsupervised_cluster_assignments.csv")
PREDICTIONS = os.path.join(ROOT, "outputs", "data", "supervised_certification_predictions.csv")


def _json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def run_track_monitoring():
    os.makedirs(MONITORING, exist_ok=True)
    students = pd.read_parquet(STUDENTS)
    clusters = pd.read_csv(ASSIGNMENTS)
    predictions = pd.read_csv(PREDICTIONS)
    with open(os.path.join(MONITORING, "unsupervised_monitoring_baseline.json"), encoding="utf-8") as handle:
        unsupervised_baseline = json.load(handle)
    unsupervised_features = unsupervised_baseline["features"]
    baseline = {
        "status": "BASELINE_READY_NO_FUTURE_COHORT",
        "students": int(len(students)),
        "schema": {column: str(dtype) for column, dtype in students.dtypes.items()},
        "behavior_feature_quantiles": {
            column: {str(q): float(v) for q, v in students[column].quantile([0.05, 0.25, 0.5, 0.75, 0.95]).items()}
            for column in unsupervised_features
        },
        "missing_rate": {column: float(students[column].isna().mean()) for column in unsupervised_features},
        "cluster_distribution": {
            str(int(k)): float(v) for k, v in clusters["unsupervised_cluster"].value_counts(normalize=True).sort_index().items()
        },
        "supervised_reference": {
            "observed_certification_rate": float(predictions["actual_certified"].mean()),
            "mean_predicted_probability": float(predictions["predicted_probability"].mean()),
        },
        "unsupervised_reference": unsupervised_baseline,
        "future_cohorts_evaluated": 0,
    }
    _json(os.path.join(MONITORING, "track_monitoring_baseline.json"), baseline)
    config = {
        "frequency": "per new academic cohort",
        "checks": [
            "schema and required fields",
            "missingness and invalid ranges",
            "behavior-feature distribution drift",
            "cluster proportion and outlier drift",
            "supervised discrimination and calibration when outcomes mature",
        ],
        "feedback_loop": "When material drift or performance degradation is confirmed, return to Step 2 and rerun the governed workflow.",
        "threshold_policy": "Thresholds must be calibrated on genuine later cohorts; no future-cohort values are simulated here.",
    }
    _json(os.path.join(MONITORING, "track_monitoring_config.json"), config)
    history = pd.DataFrame([{
        "cohort": "2012-2013 reference baseline",
        "students": len(students),
        "status": "NOT_EVALUATED_NO_FUTURE_COHORT",
        "future_cohort": False,
        "retraining_required": False,
    }])
    history.to_csv(os.path.join(MONITORING, "track_monitoring_history.csv"), index=False)
    _json(os.path.join(MONITORING, "track_retraining_decision.json"), {
        "status": "NOT_EVALUATED",
        "retraining_required": False,
        "reason": "A reference baseline exists, but no genuine future cohort is available for drift or performance comparison.",
    })
    report = """<!doctype html><html lang=\"th\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Monitoring readiness</title><style>body{font-family:Inter,Kanit,sans-serif;background:#f5f7fb;color:#0b1f3a;margin:0;padding:32px}.card{max-width:900px;margin:auto;background:white;border-top:8px solid #f4b400;padding:28px;border-radius:16px;box-shadow:0 10px 30px #0b1f3a18}code{background:#eef2f7;padding:2px 6px;border-radius:5px}</style><div class=\"card\"><h1>Monitoring & Maintenance</h1><p><strong>สถานะ:</strong> ยังประเมินไม่ได้ เพราะยังไม่มีข้อมูลนักศึกษารุ่นใหม่</p><p>ระบบได้บันทึก schema, missing rate, distribution ของฟีเจอร์, สัดส่วนกลุ่ม และ baseline ของโมเดลทำนายจากข้อมูลจริงแล้ว</p><p>เมื่อมีข้อมูลรุ่นใหม่ ให้เปรียบเทียบกับ <code>track_monitoring_baseline.json</code> หากพบ drift หรือประสิทธิภาพลดลง ให้ย้อนกลับไป Step 2</p></div></html>"""
    with open(os.path.join(MONITORING, "track_monitoring_report.html"), "w", encoding="utf-8") as handle:
        handle.write(report)
    print("[+] Step 11 monitoring baseline created; future status remains not evaluated.")


if __name__ == "__main__":
    run_track_monitoring()
