# Master Universal Data Science and Machine Learning Workflow

> An enterprise-ready, audit-ready, modality-neutral, reproducible, multilingual, and dashboard-integrated standard.

This framework combines the original workflows into a single neutral standard that can be adapted to classification, regression, clustering, forecasting, anomaly detection, NLP, computer vision, audio, sensor, graph, and multimodal projects.

The workflow must be adapted according to the project objectives, unit of analysis, data modality, target availability, data volume and quality, business risks, privacy requirements, available infrastructure, time, and budget. Algorithms must not be selected merely to satisfy a fixed number. Classification, clustering, deep learning, or other techniques should be used only when appropriate for the problem and data.

---

## Standard Directory Layout

```text
project_root/
├── config/
│   ├── project_config.yaml
│   ├── data_schema.yaml
│   └── monitoring_config.yaml
├── data/
│   ├── raw/                     # Immutable original data
│   ├── quarantine/              # Restricted labels, sensitive, or invalid records
│   ├── interim/                 # Intermediate data
│   ├── cleaned/                 # Cleaned data
│   ├── processed/               # Feature-engineered data
│   └── monitoring/              # Production and drift-monitoring data
├── src/
│   ├── ingestion/
│   ├── validation/
│   ├── cleaning/
│   ├── features/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   └── monitoring/
├── models/
│   ├── baselines/
│   ├── experiments/
│   ├── candidates/
│   ├── final/
│   └── archived/
├── outputs/
│   ├── eda/
│   ├── evaluation/
│   ├── explainability/
│   ├── fairness/
│   ├── monitoring/
│   └── dashboard/
├── reports/
│   ├── literature_review/
│   ├── model_card/
│   ├── data_sheet/
│   └── final_report/
├── tests/
│   ├── data_tests/
│   ├── pipeline_tests/
│   └── model_tests/
└── logs/
    ├── data_provenance.json
    ├── cleaning_audit.json
    ├── experiment_log.json
    ├── evaluation_log.json
    ├── deployment_log.json
    └── monitoring_log.json
```

Core requirements:

- `data/raw/` must contain immutable, read-only source data.
- Original raw data must never be overwritten.
- Every dataset and artifact must have a version, timestamp, hash, and owner.
- Sensitive data and restricted targets should have controlled access.
- All transformations must be reproducible and traceable.

---

# Phase 1: Problem Governance and Data Foundation

## Step 1 — Problem Definition and Governance

### 1.1 Define the problem

Clearly specify:

- The problem to be solved
- The affected users and stakeholders
- The decision the analysis or model will support
- Why data science or machine learning is appropriate
- Whether a simpler statistical or rule-based solution is sufficient
- The costs of false positives and false negatives
- Operational, ethical, legal, and regulatory constraints

Recommended problem-statement format:

```text
Given [available information],
predict, estimate, identify, or discover [target or structure]
for [unit of analysis]
within [prediction horizon or scope]
to support [business or operational decision],
subject to [constraints],
and evaluated using [technical and business metrics].
```

### 1.2 Define the unit of analysis

State what one record represents, such as one person, customer, transaction, event, image, video clip, document, time window, machine, sensor reading, or graph node. Define the primary key, entity identifier, timestamp, and granularity.

### 1.3 Identify the task type

- Binary, multiclass, or multilabel classification
- Regression
- Ranking or recommendation
- Clustering or segmentation
- Anomaly detection
- Time-series forecasting
- Survival or time-to-event analysis
- Natural language processing
- Computer vision
- Audio or signal processing
- Graph analytics
- Causal inference
- Multimodal learning

### 1.4 Define the target

For supervised tasks, specify the target column, positive class, prediction time, observation window, outcome window, information available at prediction time, and rules for unknown, missing, delayed, or ambiguous labels.

### 1.5 Define success criteria

Success criteria should include:

1. Technical performance
2. Business value
3. Operational performance

Example:

```text
Recall ≥ 0.80
Precision ≥ 0.65
Calibration error ≤ 0.05
Inference latency ≤ 200 milliseconds
No protected group has recall more than 10% below overall recall
```

