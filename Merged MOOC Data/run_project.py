"""Run the governed 11-step MOOC workflow from raw files to dashboard."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ.setdefault("NUMBA_CACHE_DIR", os.path.join(tempfile.gettempdir(), "mooc_numba_cache"))
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "mooc_matplotlib_cache"))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

STEPS = [
    (1, "Problem Definition", "src.step1_problem_definition", "run_problem_definition"),
    (2, "Data Collection and Provenance", "src.step2_data_gathering", "run_data_gathering"),
    (3, "Data Cleaning and Student Aggregation", "src.step3_data_cleaning", "run_data_cleaning"),
    (4, "Exploratory Data Analysis", "src.step4_eda", "run_eda"),
    (5, "Steps 5–8: Track Features, Selection, Training and Evaluation", "src.track_analysis", "run_track_analysis"),
    (9, "Deployment Packaging and Runtime Verification", "src.track_deployment", "run_track_deployment"),
    (10, "Bilingual Dashboard", "src.generate_report", "run_generate_report"),
    (11, "Monitoring Baseline and Feedback Loop", "src.track_monitoring", "run_track_monitoring"),
]

REQUIRED_ARTIFACTS = [
    "Merged_Workflow.md", "agy_workflow_Merged.md", "config/project_config.json", "requirements.txt",
    "data/processed/data_provenance.json", "outputs/tables/source_file_inventory.csv",
    "outputs/tables/raw_column_profile.csv", "outputs/tables/raw_column_value_counts.csv",
    "data/processed/enrollments_cleaned.parquet", "data/processed/enrollments_cleaned.csv.gz",
    "data/processed/students_cleaned.parquet", "data/processed/students_cleaned.csv.gz",
    "outputs/tables/missing_value_decisions.csv", "outputs/tables/course_offering_profile.csv",
    "outputs/tables/distribution_diagnostics.csv", "outputs/tables/segment_comparison.csv",
    "outputs/tables/activity_outlier_audit.csv", "outputs/tables/video_quality_audit.csv",
    "outputs/tables/segment_feature_distributions.csv",
    "data/quarantine/outcome_quality_flags.parquet", "data/quarantine/supervised_outcomes_cleaned.parquet",
    "outputs/tables/k_selection_elbow.csv", "outputs/tables/unsupervised_model_comparison.csv",
    "outputs/tables/gap_statistic_by_k.csv", "outputs/tables/k_selection_decision.csv",
    "outputs/tables/k_sensitivity_multiseed_runs.csv", "outputs/tables/k_sensitivity_multiseed_audit.csv",
    "outputs/tables/deep_learning_model_comparison.csv", "outputs/tables/supervised_model_comparison.csv",
    "outputs/tables/supervised_confusion_matrices_comparison.csv",
    "outputs/tables/supervised_feature_specification.csv", "outputs/tables/supervised_transformed_features.csv",
    "outputs/tables/llm_method_availability.csv", "outputs/tables/llm_student_text_inputs.csv",
    "outputs/tables/llm_text_classifier_comparison.csv", "outputs/tables/llm_text_confusion_matrices.csv",
    "outputs/tables/llm_text_test_predictions.csv", "outputs/tables/llm_task_definition.csv",
    "outputs/tables/llm_generative_model_comparison.csv", "outputs/tables/llm_api_provider_status.csv",
    "outputs/tables/llm_api_predictions_all.csv", "outputs/reproducibility/llm_api_benchmark_manifest.json",
    "outputs/figures/tracks/llm_text_model_comparison.png", "outputs/figures/tracks/llm_text_confusion_matrices.png",
    "models/tracks/llm_student_text_classifier.joblib",
    "outputs/reproducibility/llm_track_manifest.json",
    "outputs/tables/deployment_runtime.csv", "outputs/data/unsupervised_cluster_assignments.csv",
    "outputs/data/deep_certification_predictions.csv", "outputs/data/supervised_certification_predictions.csv",
    "outputs/figures/tracks/kmeans_elbow.png", "outputs/figures/tracks/behavior_hyperspace_3d.png",
    "outputs/figures/tracks/unsupervised_model_radar.png", "outputs/figures/tracks/cluster_profile_radar.png",
    "outputs/figures/tracks/multi_metric_k_selection_gap.png", "outputs/figures/tracks/persona_proportions.png",
    "outputs/figures/tracks/deep_model_comparison.png", "outputs/figures/tracks/deep_confusion_matrices.png",
    "outputs/figures/tracks/deep_roc_calibration.png",
    "outputs/figures/tracks/supervised_model_comparison.png", "outputs/figures/tracks/certification_class_balance.png",
    "outputs/figures/tracks/supervised_confusion_matrix.png", "outputs/figures/tracks/supervised_confusion_matrices_comparison.png",
    "outputs/figures/eda/full_distributions.png", "outputs/figures/eda/robust_boxplots.png",
    "outputs/figures/eda/zero_missing_outlier_profile.png", "outputs/figures/eda/behavior_relationships.png",
    "outputs/figures/eda/activity_outlier_diagnostics.png", "outputs/figures/eda/video_quality_diagnostics.png",
    "outputs/figures/tracks/segment_feature_comparison.png", "outputs/figures/tracks/segment_outcome_comparison.png",
    "outputs/figures/tracks/segment_cluster_comparison.png", "outputs/figures/tracks/segment_distribution_comparison.png",
    "models/tracks/unsupervised_pipeline.joblib", "models/tracks/deep_certification_pipeline.joblib",
    "models/tracks/supervised_certification_pipeline.joblib",
    "models/tracks/input_contract.json", "models/tracks/model_cards.md",
    "outputs/reproducibility/analysis_tracks_manifest.json",
    "outputs/reproducibility/dashboard_segment_summary.json",
    "reports/student_segmentation_report.html", "reports/report_manifest.json",
    "monitoring/track_monitoring_baseline.json", "monitoring/track_monitoring_config.json",
    "monitoring/track_monitoring_history.csv", "monitoring/track_retraining_decision.json",
]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def run_step(module_name, function_name):
    module = importlib.import_module(module_name)
    getattr(module, function_name)()


def verify_artifacts():
    report, missing = {}, []
    for relative in REQUIRED_ARTIFACTS:
        exists = os.path.exists(relative)
        item = {"exists": exists}
        if exists:
            size = os.path.getsize(relative)
            item.update({"size_bytes": size, "sha256": sha256(relative) if size < 50 * 1024 * 1024 else "skipped_large_file"})
        else:
            missing.append(relative)
        report[relative] = item
    os.makedirs("outputs/reproducibility", exist_ok=True)
    with open("outputs/reproducibility/artifact_check.json", "w", encoding="utf-8") as handle:
        json.dump({"verified_artifacts": report, "all_passed": not missing}, handle, indent=2)
    return missing


def write_status(step_times, total_runtime, missing):
    with open("outputs/reproducibility/analysis_tracks_manifest.json", encoding="utf-8") as handle:
        tracks = json.load(handle)
    status = {
        "workflow": "11-step governed data-science workflow",
        "steps": {
            "1": "Completed", "2": "Completed", "3": "Completed", "4": "Completed",
            "5": "Completed", "6": "Completed", "7": "Completed", "8": "Completed",
            "9": "Completed", "10": "Completed",
            "11": "Baseline Ready; evaluation waits for a genuine future cohort",
        },
        "tracks": {
            "Traditional Unsupervised": "Completed",
            "Deep Learning": "Completed",
            "Supervised Learning": "Completed",
            "Generative AI Student Text Classification": "Gemini completed on 1,800 unseen students; GPT pending OpenAI API credit",
        },
        "actual_results": {
            "students": tracks["students"],
            "unsupervised_selected_model": tracks["traditional_unsupervised"]["selected_family"],
            "unsupervised_selected_k": tracks["traditional_unsupervised"]["selected_k"],
            "supervised_selected_model": tracks["supervised_learning"]["selected_model_name"],
            "supervised_source_features": tracks["supervised_learning"]["source_feature_count"],
            "supervised_transformed_features": tracks["supervised_learning"]["transformed_feature_count"],
            "deep_learning_selected_model": tracks["deep_learning"]["selected_model_name"],
            "llm_status": tracks["generative_llm"]["status"],
        },
        "step_runtime_seconds": step_times,
        "total_runtime_seconds": round(total_runtime, 3),
        "artifact_verification": {"required": len(REQUIRED_ARTIFACTS), "missing": missing},
        "status": "SUCCESS" if not missing else "INCOMPLETE",
    }
    with open("outputs/reproducibility/workflow_status.json", "w", encoding="utf-8") as handle:
        json.dump(status, handle, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-step", type=int, choices=range(1, 12), default=1)
    args = parser.parse_args()
    started, step_times = time.perf_counter(), {}
    for number, name, module, function in STEPS:
        if number < args.from_step:
            print(f"[REUSE] Step {number}: {name}")
            continue
        print(f"\n[RUN] Step {number}: {name}")
        t0 = time.perf_counter()
        run_step(module, function)
        step_times[f"Step {number}: {name}"] = round(time.perf_counter() - t0, 3)

    print("\n[VERIFY] Active workflow tests")
    run_step("tests.test_data_layer", "run_all_tests")
    run_step("tests.test_tracks", "run_all_tests")
    missing = verify_artifacts()
    total = time.perf_counter() - started
    write_status(step_times, total, missing)
    if missing:
        raise RuntimeError(f"Missing required artifacts: {missing}")
    print(f"[SUCCESS] Workflow and {len(REQUIRED_ARTIFACTS)} active artifacts verified in {total:.2f}s")


if __name__ == "__main__":
    main()
