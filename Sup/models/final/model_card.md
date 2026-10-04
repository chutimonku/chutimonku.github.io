# Model Card: Student Risk & Performance Segmentation

## Model Details
- **Model Name:** MoocStudentRiskClassifier (RandomForestClassifier)
- **Version:** 1.0.0
- **Model Type:** Supervised Binary Classification with Calibrated Risk Tiering
- **Algorithm:** RandomForestClassifier (selected from validation results before holdout interpretation)
- **Artifact Path:** `models/final/deployment_pipeline.joblib`
- **Model File SHA-256:** `1af5eeee4ad0b0c4db3ebbe07d2a72048d53dbca8bf4caa561ce27acd2484972`
- **License / Governance:** Institutional Educational Analytics (Internal Decision Support)
- **Framework:** scikit-learn 1.6.1 / Python 3.13

## Intended Use
- **Primary Use Case:** Identify learners at imminent risk of course non-completion to deliver timely academic nudges, study group invitations, and prerequisite support.
- **Decision Tiers:**
  - **Tier 1 (Low Risk / Likely Completer, p >= 0.50):** Eligible for advanced material, peer mentoring opportunities.
  - **Tier 2 (Moderate Risk / Nudge Needed, 0.15 <= p < 0.50):** Targeted reminders, milestone checklists, advising outreach.
  - **Tier 3 (High Risk / Early Dropout, p < 0.15):** Urgent onboarding assistance, prerequisite remediation, technical support.
- **Target Users:** Academic advisors, course instructional teams, learning support personnel.
- **Out-of-Scope / Prohibited Uses:**
  - Automated dropping or cancellation of student enrollments.
  - Punitive grading or academic probation decisions.
  - Discriminatory admissions or credit-denial decisions.

## Training & Validation Data
- **Source:** HarvardX-MITx Academic Year 2013 MOOC Cohort (Kaggle dataset).
- **Unit of Analysis:** Exactly one row per student (`userid_DI`).
- **Student Cohort Size:** 335,650 unique students across 13 open online courses.
- **Partitioning:** Stratified 70% Train (234,955), 15% Validation (50,347), 15% Test (50,348).
- **Class Imbalance:** 4.13% Positive Class (Certified Completers), 95.87% Negative Class (Non-Completers).

## Quantitative Performance
- **Test ROC-AUC:** 0.9933
- **Test PR-AUC (Average Precision):** 0.8476 (vs. 0.0413 baseline)
- **Test Brier Score:** 0.0216
- **Optimal Decision Threshold (τ*):** 0.8404
- **Test Recall at τ*:** 0.842
- **Test Precision at τ*:** 0.7422
- **Test F1-Score at τ*:** 0.7889

## Ethical Considerations & Anti-Leakage Safeguards
- **Data Leakage Security:** The model rejects any input containing known outcome variables (`certified`, `grade`, `incomplete_flag`, `explored`).
- **Fairness & Disparity Audits:** True positive rates and error parity are audited across gender, education levels, and geographic regions. Demographic attributes are not primary decision drivers; fine-grained engagement behaviors dominate feature importance.
- **Human-in-the-Loop:** Predictions are guidance recommendations for human advisors, never autonomous administrative actions.
