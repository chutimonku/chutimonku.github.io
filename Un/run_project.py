#!/usr/bin/env python3
"""Run the complete 11-step MOOC unsupervised clustering workflow."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent

STEPS = [
    ("Step 1: Problem Definition", "src.step1_problem_definition"),
    ("Step 2: Data Gathering & Quarantine", "src.step2_data_gathering"),
    ("Step 3: Data Cleaning", "src.step3_data_cleaning"),
    ("Step 4: EDA & Data Quality Audit", "src.step4_eda"),
    ("Step 5: Feature Engineering", "src.step5_feature_engineering"),
    ("Step 6: Broad Clustering Family Screening", "src.step6_model_family_screening"),
    ("Step 6-7: K Selection & Model Training", "src.step6_7_model_training"),
    ("Step 8: Evaluation & Post-hoc Validation", "src.step8_evaluation_and_posthoc"),
    ("Step 8: Extended Unsupervised Diagnostics", "src.step8_extended_analysis"),
    ("Step 9: Deployment Packaging", "src.deployment"),
    ("Step 11: Monitoring Baseline", "src.step11_monitoring"),
    ("Step 10: Final Bilingual Dashboard Assembly", "src.generate_report")
]

REQUIRED_ARTIFACTS = [
    "data/processed/problem_definition.json",
    "data/processed/raw_features.parquet",
    "data/quarantine/raw_outcomes.parquet",
    "data/processed/enrollments_cleaned.parquet",
    "data/processed/students_cleaned.parquet",
    "data/processed/feature_matrix.parquet",
    "outputs/tables/k_selection_metrics.csv",
    "outputs/tables/broad_clustering_benchmark.csv",
    "outputs/tables/clustering_family_recommendation.json",
    "outputs/figures/modeling/k_selection_four_metrics.png",
    "outputs/data/cluster_assignments.csv",
    "outputs/tables/cluster_profiles.csv",
    "outputs/tables/cluster_validation_summary.json",
    "outputs/tables/unsupervised_model_comparison.csv",
    "outputs/tables/cluster_feature_contribution.csv",
    "outputs/tables/feature_ablation_sensitivity.csv",
    "outputs/tables/student_persona_dossiers.csv",
    "outputs/data/cluster_assignment_diagnostics.csv",
    "outputs/data/interactive_simulator_spec.json",
    "models/final/clustering_pipeline.joblib",
    "models/final/input_schema.json",
    "models/final/model_lock.json",
    "reports/student_segmentation_report.html",
    "monitoring/monitoring_report.json",
    "monitoring/retraining_decision.json"
]

LOGS_DIR = ROOT_DIR / "outputs/logs"
REPRO_DIR = ROOT_DIR / "outputs/reproducibility"
RUN_MANIFEST_PATH = REPRO_DIR / "run_manifest.json"
ARTIFACT_CHECK_PATH = REPRO_DIR / "artifact_check.json"


def sha256_file(path: Path) -> str:
    """Return SHA-256 of a file without loading it all into memory."""
    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def verify_artifacts() -> dict:
    """Check required outputs after all workflow steps complete."""
    artifacts = []

    for relative_path in REQUIRED_ARTIFACTS:
        full_path = ROOT_DIR / relative_path
        exists = full_path.exists() and full_path.is_file()

        artifacts.append({
            "path": relative_path,
            "exists": exists,
            "size_bytes": full_path.stat().st_size if exists else None,
            "sha256": sha256_file(full_path) if exists else None
        })

    missing = [
        artifact["path"]
        for artifact in artifacts
        if not artifact["exists"]
    ]

    return {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete": len(missing) == 0,
        "missing_artifacts": missing,
        "artifacts": artifacts
    }


def write_manifest(
    status: str,
    started_at_utc: str,
    step_results: list[dict],
    artifact_check: dict | None = None
) -> None:
    """Persist pipeline status even when a step fails."""
    REPRO_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "workflow": "MOOC Unsupervised Student Segmentation",
        "status": status,
        "started_at_utc": started_at_utc,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_executable": sys.executable,
        "project_root": str(ROOT_DIR),
        "steps": step_results,
        "artifact_check": artifact_check
    }

    RUN_MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def main() -> None:
    os.chdir(ROOT_DIR)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    REPRO_DIR.mkdir(parents=True, exist_ok=True)

    started_at_utc = datetime.now(timezone.utc).isoformat()
    started_at = time.perf_counter()

    environment = os.environ.copy()

    # Keep this project root importable when modules run as subprocesses.
    environment["PYTHONPATH"] = str(ROOT_DIR)

    step_results: list[dict] = []

    print("=" * 78)
    print("MOOC UNSUPERVISED STUDENT SEGMENTATION — 11-STEP PIPELINE")
    print("=" * 78)
    print(f"Project root: {ROOT_DIR}")
    print(f"Python: {sys.executable}")

    for step_number, (step_title, module_name) in enumerate(STEPS, start=1):
        print(f"\n[{step_number:02d}/{len(STEPS):02d}] {step_title}")

        step_started_at = time.perf_counter()

        completed = subprocess.run(
            [sys.executable, "-m", module_name],
            cwd=ROOT_DIR,
            env=environment,
            capture_output=True,
            text=True
        )

        runtime_seconds = time.perf_counter() - step_started_at

        log_path = LOGS_DIR / (
            f"{step_number:02d}_{module_name.replace('.', '_')}.log"
        )

        log_text = (
            f"STEP: {step_title}\n"
            f"MODULE: {module_name}\n"
            f"RETURN CODE: {completed.returncode}\n"
            f"RUNTIME_SECONDS: {runtime_seconds:.3f}\n\n"
            f"STDOUT\n{'=' * 72}\n"
            f"{completed.stdout}\n\n"
            f"STDERR\n{'=' * 72}\n"
            f"{completed.stderr}\n"
        )

        log_path.write_text(log_text, encoding="utf-8")

        result = {
            "step_number": step_number,
            "step_title": step_title,
            "module": module_name,
            "return_code": completed.returncode,
            "runtime_seconds": round(runtime_seconds, 3),
            "log_path": str(log_path.relative_to(ROOT_DIR))
        }

        step_results.append(result)

        if completed.returncode != 0:
            print(f"  FAILED — see log: {log_path}")

            write_manifest(
                status="failed",
                started_at_utc=started_at_utc,
                step_results=step_results
            )

            raise RuntimeError(
                f"Pipeline stopped at Step {step_number}: {step_title}"
            )

        print(f"  PASSED in {runtime_seconds:.1f} seconds")

    artifact_check = verify_artifacts()

    ARTIFACT_CHECK_PATH.write_text(
        json.dumps(artifact_check, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    final_status = (
        "complete"
        if artifact_check["complete"]
        else "incomplete"
    )

    write_manifest(
        status=final_status,
        started_at_utc=started_at_utc,
        step_results=step_results,
        artifact_check=artifact_check
    )

    if not artifact_check["complete"]:
        missing_text = "\n- ".join(
            artifact_check["missing_artifacts"]
        )

        raise RuntimeError(
            "Pipeline steps finished but required artifacts are missing:\n- "
            + missing_text
        )

    elapsed_seconds = time.perf_counter() - started_at

    print("\n" + "=" * 78)
    print("PIPELINE COMPLETE")
    print("=" * 78)
    print(f"Total runtime: {elapsed_seconds:.1f} seconds")
    print(f"Run manifest: {RUN_MANIFEST_PATH}")
    print(f"Artifact check: {ARTIFACT_CHECK_PATH}")
    print("Dashboard report: reports/student_segmentation_report.html")


if __name__ == "__main__":
    main()
