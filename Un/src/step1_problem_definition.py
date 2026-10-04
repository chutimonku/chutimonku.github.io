#!/usr/bin/env python3
"""Step 1: Define the unsupervised MOOC student-segmentation problem."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


CONFIG_PATH = Path("config/project_config.json")
OUTPUT_PATH = Path("data/processed/problem_definition.json")


def main() -> None:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing configuration file: {CONFIG_PATH}. "
            "Create config/project_config.json before running Step 1."
        )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    required_keys = [
        "project",
        "task_type",
        "unit_of_analysis",
        "behavior_features",
        "outcome_columns",
        "candidate_k_range",
        "k_selection_metrics",
    ]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(
            "project_config.json is missing required keys: "
            + ", ".join(missing_keys)
        )

    if config["task_type"] != "unsupervised_clustering":
        raise ValueError(
            "This workflow requires task_type='unsupervised_clustering'."
        )

    if len(config["behavior_features"]) != 4:
        raise ValueError(
            "This workflow requires exactly four behavioral clustering features."
        )

    problem_definition = {
        "project": config["project"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_step": 1,
        "task_type": "unsupervised_clustering",
        "unit_of_analysis": config["unit_of_analysis"],
        "primary_objective_th": (
            "แบ่งกลุ่มผู้เรียน MOOC จากพฤติกรรมการเรียนจริง "
            "เพื่อสนับสนุนการวางแผนช่วยเหลือผู้เรียนอย่างรับผิดชอบ"
        ),
        "primary_objective_en": (
            "Segment MOOC learners using observed learning behaviours "
            "to support responsible learner-support planning."
        ),
        "business_questions_th": [
            "ผู้เรียนสามารถแบ่งเป็นกลุ่มพฤติกรรมการเรียนที่แตกต่างกันได้หรือไม่",
            "จำนวนกลุ่ม K เท่าใดมีความเหมาะสมทั้งด้านคุณภาพและความเสถียร",
            "แต่ละกลุ่มมีลักษณะด้านกิจกรรม การดูวิดีโอ และการมีส่วนร่วมใน forum อย่างไร",
            "ผลลัพธ์ทางการเรียนมีความแตกต่างระหว่างกลุ่มหรือไม่ โดยตรวจหลังล็อกโมเดลแล้วเท่านั้น"
        ],
        "business_questions_en": [
            "Can learners be segmented into distinct learning-behaviour groups?",
            "Which K is supported by cluster quality and resampling stability?",
            "How do clusters differ in activity, video engagement, and forum participation?",
            "Do observed learning outcomes differ by cluster after model lock?"
        ],
        "clustering_features": config["behavior_features"],
        "feature_policy": {
            "included": "Exactly four behavioural percentile features only.",
            "excluded_profiles": config["profile_columns"],
            "excluded_outcomes": config["outcome_columns"],
            "reason_for_exclusion": (
                "Profile fields describe learner identity or context rather than "
                "learning behaviour. Outcome fields are quarantined to prevent leakage."
            )
        },
        "outcome_quarantine": {
            "columns": config["outcome_columns"],
            "policy": config["outcome_policy"],
            "allowed_use": (
                "Post-hoc cluster validation and data-quality auditing only, "
                "after the final clustering model is locked."
            ),
            "forbidden_use": [
                "EDA feature selection for clustering",
                "imputation statistics for clustering",
                "scaling for clustering",
                "K selection",
                "cluster model fitting"
            ]
        },
        "k_selection_plan": {
            "candidate_k_range": config["candidate_k_range"],
            "metrics": config["k_selection_metrics"],
            "stability_resamples": config["stability_resamples"],
            "selection_rule": (
                "Rank each candidate K by Silhouette descending, "
                "Davies-Bouldin ascending, Calinski-Harabasz descending, "
                "and mean resample Adjusted Rand Index descending. "
                "Select the lowest mean rank, then use Davies-Bouldin and K as tie-breakers."
            )
        },
        "data_quality_scope": {
            "video_policy": config["video_policy"],
            "grade_audit_policy": config["grade_audit_policy"],
            "raw_data_is_immutable": True,
            "audit_requirement": (
                "Keep raw data unchanged. Record missing values, sentinel values, "
                "duplicates, invalid dates, outliers, and outcome inconsistencies in audit outputs."
            )
        },
        "success_criteria": {
            "technical": [
                "All four clustering features are behavioural and contain no outcome columns.",
                "K selection is based on all four configured metrics.",
                "The selected K is shown with a vertical dashed line in the metric chart.",
                "Every cluster contains enough observations for interpretation.",
                "The pipeline can score compatible later cohorts using the locked preprocessing and cluster model."
            ],
            "reporting": [
                "Thai and English explanations are consistent.",
                "All claims in the dashboard are supported by generated tables or figures.",
                "Grade and certification anomalies are reported as flags, not silently corrected."
            ]
        },
        "limitations_th": [
            "ข้อมูลเป็น person-course record แบบสรุป จึงไม่สามารถใช้วัดพฤติกรรมรายสัปดาห์ได้",
            "ข้อมูลไม่มีระยะเวลาวิดีโอ จึงวิเคราะห์ได้เพียงจำนวนการเล่นวิดีโอและคุณภาพข้อมูล",
            "ผลการจัดกลุ่มเป็นเครื่องมือช่วยทำความเข้าใจพฤติกรรม ไม่ใช่การตัดสินคุณค่าหรือความสามารถของผู้เรียน"
        ],
        "limitations_en": [
            "The source contains aggregated person-course records and cannot measure weekly behaviour.",
            "The dataset has no video-duration field; analysis is limited to video-play counts and data quality.",
            "Clusters support behavioural understanding and must not be used to judge learner ability or worth."
        ]
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(problem_definition, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[Step 1] Problem definition written to: {OUTPUT_PATH}")
    print(
        "[Step 1] Behavioural clustering features: "
        + ", ".join(config["behavior_features"])
    )


if __name__ == "__main__":
    main()