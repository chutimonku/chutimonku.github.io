"""รันและตรวจสอบความถูกต้องของเวิร์กโฟลว์ Supervised Learning ทั้ง 11 ขั้นตอนอย่างสมบูรณ์."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# รายการขั้นตอนการประมวลผลทั้งหมดตามลำดับ
STEPS = [
    ("ขั้นตอนที่ 1: การกำหนดขอบเขตปัญหา (Problem Definition)", "src.step1_problem_definition"),
    ("ขั้นตอนที่ 2: การรวบรวมข้อมูลและการแยกเลเบล (Data Gathering)", "src.step2_data_gathering"),
    ("ขั้นตอนที่ 3: การทำความสะอาดข้อมูลและการรวมระดับนักศึกษา (Data Cleaning)", "src.step3_data_cleaning"),
    ("ขั้นตอนที่ 4: การวิเคราะห์ข้อมูลเชิงสำรวจ (EDA & Screening)", "src.step4_eda"),
    ("ขั้นตอนที่ 5: วิศวกรรมฟีเจอร์และการแบ่งพาร์ติชัน (Feature Engineering)", "src.step5_feature_engineering"),
    ("ขั้นตอนที่ 6-7: การคัดเลือก ฝึกสอน และปรับจูนโมเดล (Model Training & Tuning)", "src.step6_7_model_training"),
    ("ขั้นตอนที่ 8: การประเมินผลโมเดลและล็อกโมเดล (Evaluation & Locking)", "src.step8_model_evaluation"),
    ("ขั้นตอนที่ 9: การบรรจุส่งมอบไปป์ไลน์ (Deployment Packaging)", "src.pipeline"),
    ("ขั้นตอนที่ 9: การทดสอบอัตโนมัติ (Automated Test Suite)", "tests.test_pipeline"),
    ("ขั้นตอนที่ 10: สร้างแดชบอร์ด HTML สรุปผล (HTML Dashboard)", "src.generate_report"),
    ("ขั้นตอนที่ 11: การติดตามโมเดลในการใช้งานจริง (Monitoring Baseline)", "src.step11_monitoring"),
    ("ปรับปรุงรายงานแดชบอร์ดฉบับสมบูรณ์ (Final Report Refresh)", "src.generate_report"),
]

# รายการไฟล์ Artifacts ที่จำเป็นต้องเกิดขึ้นครบถ้วนหลังรันสำเร็จ
REQUIRED_ARTIFACTS = [
    "Workflow.md",
    "agy_workflow_Sup.md",
    "CHANGELOG.md",
    "PRESENTATION_GUIDE_TH.md",
    "run_project.py",
    "prediction_app.py",
    "requirements.txt",
    "config/project_config.json",
    "src/__init__.py",
    "src/feature_transformer.py",
    "src/deployment.py",
    "src/inference_preparation.py",
    "src/pipeline.py",
    "src/predict_risk.py",
    "src/step1_problem_definition.py",
    "src/step2_data_gathering.py",
    "src/step3_data_cleaning.py",
    "src/step4_eda.py",
    "src/step5_feature_engineering.py",
    "src/step6_7_model_training.py",
    "src/step8_model_evaluation.py",
    "src/generate_report.py",
    "src/step11_monitoring.py",
    "tests/test_pipeline.py",
    "examples/sample_student_input.csv",
    "examples/sample_prediction_output.csv",
    "data/processed/problem_definition.json",
    "data/processed/data_provenance.json",
    "data/processed/data_dictionary.csv",
    "data/processed/raw_features.parquet",
    "data/labels/raw_targets.parquet",
    "data/processed/students_cleaned.parquet",
    "data/labels/student_labels.parquet",
    "data/processed/cleaning_rules.json",
    "data/processed/cleaning_audit.json",
    "data/processed/feature_definitions.csv",
    "data/processed/train_features.parquet",
    "data/processed/val_features.parquet",
    "data/processed/test_features.parquet",
    "data/labels/train_labels.parquet",
    "data/labels/val_labels.parquet",
    "data/labels/test_labels.parquet",
    "models/preprocessing_pipeline.joblib",
    "models/final/supervised_model.joblib",
    "models/final/model_lock.json",
    "models/final/deployment_pipeline.joblib",
    "models/final/input_schema.json",
    "models/final/model_card.md",
    "outputs/research/literature_review.md",
    "outputs/research/model_selection_rationale.md",
    "outputs/tables/eda_summary.csv",
    "outputs/tables/feature_screening.csv",
    "outputs/tables/candidate_models.csv",
    "outputs/tables/model_tuning_results.csv",
    "outputs/tables/model_comparison.csv",
    "outputs/tables/test_evaluation_summary.csv",
    "outputs/tables/certificate_prediction_summary.csv",
    "outputs/tables/feature_importance.csv",
    "outputs/tables/fairness_diagnostics.csv",
    "outputs/tables/error_analysis.csv",
    "outputs/tables/feature_engineering_comparison.csv",
    "outputs/tables/optimization_history.csv",
    "outputs/reproducibility/split_summary.json",
    "outputs/reproducibility/training_config.json",
    "outputs/reproducibility/experiment_log.md",
    "outputs/logs/model_training_log.csv",
    "outputs/data/test_predictions.csv",
    "reports/student_risk_prediction_report.html",
    "reports/report_manifest.json",
    "monitoring/monitoring_config.json",
    "monitoring/monitoring_report.html",
    "monitoring/monitoring_history.csv",
    "monitoring/retraining_decision.json",
]

REQUIRED_ARTIFACT_GROUPS = [
    {
        "label": "ภาพประกอบ EDA",
        "pattern": "outputs/figures/eda/*.png",
        "minimum_count": 1,
    },
    {
        "label": "ภาพประกอบการประเมินผลโมเดล",
        "pattern": "outputs/figures/evaluation/*.png",
        "minimum_count": 1,
    },
    {
        "label": "ไฟล์โมเดลตัวเลือกที่ผ่านการฝึกสอน",
        "pattern": "models/candidates/*.joblib",
        "minimum_count": 1,
    },
]


def sha256_file(path: Path) -> str:
    """คำนวณค่าแฮช SHA-256 ของไฟล์."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def write_run_state(step_results: list[dict], status: str, started_at: str, elapsed: float):
    """บันทึกสถานะการรันและเวลาดำเนินการของแต่ละขั้นตอนลงใน run_manifest.json."""
    output_dir = Path("outputs/reproducibility")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "elapsed_seconds": round(elapsed, 2),
        "python_version": sys.version,
        "steps": step_results,
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def verify_artifacts() -> dict:
    """ตรวจสอบความครบถ้วนสมบูรณ์ของไฟล์ผลลัพธ์ทั้งหมดในโครงการ."""
    rows = []
    for name in REQUIRED_ARTIFACTS:
        path = Path(name)
        exists = path.exists()
        rows.append({
            "path": name,
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else None,
            "sha256": sha256_file(path) if exists and path.is_file() else None,
        })
    groups = []
    for requirement in REQUIRED_ARTIFACT_GROUPS:
        matches = sorted(
            str(path) for path in Path(".").glob(requirement["pattern"]) if path.is_file()
        )
        groups.append({
            **requirement,
            "observed_count": len(matches),
            "complete": len(matches) >= requirement["minimum_count"],
            "matches": matches,
        })

    missing_files = [row["path"] for row in rows if not row["exists"]]
    missing_groups = [
        f"{group['label']} ({group['pattern']})"
        for group in groups
        if not group["complete"]
    ]
    check = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "required_count": len(rows) + len(groups),
        "required_file_count": len(rows),
        "required_group_count": len(groups),
        "complete": not missing_files and not missing_groups,
        "missing": missing_files + missing_groups,
        "artifacts": rows,
        "artifact_groups": groups,
    }
    output = Path("outputs/reproducibility/artifact_check.json")
    output.write_text(json.dumps(check, indent=2, ensure_ascii=False), encoding="utf-8")
    return check