### 1.6 Establish governance

Evaluate GDPR, PDPA, organizational policies, consent, permitted purpose, personal and sensitive information, retention, access control, security, fairness, human oversight, and the consequences of incorrect predictions.

### Dashboard requirements

- Problem statement
- Unit of analysis
- Task and target definition
- Success criteria
- Privacy and regulatory status
- Target-leakage risk status

---

## Step 2 — Data Gathering, Ingestion, and Provenance

### 2.1 Identify data sources

Use reliable and legally permitted sources such as internal databases, data warehouses, public datasets, APIs, sensors, surveys, media repositories, document collections, authorized web sources, and human annotation.

### 2.2 Record data provenance

Record in `logs/data_provenance.json`:

- Source name, URL, owner, license, and usage restrictions
- Extraction date and covered time period
- Record count and file size
- Languages and modality
- Schema and raw-data version
- SHA-256 hash
- Extraction query or API version
- Sampling method and known limitations

### 2.3 Transform multimodal data

- **Tabular:** numerical, categorical, and ordinal representations
- **Text:** tokens, TF-IDF, linguistic features, or embeddings
- **Images:** pixels, descriptors, or visual embeddings
- **Audio:** waveforms, MFCCs, Mel-spectrograms, or embeddings
- **Video:** frames, motion, optical flow, or multimodal embeddings
- **Time series:** lags, rolling statistics, seasonality, or frequency features
- **Graphs:** node, edge, subgraph, or graph embeddings
- **Multimodal:** early, intermediate, or late fusion

### 2.4 Perform initial validation

Check schema consistency, file corruption, counts, unique identifiers, timestamps, label availability, class distribution, consent, unexpected columns, duplicate extraction, and train-serving consistency risks.

### Dashboard requirements

- Data-provenance table
- Record counts and time coverage
- Modality and language summaries
- Dataset version and hash
- Known limitations

---

## Step 3 — Data Quality Control and Cleaning

### 3.1 Apply target-isolation controls

The target must be logically separated from predictors, excluded from feature construction and preprocessing inputs, and absent from production inference inputs. It must still be assessed separately for missing, invalid, ambiguous, inconsistent, or noisy labels; class imbalance; and annotation agreement.

Target isolation means preventing leakage, not avoiding target-quality analysis.

### 3.2 Perform data cleaning

Address missing values, duplicates, incorrect types, invalid categories, impossible values, invalid timestamps, inconsistent units, encoding errors, garbage text, corrupted media, signal noise, sensor faults, inconsistent identifiers, and leakage columns.

### 3.3 Analyze missing data

Assess whether missingness is Missing Completely at Random, Missing at Random, Missing Not at Random, or informative. Possible treatments include removal when justified, statistical or model-based imputation, time-aware imputation, missing indicators, and an explicit unknown category.

Imputation parameters must not be learned from the complete dataset before splitting.

### 3.4 Validate domain and logic rules

Examples include:

- `start_time ≤ end_time`
- Age is within a permitted range
- Prediction time occurs before the outcome
- Totals equal their components
- Units are consistent
- Mutually exclusive fields do not conflict

Correct records with auditable domain rules where possible instead of deleting them automatically.

### 3.5 Create a cleaning audit trail

For every rule, record its ID, description, affected count, action, permitted before-and-after values, affected percentage, justification, timestamp, and pipeline version.

### Dashboard requirements

- Raw-to-cleaned funnel or Sankey diagram
- Missing-value matrix
- Duplicate summary
- Quality-rule table
- Modified, removed, and quarantined counts
- Data-quality score

---

# Phase 2: Exploratory Analysis and Evidence Review

## Step 4 — Exploratory Data Analysis

### 4.1 Create a complete feature inventory

For every feature, record its type, unique count, missing percentage, mean, median, standard deviation, minimum, maximum, quantiles, skewness, kurtosis, outlier count, and constant or near-constant status.

### 4.2 Perform univariate analysis

Use appropriate histograms, density plots, boxplots, violin plots, bar charts, frequency tables, time-series charts, and media-quality distributions.

