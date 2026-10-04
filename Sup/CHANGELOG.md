# Supervised Project Revision & Implementation Log (CHANGELOG)

## Overview
This repository contains the complete, production-grade supervised machine learning pipeline for **Student Risk & Performance Segmentation**, developed according to the 11-step framework outlined in `Workflow.md` and formalized in `agy_workflow_Sup.md`.

---

## Key Architectural Highlights

1. **Strict Anti-Leakage Isolation (Step 2 & Step 3)**
   - Outcome variables (`certified`, `grade`, `incomplete_flag`, `explored`) were physically partitioned into an isolated label store (`data/labels/raw_targets.parquet` and `student_labels.parquet`).
   - The feature matrix ($X$) is strictly validated to contain 0 outcome indicators, preventing trivial or spurious classification accuracy.

2. **Clean Student-Level Unit of Analysis (Step 3)**
   - Aggregated 416,921 enrollment records to 335,650 unique students (`userid_DI`).
   - Converted the undocumented video placeholder (`197757`) to `NaN` while adding a `video_data_available_rate` feature.
   - Handled date inversions and invalid ages ($age \le 0$ or $> 100$).

3. **Split-Disciplined Feature Engineering (Step 5)**
   - Performed Stratified Splitting (70% Train, 15% Validation, 15% Test) prior to any feature transformation.
   - Fitted all imputers, log1p scalers, and categorical encoders strictly on $X_{train}$.

4. **Multi-Family Candidate Benchmarking (Steps 6 & 7)**
   - Evaluated 14 configurations from 10 explicitly separated families (including the null baseline):
     - Baseline heuristic (DummyClassifier)
     - Logistic Regression and scalable ElasticNet SGD
     - Gaussian Naive Bayes
     - Calibrated Linear SVM
     - Single Decision Tree
     - Random Forest and Extra Trees
     - HistGradientBoostingClassifier
     - Multi-Layer Perceptron
   - Generated `candidate_models.csv` directly from the estimators trained by code, preventing documentation/model-list drift.
   - Selected the winner on the validation partition by PR-AUC, then ROC-AUC, then Brier Score; the holdout test set did not choose the model.

5. **Operational Risk Tiering & Threshold Calibration (Step 8)**
   - Optimized decision threshold $\tau^*$ to maximize F1 and capture at-risk learners.
   - Segmented predictions into 3 operational support tiers:
     - **Tier 1 (Low Risk / Likely Completer):** $\hat{p} \ge 0.50$
     - **Tier 2 (Moderate Risk / Target for Nudge):** $0.15 \le \hat{p} < 0.50$
     - **Tier 3 (High Risk / Early Dropout):** $\hat{p} < 0.15$
   - Validated against holdout test set with ROC-AUC, PR-AUC, Brier score, and reliability curves.

6. **Deployment Packaging & Safety Contract (Step 9)**
   - Exported portable `MoocStudentRiskPipeline` with embedded schema validation.
   - Implemented automated exception handling (`DataLeakageSecurityException`) that immediately rejects inference requests containing target fields.
   - 10 comprehensive unit and integration tests passing in `tests/test_pipeline.py`.

7. **Interactive HTML Dashboard (Step 10)**
   - Fully standalone, presentation-ready report (`reports/student_risk_prediction_report.html`).
   - Contains executive KPIs, literature review, exploratory charts, model curves, fairness audits, limitations, and monitoring evidence.

8. **Monitoring Baseline & Governance Protocol (Step 11)**
   - Established reference distributions, PSI alert thresholds, and explicit retraining triggers.

9. **Feedback Loop & Workflow.md Full Alignment Revision (September 2026)**
   - Re-aligned `agy_workflow_Sup.md` to meticulously cover all 11 numbered steps, sub-bullets, the Model Optimization Cycle (Steps 5–8 iteration policy), and the Feedback Loop (returning to Step 2 upon significant drift).
   - Re-generated `reports/student_risk_prediction_report.html` and `reports/report_manifest.json` with an executive top navigation bar and all 11 steps + Optimization Cycle + Feedback Loop explicitly articulated and rendered.

10. **Bilingual 3-Column Layout Overhaul & Sticky Right Simulator (September 2026)**
    - Re-architected dashboard layout: Left Slide-out Hidden Drawer (`slide-drawer` with backdrop), Center detailed content column with strict bounds containment (`minmax(0, 1fr)`), and Right Sticky Interactive Simulator (`simulator-sticky-panel`).
    - Implemented client-side English/Thai instant language switcher (`🌐 EN | TH`) with English as the primary default language and full bilingual support across all sections, KPIs, tables, and simulator recommendations.
    - Added strict bounding rules preventing any text, tables, or code blocks from overflowing card borders.

11. **Verified Random Forest Prediction Interface (September 2026)**
    - Removed the approximate JavaScript Scenario Explorer because it did not call the trained model.
    - Added `prediction_app.py`, a CSV upload/download interface that invokes `models/final/deployment_pipeline.joblib` directly.
    - Kept the upload interface separate from the standalone HTML report so the dashboard contains only report evidence.
    - Strengthened inference validation: all non-derived training inputs are required, deterministic features are recomputed, and missing fields are no longer silently replaced with zero.
    - Regenerated the complete input schema and schema-complete sample CSV from observed student profiles.
    - Corrected dashboard age-cleaning text and the invalid-age percentage (241 records; 0.058%).