def main():
    """ฟังก์ชันหลักสำหรับเริ่มรันกระบวนการทั้งหมดตั้งแต่ขั้นตอนที่ 1 ถึง 11."""
    started_clock = time.time()
    started_at = datetime.now(timezone.utc).isoformat()
    Path("outputs/logs").mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "."
    environment["MPLCONFIGDIR"] = os.path.join("/tmp", "mooc-matplotlib-sup")
    environment["LOKY_MAX_CPU_COUNT"] = str(os.cpu_count() or 1)

    results = []
    print("=" * 78)
    print("เริ่มกระบวนการทำงานเวิร์กโฟลว์ SUPERVISED LEARNING อย่างสมบูรณ์")
    print("=" * 78)

    for order, (title, module) in enumerate(STEPS, start=1):
        print(f"[{order}/{len(STEPS)}] {title}")
        step_started = time.time()

        if module == "tests.test_pipeline":
            cmd = [sys.executable, "-m", "pytest", "tests/test_pipeline.py"]
        else:
            cmd = [sys.executable, "-m", module]

        completed = subprocess.run(
            cmd,
            env=environment,
            capture_output=True,
            text=True,
        )
        duration = time.time() - step_started
        log_path = Path("outputs/logs") / f"{order:02d}_{module.replace('.', '_')}.log"
        log_path.write_text(
            completed.stdout + ("\nSTDERR\n" + completed.stderr if completed.stderr else ""),
            encoding="utf-8",
        )
        result = {
            "order": order,
            "title": title,
            "module": module,
            "return_code": completed.returncode,
            "duration_seconds": round(duration, 2),
            "log_path": str(log_path),
        }
        results.append(result)
        if completed.returncode != 0:
            print(f"  ล้มเหลว (FAILED) — ดูรายละเอียดที่ {log_path}")
            write_run_state(results, "failed", started_at, time.time() - started_clock)
            print(completed.stderr)
            raise SystemExit(completed.returncode)
        print(f"  สำเร็จในเวลา {duration:.1f} วินาที")

    check = verify_artifacts()
    status = "complete" if check["complete"] else "incomplete"
    write_run_state(results, status, started_at, time.time() - started_clock)
    if not check["complete"]:
        raise RuntimeError(f"ไฟล์ผลลัพธ์ที่จำเป็นสูญหาย: {check['missing']}")

    print("=" * 78)
    print(f"เสร็จสมบูรณ์ — ตรวจสอบไฟล์ผลลัพธ์ผ่านทั้งหมด {check['required_count']} รายการ")
    print(f"เวลารวมทั้งหมด: {time.time() - started_clock:.1f} วินาที")
    print("=" * 78)


if __name__ == "__main__":
    main()