### 4.3 Perform bivariate and multivariate analysis

Analyze Pearson and Spearman correlation, Cramér's V, mutual information, target association, interactions, temporal trends, segment differences, multicollinearity, and spatial relationships. Correlation must not be presented as proof of causation.

### 4.4 Analyze outliers

Possible techniques include IQR, robust Z-score, median absolute deviation, Isolation Forest, Local Outlier Factor, and domain rules. Distinguish data errors, rare valid observations, genuine anomalies, and natural distribution tails. Never remove outliers without justification.

### 4.5 Analyze leakage risk

Check for post-outcome features, target proxies, identifiers that memorize labels, aggregates containing future data, duplicate entities across splits, complete-dataset preprocessing, and human decisions influenced by the outcome.

### 4.6 Evaluate clustering feasibility

Clustering should be performed only when pattern discovery or segmentation is relevant.

#### Within-Cluster Sum of Squares

$$
WCSS=\sum_{i=1}^{K}\sum_{x\in C_i}\lVert x-\mu_i\rVert^2
$$

#### Silhouette coefficient

$$
s(i)=\frac{b(i)-a(i)}{\max(a(i),b(i))}
$$

#### Calinski–Harabasz index

$$
CH_K=\frac{\mathrm{Tr}(B_K)}{\mathrm{Tr}(W_K)}\times\frac{N-K}{K-1}
$$

#### Davies–Bouldin index

$$
DB=\frac{1}{K}\sum_i\max_{j\neq i}\frac{\sigma_i+\sigma_j}{d(c_i,c_j)}
$$

Select the final number of clusters by considering WCSS, silhouette, Calinski–Harabasz, Davies–Bouldin, cluster stability, size, interpretability, and business usefulness.

### Dashboard requirements

- Distribution plots with numerical summaries
- Missing-value heatmap
- Correlation and association matrices
- Outlier and temporal summaries
- Leakage-risk table
- K-metric chart and optimal-K reference line when applicable

---

## Step 5 — Literature Review and Evidence Assessment

Review peer-reviewed studies, benchmark datasets, established industry methods, similar-data models, recommended metrics, known risks, fairness research, interpretability research, and professional guidance.

For each source, record:

- Citation and publication year
- Dataset, population, modality, and sample size
- Task, model, and metrics
- Main findings and limitations
- Applicability to the current project

Evidence should generally be prioritized as follows:

1. Systematic reviews and professional standards
2. Peer-reviewed research
3. Official technical documentation
4. Reputable benchmark studies
5. Technical articles when stronger evidence is unavailable

The review must justify model and evaluation choices rather than merely summarize publications.

---

# Phase 3: Feature and Model Development

## Step 6 — Feature Engineering and Selection

### 6.1 Split data before learned preprocessing

Create separate training, validation, and test sets. Any operation with `.fit()` must be fitted exclusively on training data. Validation and test data may only use `.transform()`.

### 6.2 Create candidate features

Examples include ratios, rates, differences, interactions, polynomial terms, time-since-event variables, lags, rolling statistics, frequency features, linguistic features, media embeddings, and domain-specific scores.

Every feature must be available at inference time, avoid future information, have a statistical or domain rationale, have a documented formula and version, and be reproducible in production.

### 6.3 Transform features

#### Log transformation

$$
y=\log(1+x)
$$

#### Standard scaling

$$
z=\frac{x-\mu_{\text{train}}}{\sigma_{\text{train}}}
$$

#### Robust scaling

$$
z_{\text{robust}}=\frac{x-\mathrm{Median}_{\text{train}}}{Q3_{\text{train}}-Q1_{\text{train}}}
$$

Other options include power and quantile transformations, binning, one-hot and ordinal encoding, cross-fitted target encoding, dimensionality reduction, and embedding reduction.

### 6.4 Select features

Consider domain relevance, missingness, variance, multicollinearity, mutual information, regularization, permutation importance, recursive elimination, stability across folds, collection cost, and inference-time availability.

### 6.5 Conduct ablation studies

Compare baseline features, engineered features, reduced sets, and full sets to demonstrate whether new features add stable value.

