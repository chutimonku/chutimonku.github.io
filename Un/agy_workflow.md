# Project Workflow: Student Segmentation & Responsible Support Planning

**Project:** Student Segmentation for Responsible Support Planning  
**Dataset Source:** [Kaggle MOOC Dataset](https://www.kaggle.com/datasets/kanikanarang94/mooc-dataset)  
**Unit of Analysis:** One row per student (`userid_DI`)  
**Task Type:** Unsupervised Learning (Clustering)  
**Governance Constraint:** Known course outcomes (`certified`, `grade`, `incomplete_flag`, `explored`) are strictly quarantined and physically isolated. They must exert zero influence on data gathering, cleaning, sampling, feature engineering, candidate model selection, hyperparameter tuning, or model locking. Outcomes are unblinded exclusively for post-hoc validation after the final model is locked. No supervised classification, classification accuracy, or confusion matrices are permitted.

---

### Step 1: Problem Definition
- **What Must Be Done:** Define the project objective, research questions, unit of analysis, task type, ethical boundaries, intended users, and expected decisions. Confirm whether unsupervised clustering is appropriate for discovering meaningful student behavioral groups.

- **Why It Is Needed:** A clear problem definition prevents arbitrary feature construction, model selection, evaluation, and interpretation. It also ensures that discovered groups support responsible educational decisions rather than unsupported labeling.

- **How Decisions Will Be Made:** Define success criteria before modeling using internal clustering quality, stability, interpretability, practical usefulness, fairness, and reproducibility. Any numerical acceptance thresholds must be supported by relevant literature or empirical analysis and documented rather than assumed in advance.

- **What Outputs Will Be Created:**
  - Project definition and research questions: `data/processed/problem_definition.json`
  - Problem definition, ethical scope, and success criteria documented in the HTML report
---

### Step 2: Data Gathering & Outcome Quarantine
- **What Must Be Done:** Load the supplied dataset from its documented source and calculate its actual dimensions, file size, checksum, unique-student count, schema, data types, missingness, and duplicate status. Classify fields as identifiers, observational inputs, contextual variables, or known outcomes. Quarantine verified outcome fields with the keys required for later post-hoc validation.

- **Why It Is Needed:** Verifying the source and schema prevents incorrect assumptions about record counts, available fields, and the unit of analysis. Separating outcomes prevents data leakage into sampling, feature engineering, and model optimization.

- **How Decisions Will Be Made:** Determine field roles from dataset documentation and observed values. Treat a field as an outcome only when its meaning represents a learning result. Do not calculate or use outcome distributions until the final clustering model is selected and locked. Preserve all valid records and document every exclusion with its reason.

- **What Outputs Will Be Created:**
  - Data provenance and checksum: `data/processed/data_provenance.json`
  - Data dictionary: `data/processed/data_dictionary.csv`
  - Non-outcome raw data: `data/processed/raw_non_outcomes.parquet`
  - Quarantined outcomes and manifest: `data/quarantine/`
---

### Step 3: Data Cleaning & Student-Level Unit of Analysis
- **What Must Be Done:** Clean the non-outcome data by handling duplicate records, missing values, incorrect data types, inconsistent categories, and invalid or documented sentinel values. Then aggregate repeated records into one row per student using rules appropriate to each field.

- **Why It Is Needed:** Clustering requires consistent student-level data. Unsupported replacements or incorrect aggregation may distort student behavior and create artificial clusters.

- **How Decisions Will Be Made:** Determine cleaning and aggregation rules from dataset documentation, field meaning, and observed distributions. Do not automatically replace unusual values unless they are verified as errors or sentinels. Record student counts before and after every operation, preserve missingness when its meaning is uncertain, and exclude records only with a documented reason.

- **What Outputs Will Be Created:**
  - Cleaned student-level dataset: `data/processed/students_cleaned.parquet`
  - Cleaning and aggregation rules: `data/processed/cleaning_rules.json`
  - Record-count and exclusion audit: `data/processed/cleaning_audit.json`
---

### Step 4: Exploratory Data Analysis (EDA) & Statistical Sampling Justification
- **What Must Be Done:** Explore the cleaned non-outcome data using descriptive statistics and visualizations of missingness, distributions, outliers, sparsity, category frequencies, correlations, feature relationships, redundancy, and potential clustering structure.

- **Why It Is Needed:** EDA reveals data quality issues, feature behavior, and whether the available variables contain meaningful structure for clustering before features or models are selected.

- **How Decisions Will Be Made:** Perform descriptive analysis on the full student-level dataset whenever feasible. If a sample is required for computationally expensive analyses, determine its size and method from the actual data and computational constraints. Document the justification, sample size, random seed, representativeness checks, and limitations using non-outcome variables only. Do not predetermine numerical thresholds without evidence.

- **What Outputs Will Be Created:**
  - EDA statistics: `outputs/tables/eda_summary.csv`
  - Correlation and feature-screening results: `outputs/tables/feature_screening.csv`
  - EDA visualizations: `outputs/figures/eda/`
  - Sampling decision and validation, if used: `data/processed/sampling_report.json`
---

### Step 5: Feature Engineering & Dimensionality Inspection
- **What Must Be Done:** Create, transform, encode, scale, and select clustering features from verified non-outcome variables. Construct student-level behavioral features only when supported by field definitions and observed data.

- **Why It Is Needed:** Clustering is sensitive to feature scale, distribution, redundancy, and high-dimensional encoding. Appropriate preprocessing prevents a small group of variables from dominating the cluster structure.

- **How Decisions Will Be Made:** Select transformations from actual distributions and model requirements. Evaluate missing-value indicators, skew transformations, categorical encoding, scaling, redundancy removal, and dimensionality reduction only when appropriate. Compare alternatives using clustering quality, stability, and interpretability. Do not use outcomes or impose a fixed PCA threshold without evidence.

- **What Outputs Will Be Created:**
  - Feature definitions and rationale: `data/processed/feature_definitions.csv`
  - Fitted preprocessing pipeline: `models/preprocessing_pipeline.joblib`
  - Model-ready feature matrix: `data/processed/feature_matrix.parquet`
  - Feature-engineering comparison: `outputs/tables/feature_engineering_comparison.csv`
---

### Step 6: Model Selection & Candidate Architecture Evaluation
- **What Must Be Done:** Review relevant studies on student segmentation and clustering methods. Use the literature together with the observed data size, variable types, distributions, sparsity, and cluster geometry to select a diverse set of suitable candidate algorithms.

- **Why It Is Needed:** Different clustering algorithms make different assumptions about cluster shape, density, distance, and data scale. Literature and data evidence provide a defensible reason for selecting or excluding each model.

- **How Decisions Will Be Made:** Select genuinely distinct clustering approaches rather than counting parameter settings or closely related implementations as separate models. Determine candidate cluster counts and search ranges from empirical diagnostics and algorithm requirements. Document any model excluded because of incompatibility, computational cost, or poor scalability. Do not use known outcomes for model selection.

- **What Outputs Will Be Created:**
  - Literature review and references: `outputs/research/literature_review.md`
  - Candidate-model rationale and assumptions: `outputs/tables/candidate_models.csv`
  - Model-selection and exclusion record: `outputs/research/model_selection_rationale.md`
---

### Step 7: Model Training, Tuning & Robustness Analysis
- **What Must Be Done:** Train each candidate clustering model through the same preprocessing pipeline and tune its relevant hyperparameters. Repeat stochastic models across documented random seeds and evaluate stability across resamples or data subsets.

- **Why It Is Needed:** Clustering results may change with initialization, hyperparameters, and sampled observations. Consistent training and repeated runs are required for a fair and reproducible comparison.

- **How Decisions Will Be Made:** Determine hyperparameter ranges, number of repetitions, and training-data size from the algorithm requirements, empirical results, and available computational resources. Use the full student-level dataset whenever feasible; otherwise use the validated sampling procedure from Step 4 and document the limitation. Record runtime, convergence or failure status, configurations, random seeds, and the documented memory budget used to determine computational sample sizes. Outcomes must remain quarantined throughout training and tuning.

- **What Outputs Will Be Created:**
  - Trained candidate model artifacts: models/candidates/
  - Hyperparameter search results: `outputs/tables/model_tuning_results.csv`
  - Training configuration and random seeds: `outputs/reproducibility/training_config.json`
  - Runtime, convergence, and failure log: `outputs/logs/model_training_log.csv`
---

### Step 8: Model Locking & Post-Hoc Validation
- **What Must Be Done:** Compare all successfully trained models using internal clustering metrics, stability, cluster-size distribution, and computational performance. Select a provisional model using the documented non-outcome ranking rule, then conduct pre-lock interpretability and preprocessing-sensitivity reviews. Lock the model only after these reviews pass and before accessing quarantined outcomes. After locking, use outcomes only to describe post-hoc differences between clusters.

- **Why It Is Needed:** Clustering has no single accuracy measure or true class label. A model may score well on one metric but produce unstable, impractical, or uninterpretable groups. Separating selection from post-hoc validation prevents outcome leakage.

- **How Decisions Will Be Made:** Apply a documented selection rule based only on non-outcome evidence and avoid selecting a model from one metric alone. Investigate unstable assignments, outliers, noise points, small clusters, and sensitivity to preprocessing or hyperparameters. Record the selected configuration and checksum before unblinding outcomes. For post-hoc analysis, report distributions, uncertainty, statistical tests, and effect sizes without using them to revise the selected model.

- **What Outputs Will Be Created:**
  - Complete model comparison: `outputs/tables/model_comparison.csv`
  - Assignment and ambiguity diagnostics: outputs/tables/model_diagnostics.csv
  - Feature-group ablation results: outputs/tables/feature_group_ablation.csv
  - Preprocessing sensitivity results: outputs/tables/feature_engineering_comparison.csv
  - Locked model configuration and checksum: `models/final/model_lock.json`
  - Locked clustering model: `models/final/cluster_model.joblib`
  - Student cluster assignments without outcomes: `outputs/data/cluster_assignments.csv`
  - Separate post-hoc validation results: `outputs/tables/posthoc_validation.csv`

---

### Model Optimization Cycle: Repeat Steps 5–8

- Repeat feature engineering, model selection, training, and internal evaluation only when the current results do not satisfy the documented success criteria.

- Record the reason, hypothesis, configuration change, computational cost, and result of every iteration. Compare each iteration with the current best reproducible baseline.

- Keep outcomes quarantined throughout the optimization cycle. Once the final model is locked and outcomes are unblinded for post-hoc validation, they must not be used to return to the cycle or modify the selected model.

- If a redesign is necessary after viewing outcomes, register it as a new analysis version and restart from Step 2 with outcomes quarantined again.

- **Outputs:**
  - Optimization history: `outputs/tables/optimization_history.csv`
  - Decision and experiment log: `outputs/reproducibility/experiment_log.md`
---

### Step 9: Model Deployment & Verification Testing
- **What Must Be Done:** Package the locked preprocessing and clustering model into a reproducible inference pipeline. Provide a supported method for assigning new student-level data to established clusters, with schema validation and outcome-exclusion safeguards.

- **Why It Is Needed:** Deployment ensures that new data receives exactly the same cleaning, feature engineering, and transformations used during model training.

- **How Decisions Will Be Made:** Select batch processing, an interactive tool, or an API according to the documented user need and available infrastructure. Validate required columns, data types, missing values, unseen categories, and excluded outcome fields. Confirm that the saved model can be loaded and executed in a clean environment before release.

- **New-Data Boundary:** The locked pipeline may assign later cohorts only when field definitions and the raw or student-level schema match the documented data contract. If columns or meanings differ, return to Step 2 and train a new pipeline; do not force incompatible data through the locked model.

- **What Outputs Will Be Created:**
  - Portable final pipeline: `models/final/clustering_pipeline.joblib`
  - Inference program: `src/predict_clusters.py`
  - Input schema and validation rules: `models/final/input_schema.json`
  - Reproducible environment specification: `requirements.txt`
  - Deployment tests and example input/output: `tests/` and `examples/`
  - Model documentation: `models/final/model_card.md`
---

### Step 10: Communicate Results & HTML Dashboard

- **What Must Be Done:** Generate a concise, self-contained HTML dashboard directly from the saved data, tables, figures, model artifacts, and post-hoc results. Explain the methods, evidence, findings, limitations, and responsible uses in language appropriate for both technical and non-technical readers.

- **Why It Is Needed:** A reproducible report prevents manually entered or outdated values and makes the complete analysis traceable from the original data to the final conclusions.

- **How Decisions Will Be Made:** Include only values calculated by the pipeline and clearly separate observed findings from interpretation or recommendations. Generate neutral cluster descriptions from measured profiles rather than predefined personas. Display internal clustering metrics instead of classification accuracy, and verify that charts, labels, tables, and interactive components remain readable.

- **Required Dashboard Sections:** Executive Overview; Problem Definition & Research Questions; Literature Review & Method Rationale; Dataset Provenance & Quality; Data Dictionary; Descriptive Statistics & EDA; Statistical Feature Screening; Preprocessing & Feature Engineering; Unsupervised Model Comparison; Cluster Profiles & Visualizations; Cluster-Defining Feature Contributions; Stability, Error, Ablation & Sensitivity Analysis; Post-Hoc Validation; Interactive Student Scenario Explorer; Conclusions, Limitations & Next Steps.

- **What Outputs Will Be Created:**
  - Final interactive report: `reports/student_segmentation_report.html`
  - Report source/generator: `src/generate_report.py`
  - Report figures and tables: `outputs/figures/` and `outputs/tables/`
  - Report artifact manifest: `reports/report_manifest.json`
---

### Step 11: Monitor, Maintain & Feedback Loop

- **What Must Be Done:** Monitor input schema, data quality, feature drift, cluster-assignment distribution, assignment uncertainty, outlier rates, cluster stability, pipeline failures, and responsible use over time. Compare new data with the documented training baseline.

- **Why It Is Needed:** Student behavior, course design, and data collection may change, causing the established clusters to become unstable, misleading, or no longer useful.

- **How Decisions Will Be Made:** Define monitoring frequency, warning levels, and retraining triggers from the training baseline, historical variation, literature, and operational needs rather than arbitrary fixed thresholds. Investigate detected changes before retraining. If substantial drift or degradation is confirmed, return to Step 2 and repeat the workflow while maintaining the same outcome-quarantine rules. Deploy a replacement only after it outperforms the locked model under the documented evaluation criteria.

- **What Outputs Will Be Created:**
  - Monitoring baseline and rules: `monitoring/monitoring_config.json`
  - Periodic drift and stability report: `monitoring/monitoring_report.html`
  - Monitoring history: `monitoring/monitoring_history.csv`
  - Retraining decision record: `monitoring/retraining_decision.json`
---

## Workflow Execution Rules

- Execute every applicable step in this workflow and create the specified outputs; do not stop after reviewing or rewriting the workflow.

- Use only the supplied dataset, its documentation, relevant literature, and results calculated by the project code. Do not fabricate values, results, columns, models, cluster counts, personas, or conclusions.

- Preserve the original raw data unchanged. Record file checksums, row counts, student counts, exclusions, configurations, random seeds, software versions, and generated artifacts.

- Generate all tables, figures, metrics, narratives, and HTML content from saved analysis outputs. Do not hard-code calculated results into the report.

- Treat config/project_config.json as the source for the dataset location, source, expected raw schema, unit identifier, and quarantined outcomes during ingestion. If the schema or field meanings change, revise the project-specific cleaning and feature logic and restart from Step 2.

- Keep known outcomes quarantined until the final model is selected and locked. If an outcome is accidentally accessed earlier, invalidate that model-selection run and record the incident.

- If a required task cannot be completed, document the exact reason and limitation instead of substituting assumed results.

- Provide one reproducible entry point that runs the workflow in the correct order and verifies all required outputs.

- Main execution entry point: `run_project.py`
- Reproducible project configuration: `config/project_config.json`
- Environment and dependency record: `requirements.txt`
- Complete run manifest: `outputs/reproducibility/run_manifest.json`
- Required-output verification: `outputs/reproducibility/artifact_check.json`
