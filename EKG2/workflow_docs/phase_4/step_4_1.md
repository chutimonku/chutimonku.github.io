# workflow_docs/phase_4/step_4_1.md

## Phase 4 – Model Training & GroupKFold Validation

**Goal:** Train a multi‑class classifier for the five diagnostic super‑classes while guaranteeing patient‑level isolation using `GroupKFold`.

**Key actions**
- Load the processed feature table (`data/processed/ptbxl_processed_features.parquet`).
- Split the data with `GroupKFold` (default 5‑fold) using `patient_id` as the grouping column.
- Train a LightGBM `LGBMClassifier` (or other configurable model) on each fold.
- Record per‑fold metrics (accuracy, macro‑F1, macro‑ROC‑AUC) and overall averages.
- Save each fold model (`models/fold_{i}.pkl`) and the final model trained on the full data (`models/final/final_model.pkl`).
- Persist a comprehensive experiment log (`logs/experiment_log.json`).

**Reference implementation:** `src/training/train_model.py`