### Dashboard requirements

- Before-and-after distributions
- Feature-lineage table
- Selected and removed features
- Leakage-check results
- Train-only fitting verification
- Ablation comparison

---

## Step 7 — Model Selection, Training, and Experiment Tracking

### 7.1 Select models based on the task

Construct a candidate pool according to the problem. When the data and project scope permit, evaluate at least five meaningfully different candidates for the activated task. Fewer models are acceptable when justified.

#### Classification candidates

- Dummy classifier
- Logistic regression
- Naive Bayes
- k-Nearest Neighbors
- Decision tree
- Random forest or Extra Trees
- Gradient boosting
- XGBoost, LightGBM, or CatBoost
- Support vector machine
- Multilayer perceptron
- CNN or Transformer-based classifier

#### Clustering candidates

- K-Means or MiniBatch K-Means
- Gaussian Mixture Model
- Agglomerative clustering
- BIRCH
- DBSCAN or HDBSCAN
- Spectral clustering
- K-Medoids
- Self-organizing map
- Deep clustering

#### Regression candidates

- Mean or median baseline
- Linear regression or Elastic Net
- Decision tree or random forest
- Gradient boosting
- XGBoost, LightGBM, or CatBoost
- Support vector regression
- Neural network

#### Time-series candidates

- Naive and seasonal-naive forecasts
- Exponential smoothing
- ARIMA or SARIMA
- Prophet
- Gradient-boosted lag model
- State-space model
- RNN, LSTM, or Temporal Fusion Transformer

#### Anomaly-detection candidates

- Rule-based baseline
- Robust statistical threshold
- Isolation Forest
- Local Outlier Factor
- One-Class SVM
- Autoencoder

### 7.2 Select a splitting strategy

Use stratified, group, time-series, spatial, entity-aware, or nested cross-validation as appropriate. A general starting point is 70% training, 15% validation, and 15% testing, but the final split must reflect data volume and structure.

### 7.3 Handle imbalanced data

Options include class weighting, threshold adjustment, under-sampling, over-sampling, SMOTE within training folds only, cost-sensitive learning, and focal loss. Never resample validation or test data.

### 7.4 Tune hyperparameters

Use grid search, random search, Bayesian optimization, or successive halving. Never use the test set to select features, models, thresholds, or hyperparameters.

### 7.5 Track experiments

Record the run ID, dataset and feature versions, code version, seed, splitting strategy, preprocessing, model, hyperparameters, runtime, memory, hardware, validation metrics, artifact paths, warnings, and failures.

### Dashboard requirements

- Activated model-track matrix
- Experiment table and validation leaderboard
- Runtime and memory comparison
- Reproducibility status
- Data-split visualization

---

# Phase 4: Evaluation, Explainability, and Decision-Making

## Step 8 — Model Evaluation, Optimization, and Error Analysis

### 8.1 Establish a baseline

Compare every model with an appropriate majority, random, mean, median, seasonal-naive, rule-based, or current-process baseline.

### 8.2 Classification metrics

$$
Accuracy=\frac{TP+TN}{TP+TN+FP+FN}
$$

$$
Precision=\frac{TP}{TP+FP}
$$

$$
Recall=\frac{TP}{TP+FN}
$$

$$
F1=2\times\frac{Precision\times Recall}{Precision+Recall}
$$

$$
Brier=\frac{1}{N}\sum_{i=1}^{N}(p_i-y_i)^2
$$

Also consider specificity, balanced accuracy, ROC-AUC, PR-AUC, log loss, Matthews correlation coefficient, top-k accuracy, and calibration error.

### 8.3 Regression metrics

Use appropriate combinations of MAE, RMSE, median absolute error, R-squared, MAPE or sMAPE, and prediction-interval coverage.

### 8.4 Forecasting metrics

Use MAE, RMSE, MASE, sMAPE, forecast bias, interval coverage, and backtesting performance as appropriate.

### 8.5 Clustering metrics

Evaluate WCSS, silhouette, Calinski–Harabasz, Davies–Bouldin, cluster stability, size balance, interpretability, and ARI or NMI when reference labels exist.

