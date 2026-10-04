"""Step 9: package and verify the portable deployment pipeline."""

from __future__ import annotations

import importlib.metadata
import json
import os

import joblib
import pandas as pd

from src.deployment import MoocStudentSegmentationPipeline


FINAL_DIR = os.path.join("models", "final")
MODEL_PATH = os.path.join(FINAL_DIR, "cluster_model.joblib")
PREPROCESSING_PATH = os.path.join("models", "preprocessing_pipeline.joblib")
PIPELINE_PATH = os.path.join(FINAL_DIR, "clustering_pipeline.joblib")
PROFILES_PATH = os.path.join("outputs", "tables", "cluster_profiles.csv")
STUDENTS_PATH = os.path.join("data", "processed", "students_cleaned.parquet")
CONFIG_PATH = os.path.join("config", "project_config.json")
STUDENT_INPUT_COLUMNS = [
    "userid_DI", "n_courses", "view_rate", "total_events",
    "total_active_days", "total_chapters", "total_forum_posts",
    "overall_span_days",
]


def build_metadata() -> dict[int, dict]:
    profiles = pd.read_csv(PROFILES_PATH)
    return {
        int(row.cluster): {
            "cluster_name": row.cluster_name,
            "neutral_descriptor": row.neutral_descriptor,
        }
        for row in profiles.itertuples()
    }


def write_schema(students: pd.DataFrame, config: dict):
    required = STUDENT_INPUT_COLUMNS
    schema = {
        "unit_of_analysis": "one row per userid_DI",
        "required_student_level_columns": required,
        "observed_dtypes": {column: str(students[column].dtype) for column in required},
        "forbidden_outcome_columns": config["outcome_columns"],
        "nullable_columns": ["overall_span_days"],
        "whole_number_columns": [
            "n_courses", "total_events", "total_active_days",
            "total_chapters", "total_forum_posts",
        ],
        "range_rules": {
            "n_courses": "at least 1",
            "view_rate": "between 0 and 1 inclusive",
            "counts_and_span": "non-negative; overall_span_days may be missing",
        },
        "derived_inside_pipeline": {
            "event_intensity": "total_events / max(total_active_days, 1)"
        },
        "duplicate_policy": "Reject duplicate userid_DI in student-level input; use raw mode for repeated person-course records.",
        "supported_new_data": "A later cohort with the same raw or student-level data contract.",
        "incompatible_data_policy": "A dataset with different fields or meaning must restart the workflow from Step 2 and train a new model.",
        "unknown_category_policy": "Accepted for non-clustering contextual fields.",
        "validation_policy": "Reject missing fields, invalid dtypes/ranges, duplicate students, non-finite values, and outcome columns.",
    }
    with open(os.path.join(FINAL_DIR, "input_schema.json"), "w", encoding="utf-8") as handle:
        json.dump(schema, handle, indent=2)


def write_environment():
    packages = [
        "joblib", "matplotlib", "numpy", "pandas", "pyarrow",
        "scikit-learn", "scipy", "seaborn",
    ]
    lines = [f"{name}=={importlib.metadata.version(name)}" for name in packages]
    with open("requirements.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def write_model_card(lock: dict):
    content = f"""# Student Segmentation Model Card

## Model

- Algorithm: {lock['algorithm']}
- Cluster count selected from internal evidence: {lock['n_clusters']}
- Training population: {lock['population_size_used_for_final_fit']:,} students
- Features: {', '.join(lock['feature_names'])}
- Model checksum: {lock['cluster_model_sha256']}

## Intended use

Exploratory segmentation for responsible student-support planning. Cluster assignments describe observed behavioral similarity; they are not grades, diagnoses, or deterministic risk labels.

## Prohibited use

Do not use the model for automated penalties, admissions, grading, or denial of support. Known outcomes are rejected as inputs.

## Validation

The model was selected using internal clustering metrics, stability, interpretability, and reproducibility. Educational outcomes were accessed only after the model lock for descriptive post-hoc validation.

## Limitations

The source covers historical HarvardX/MITx courses. Video activity is substantially missing and is excluded from the core model. Clusters may drift with courses, platform instrumentation, and student populations.

## New-data contract

The saved pipeline supports later cohorts with the same raw MOOC schema or the documented student-level schema. It derives event intensity internally and rejects outcome columns, invalid values, and duplicate student rows. A dataset with different fields or meanings requires a new workflow run from Step 2; the locked model must not be reused as if the schemas were interchangeable.
"""
    with open(os.path.join(FINAL_DIR, "model_card.md"), "w", encoding="utf-8") as handle:
        handle.write(content)


def build_and_save_pipeline():
    os.makedirs(FINAL_DIR, exist_ok=True)
    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)
    preprocessing = joblib.load(PREPROCESSING_PATH)
    model = joblib.load(MODEL_PATH)
    pipeline = MoocStudentSegmentationPipeline(
        preprocessing,
        model,
        cluster_metadata=build_metadata(),
        forbidden_outcome_columns=config["outcome_columns"],
    )
    joblib.dump(pipeline, PIPELINE_PATH)

    students = pd.read_parquet(STUDENTS_PATH)
    write_schema(students, config)
    write_environment()
    with open(os.path.join(FINAL_DIR, "model_lock.json"), encoding="utf-8") as handle:
        lock = json.load(handle)
    write_model_card(lock)

    reloaded = joblib.load(PIPELINE_PATH)
    smoke = reloaded.predict_student_profiles(students.head(25))
    if len(smoke) != 25 or smoke["cluster"].isna().any():
        raise RuntimeError("Deployment smoke test failed.")
    os.makedirs("examples", exist_ok=True)
    example_input = students.loc[:, STUDENT_INPUT_COLUMNS].head(10)
    example_input.to_csv(os.path.join("examples", "student_level_input.csv"), index=False)
    reloaded.predict_student_profiles(example_input).to_csv(
        os.path.join("examples", "student_cluster_output.csv"), index=False
    )
    print(f"[+] Portable pipeline saved and reloaded: {PIPELINE_PATH}")
    return pipeline


if __name__ == "__main__":
    build_and_save_pipeline()
