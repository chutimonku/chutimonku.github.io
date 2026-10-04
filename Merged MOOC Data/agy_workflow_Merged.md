# Project Workflow: Multi-Track MOOC Student Analytics

**Governing workflow:** `Merged_Workflow.md`  
**Project version:** 3.0.0  
**Unit of analysis:** one row per student (`userid_DI`) after preserving a separate enrollment-level clean table  
**Sources:** HarvardX official DOI file and the project-supplied HarvardX–MITx Kaggle file  
**Tracks:** Traditional Unsupervised, Deep Learning, Supervised Learning, and Generative LLM-supported communication  
**Governance:** outcomes never influence clustering; certification is permitted only as the declared target of the separate supervised track.

## 1. Problem Definition

- Define the data-quality, behavioral-segmentation, and certification-prediction questions separately.
- Record unit of analysis, task type, constraints, success criteria, ethical limits, and project/data/schema versions.
- **Output:** `data/processed/problem_definition.json`.

## 2. Data Collection

- Load both named source files; record URL, filename, checksum, rows, columns, duplicates, students, course offerings, scope, rationale, and limitations.
- Preserve raw files and physically quarantine `certified`, `grade`, `viewed`, `explored`, and `incomplete_flag` from non-outcome inputs.
- **Outputs:** provenance JSON/report, source inventory, raw non-outcomes, quarantined outcomes, and quarantine manifest.

## 3. Data Understanding and Cleaning

- Audit every source column: data type, missing count/rate, distinct count, descriptive statistics, and complete/top category counts.
- Deduplicate cross-source enrollment overlaps by `(userid_DI, institute, course_id, year, semester)` while retaining legitimate multi-course records.
- Convert the video sentinel to missing with an indicator; set invalid ages to missing; map missing demographics including gender to `Unknown`.
- Swap valid reversed start/end date pairs, keep original values, and record a repair flag instead of deleting the student.
- Profile every course offering because course duration and activity opportunity differ; create within-course behavioral percentiles.
- Audit outcome consistency. Keep contradictions in quarantine evidence and exclude only definitively invalid labels from supervised eligibility; never remove them to improve clustering.
- Export both clean enrollment-level data (more than 500,000 rows) and one-row-per-student data, plus an append-only processing log.
- **Outputs:** clean Parquet/CSV.gz files, missing-value decisions, all-column profiles/value counts, course profiles, quality flags, class-balance audit, and cleaning log.

## 4. Exploratory Data Analysis (EDA)

- Examine distributions, outliers, missingness, correlations, imbalance, dimensionality, and institution/course differences.
- Show data hyperspace with a 3D projection for visualization only; do not use plot coordinates as hidden model evidence.
- Explain how findings affect transformations, sampling, feature choice, metrics, and model families.
- **Outputs:** EDA tables, research notes, and figures.

## 5. Feature Engineering and Data Preparation

- Keep one clean master cohort, then create a different governed feature set for each task.
- **Traditional/Deep:** select eligible non-outcome behavioral features from the merged clean data using coverage, variance, redundancy, and leakage rules. Exclude profiles and outcomes.
- **Supervised:** select eligible pre-outcome source features from the merged clean data; exclude identifiers, raw dates, provenance/quality flags, majority-missing fields, high-cardinality categoricals, and near-duplicate numeric fields. Fit imputation/scaling/encoding on training data only and record the actual transformed columns.
- Export feature specifications and transformed-feature names.

## 6. Analysis and Model Selection

- Review cited research and include only methods supported by the data and objective.
- **Traditional:** K-Means, MiniBatch K-Means, GMM, BIRCH, HAC, DBSCAN, and approximate K-Medoids.
- **Deep:** Autoencoder representation followed by K-Means or GMM.
- **Supervised:** baseline, Logistic Regression, Decision Tree, Random Forest, Extra Trees, Gradient Boosted Trees, Linear SVM, and Gaussian Naive Bayes.
- **Generative LLM:** use computed artifacts as grounding evidence to create bilingual narrative summaries. Do not use it as a classifier or clustering model and do not fabricate predictive metrics.
- Do not count hyperparameter variations as different model families.

## 7. Model Training

- For clustering, draw an outcome-free 15,000-student computational cohort, fit on 10,500, evaluate on unseen 4,500, test `k=2–10`, and record seed/runtime.
- For supervised learning, use a stratified 70/15/15 train/validation/test split; learn preprocessing on training only and choose the decision threshold on validation only.
- Record failures; never silently substitute a result.

## 8. Model Evaluation and Improvement

- Select the clustering range from the observed K-Means elbow, then compare deployable candidates near the elbow using Silhouette, Davies–Bouldin, Calinski–Harabasz, resample ARI, cluster size, noise, and runtime.
- Compare supervised candidates on the untouched test set using PR-AUC as the primary metric because certification is imbalanced; also report ROC-AUC, Brier, Accuracy, Balanced Accuracy, Precision, Recall, F1, threshold, and runtime.
- Use radar charts only as normalized visual summaries; keep raw values in tables.
- Repeat Steps 5–8 only when evidence justifies a change and log each material revision.
- **Current computed result:** Traditional selected MiniBatch K-Means; Supervised selected Gradient Boosted Trees; Generative LLM produced grounded bilingual summaries from saved artifacts. These are outputs of the current run, not workflow assumptions.

## 9. Deployment

- Package each selected model with its exact preprocessing and an input contract.
- Verify inference on clean student rows and record deployment runtime/throughput; report that runtime is machine-dependent.
- Produce example input/output files and active model cards.
- **Outputs:** `models/tracks/`, `outputs/tables/deployment_runtime.csv`, and `examples/track_*`.

## 10. Communicating Results and Dashboard

- Generate a responsive Thai/English HTML dashboard from saved artifacts only; do not type computed values manually.
- Use large views for Project Overview, Traditional Unsupervised, Deep Learning, Supervised Learning, and LLM.
- Include a collapsible sidebar, 11-step tracker, data downloads, every-column audit, model tables, runtime, elbow/radar/3D plots, limitations, and citations.
- Provide dynamic descriptive segments: All Students, High Engagement, Low Engagement, and Certified Only. Segment filters must not refit or change the locked models.
- **Output:** `reports/student_segmentation_report.html` and report manifest.

## 11. Monitoring and Maintenance

- Save schema, missingness, feature quantiles, cluster proportions, and supervised reference values as the baseline.
- When a genuine future cohort arrives, compare schema, missingness, feature drift, cluster/outlier shift, discrimination, and calibration.
- Until then, report `Not Evaluated`; do not simulate future stability.
- If confirmed drift or degradation occurs, return to Step 2 and repeat affected steps.

## Execution and Verification

Run `python run_project.py`. The command executes active steps, tests the data/model contracts, checks required artifacts and checksums, and writes `outputs/reproducibility/workflow_status.json`. Legacy experiments are not part of the active workflow.