### 8.6 Protect evaluation integrity

- Use the test set only after model selection is complete.
- Report cross-validation means and variation.
- Use confidence intervals or bootstrapping where appropriate.
- Examine training, validation, and test performance gaps.
- Compare results with predefined success criteria.
- Never select a model using only one metric.

### 8.7 Optimize thresholds and calibration

Choose classification thresholds with validation data, assess precision–recall trade-offs, inspect calibration, apply Platt or isotonic calibration if necessary, and evaluate the final locked configuration on the test set.

### 8.8 Conduct error analysis

Analyze false positives, false negatives, large residuals, subgroup errors, temporal errors, source-specific errors, missingness patterns, confidence bands, label noise, and distribution shifts.

### 8.9 Apply explainable AI

Use model coefficients, feature importance, permutation importance, partial dependence, ICE, SHAP, LIME, or counterfactual explanations as appropriate. Feature importance must not be presented as proof of causality.

### 8.10 Conduct a fairness audit

Where relevant and legally permitted, compare performance, recall, precision, false-positive and false-negative rates, calibration, sample sizes, and confidence intervals across groups.

### 8.11 Apply the optimization cycle

Repeat Steps 6–8 when criteria are unmet, leakage is discovered, error analysis identifies a fixable issue, features are unstable, or the model fails to generalize.

Stop when criteria are met, improvements fall below a predefined minimum, resources are exhausted, complexity is unjustified, or data quality prevents further progress.

### Dashboard requirements

- Model-comparison table
- Training, validation, and test metrics
- Confusion matrix and task-appropriate curves
- Calibration and residual plots
- Explainability results
- Error and fairness analyses
- Final model-selection rationale

---

# Phase 5: Deployment, Communication, and Lifecycle Management

## Step 9 — Deployment and Operational Validation

### 9.1 Build a unified inference pipeline

```text
Input validation
→ Cleaning
→ Feature engineering
→ Encoding and scaling
→ Model inference
→ Calibration or thresholding
→ Prediction output
→ Logging
```

### 9.2 Validate the input schema

Validate required fields, data types, ranges, categories, missingness, timestamps, file formats, media dimensions, text encoding, batch sizes, and unexpected columns.

### 9.3 Select the deployment mode

Choose batch processing, online API, streaming inference, edge deployment, embedded application, or human-in-the-loop decision support.

### 9.4 Perform pre-production testing

Conduct unit, integration, parity, schema, leakage, load, latency, security, artifact-integrity, and rollback tests.

### 9.5 Create a model card

Document intended and out-of-scope uses, training data, metrics, threshold, limitations, ethical considerations, known failure cases, version, owner, and review date.

### Dashboard requirements

- Deployment, model, and pipeline status
- Schema-test results
- Latency and throughput
- Readiness checklist
- Rollback version

---

## Step 10 — Communication and Interactive HTML Reporting

Create a responsive HTML report that can run as a standalone report or server-backed dashboard.

### Required report sections

1. Executive summary
2. Problem definition
3. Data provenance
4. Data quality and cleaning
5. Exploratory data analysis
6. Literature review
7. Feature engineering
8. Model selection
9. Training and experiments
10. Model evaluation
11. Error analysis
12. Explainability and fairness
13. Deployment readiness
14. Monitoring plan
15. Limitations
16. Recommendations
17. Reproducibility information

### Bilingual requirements

When bilingual reporting is required, the TH/EN control should translate navigation, headings, explanations, chart labels, table headings, statistical annotations, warnings, and recommendations.

### Interactive components

Where appropriate, include filters, date selectors, segment selectors, model and metric selectors, feature selectors, tooltips, downloadable tables, expandable methods, a what-if simulator, and prediction explanations.

### What-if simulator safeguards

The simulator must validate inputs, display the active model version, show uncertainty where possible, use only features available at inference, prevent post-outcome features, and state that simulation does not prove causality.

---

## Step 11 — Monitoring, Maintenance, and Feedback Loop

### 11.1 Monitor all relevant dimensions

