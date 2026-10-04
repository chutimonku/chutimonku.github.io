# workflow_docs/phase_5/step_5_1.md

## Phase 5 – Dashboard / Patient Longitudinal Inspection & XAI

**Goal:** Provide an interactive exploration UI that lets clinicians browse a patient’s longitudinal ECG history, view model predictions with confidence scores, visualize filtered 12‑lead waveforms, and inspect feature‑level explanations (SHAP or Integrated Gradients).

**Key actions**
- Load the processed feature set (`data/processed/ptbxl_processed_features.parquet`) and the final LightGBM model (`models/final/final_model.pkl`).
- Offer a searchable dropdown for `patient_id` and a timeline of encounters (`ecg_id`).
- For a selected encounter display:
  * Prediction probabilities per diagnostic superclass.
  * 12‑lead ECG plot (filtered signals) with highlighted R‑peaks and morphology markers.
  * Clinical metrics table (HR, HRV, QRS duration, ST‑elevation, etc.).
  * XAI overlay (SHAP bar chart) and a What‑If simulator to adjust ST‑elevation / heart‑rate.
- Log user interactions for auditability.

**Reference implementation:** `outputs/dashboard/app.py` (now split into modular page files).
