# workflow_docs/phase_3/step_3_1.md

## Phase 3 – Feature Extraction & Multimodal Fusion

**Goal:** Extract HRV and morphological features from cleaned 12‑lead ECG signals and fuse them with patient‑level metadata.

**Key actions**
- Load cleaned waveforms (`data/cleaned/…`) and interim metadata (`data/interim/ptbxl_interim_metadata.csv`).
- Run Pan‑Tompkins R‑peak detection on Lead II (fallback to Lead V5).
- Compute HRV time‑domain metrics (SDNN, RMSSD, pNN50) and frequency‑domain metrics (LF, HF, LF/HF).
- Extract morphology: QRS duration, PR interval, QT interval, ST‑segment elevation/depression per relevant lead.
- Collapse each encounter (`ecg_id`) to a single feature row while preserving the composite key (`patient_id` + `ecg_id`).
- Validate grain consistency (no duplicate rows, correct joins).
- Persist the ML‑ready table to `data/processed/ptbxl_processed_features.parquet`.

**Reference implementation:** `src/features/extract_hrv.py`