Monitor data quality, schema, missingness, data drift, concept drift, prediction drift, performance drift, calibration drift, fairness drift, latency, throughput, error rate, cost, and failures.

### 11.2 Calculate the Population Stability Index

$$
PSI=\sum_i(\mathrm{Actual}_i-\mathrm{Expected}_i)\ln\left(\frac{\mathrm{Actual}_i}{\mathrm{Expected}_i}\right)
$$

Suggested initial thresholds:

- $PSI < 0.10$: Normal
- $0.10 \leq PSI < 0.25$: Warning
- $PSI \geq 0.25$: Significant drift

These are guidelines, not universal rules. Adjust them for sample size, feature importance, domain behavior, and business risk.

### 11.3 Define performance triggers

Examples include a recall or F1 decline greater than 15%, excessive calibration error, increased missingness, excessive unknown categories, unacceptable fairness gaps, SLA failures, schema changes, or data-source changes.

### 11.4 Implement the feedback loop

```text
Monitor production
        ↓
Detect degradation
        ↓
Validate the alert and identify the root cause
        ↓
Return to Step 2 if new data is required
Return to Step 3 if cleaning rules must change
Return to Step 6 if features or models must change
        ↓
Retrain and evaluate
        ↓
Review and approve
        ↓
Deploy using shadow or canary testing
        ↓
Complete deployment or roll back
```

### 11.5 Define a retraining policy

Specify the schedule, triggers, minimum new sample size, label delay, approval process, champion–challenger comparison, rollback conditions, artifact retention, and model-retirement policy.

### Dashboard requirements

- PSI gauge and drift trends
- Performance and calibration trends
- Fairness and data-quality status
- Service health and current model version
- Last retraining and next review dates
- Feedback-loop status

---

# Final Deliverables

Each project should provide, where applicable:

1. Problem statement and success criteria
2. Data-provenance log
3. Data dictionary and schema
4. Cleaning-audit log
5. EDA report
6. Literature review
7. Feature-lineage and leakage report
8. Experiment log
9. Model-comparison table
10. Confusion matrix or task-appropriate evaluation plots
11. Error analysis
12. Explainability report
13. Fairness report
14. Serialized inference pipeline
15. Input-schema validator
16. Model card
17. Monitoring and retraining plan
18. Reproducible source code
19. Environment and dependency specification
20. Interactive HTML report

---

# Minimum Quality Gates

| Quality gate | Passing requirement |
|---|---|
| Problem definition | Target, unit of analysis, decision context, and success criteria are clearly defined |
| Data provenance | Source, ownership, license, schema, version, and hash are recorded |
| Privacy | Privacy, consent, access control, and retention requirements are satisfied |
| Data quality | Cleaning decisions are documented and auditable |
| Leakage prevention | No target, temporal, entity, or preprocessing leakage is detected |
| Data splitting | Splits correctly account for class, entity, group, spatial, and temporal structure |
| Feature processing | Learned transformations are fitted only on training data |
| Baseline | Every candidate is compared with an appropriate baseline |
| Model selection | Candidate models are appropriate for the problem and data |
| Evaluation | Validation and test sets remain independent |
| Explainability | The explanation method matches the model and risk level |
| Fairness | Relevant subgroup performance is evaluated |
| Deployment | Unified pipeline, schema, integrity, and rollback tests pass |
| Reproducibility | Data, code, configuration, environment, and seed versions are recorded |
| Monitoring | Drift, performance, alert, retraining, and rollback plans exist |
| Reporting | Results, assumptions, limitations, and risks are communicated transparently |

---

# End-to-End Lifecycle

The workflow is iterative rather than strictly linear:

```text
Define
  → Gather
  → Clean
  → Explore
  → Review Evidence
  → Engineer Features
  → Select and Train Models
  → Evaluate and Optimize
  → Deploy
  → Communicate
  → Monitor
       ↓
  Feedback and Retraining
       ↓
  Return to the appropriate earlier step
```

The final model should not automatically be the most complex model or the model with the highest single metric. It should provide the best justified balance of predictive performance, stability, interpretability, fairness, operational feasibility, risk, and business value.
