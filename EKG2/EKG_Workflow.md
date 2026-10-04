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

- `data/raw/` must contain immutable, read-only source data; original data must never be overwritten.
- Every dataset, model, report, and intermediate artifact must have a version, timestamp, hash, and accountable owner.
- Sensitive data, restricted labels, and re-identification keys must have controlled access.
- All transformations must be reproducible and traceable.

---

# Phase 1: Problem Governance and Data Foundation

## Step 1 — Problem Definition and Governance

### 1.1 Define the problem

Clearly specify the problem, affected people and stakeholders, decision supported, prediction or analysis horizon, why data science is appropriate, whether a simpler rule-based method is sufficient, the costs of false positives and false negatives, and operational, ethical, legal, and regulatory constraints.

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

#### Repeated observations and longitudinal entities

Do not assume that one entity has only one record. An entity may legitimately have many observations, visits, studies, transactions, images, signal segments, or measurements. Preserve the entity identifier and an observation/study identifier; define their relationship explicitly.

- Do not drop valid repeated observations merely to force one row per entity.
- Do not aggregate repeated observations into one record unless the question, prediction time, and aggregation rule justify it.
- Define whether the target applies to an observation, episode, encounter, entity, or future time window.
- Prevent entity leakage: observations from the same entity must not appear across independent train, validation, and test partitions unless the evaluation explicitly simulates a permitted longitudinal use case.
- When deployment predicts repeatedly for the same entity, define how predictions are displayed, reconciled, escalated, and audited over time.

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

For health, biometric, clinical, or similarly high-impact data, also define the lawful basis and permitted purpose; minimum necessary data; de-identification or pseudonymization; re-identification-key custody; role-based access; audit logging; retention and deletion; data-sharing controls; clinical review and escalation; validation population; intended use and prohibited use; and applicable local rules or standards. HIPAA, PDPA, GDPR, medical-device rules, and professional standards apply only when relevant to the jurisdiction and intended use; this workflow does not itself establish compliance or clinical validity.

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

#### Optional extension: physiological signals, clinical waveforms, and scanned waveform images

This extension applies when the project contains a physiological waveform (for example, ECG/EKG, EEG, PPG, respiratory, pressure, or other biosignal) in native digital form, as a device export, or as a photograph/scanned printout. It is an optional modality-specific branch, not a requirement for unrelated projects.

- Preserve the immutable original signal, image, and device export. Record device/vendor, lead or channel names, sampling rate, gain, filter settings where available, acquisition duration, timestamps, calibration marks, and source-system version.
- For a native waveform, verify sampling rate, channel order, units, amplitude scale, time base, signal length, synchronization, gaps, clipping, saturation, and duplicate acquisition identifiers. Never silently resample, relabel leads, or infer unavailable metadata.
- For a scanned or photographed waveform, record image resolution, color space, orientation, crop boundaries, visible lead labels, paper speed, gain, grid scale, annotation/overlay presence, and whether the image is complete enough for the proposed use.
- Image preparation may include orientation correction, deskewing, contrast normalization, illumination correction, crop/alignment of the graph area, grid-line suppression or modeling, and quality flags. Retain the original image and record every derived-image transform; grid removal must not erase the waveform or clinically relevant annotations.
- Signal extraction from an image is a separate, fallible reconstruction task. If it is used, validate the recovered time-series against a suitable reference, preserve an extraction-confidence/quality score, and keep image-derived signals distinct from device-native signals.
- Do not treat an image of a plotted waveform as proof that the underlying digital waveform, timestamps, sampling rate, lead identity, or clinical annotation is available.

### 2.4 Perform initial validation

Check schema consistency, file corruption, counts, unique identifiers, timestamps, label availability, class distribution, consent, unexpected columns, duplicate extraction, and train-serving consistency risks.

For repeated-observation datasets, validate the entity-to-observation cardinality, visit/study ordering, duplicate versus clinically distinct observations, time-zone and clock consistency, and any label delay. A repeated study is not automatically a duplicate. Define the event key that distinguishes a repeated measurement from an accidental re-export.

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

#### Optional signal and waveform-image quality control

Use modality-appropriate, versioned quality controls. For physiological waveforms this can include baseline drift, motion artifact, electrode/contact artifact, clipping, flat lines, missing leads, lead reversal suspicion, implausible amplitude, power-line interference, and acquisition interruptions. Candidate denoising methods may include detrending, robust baseline correction, a band-pass filter, and a 50/60 Hz notch filter when justified by the acquisition context. Filter cutoffs are not universal defaults: they must be selected, documented, and validated for the device, sampling rate, clinical objective, and downstream task. Store both the raw and derived signal, filter parameters, and a signal-quality decision.

For waveform images, perform image-quality assessment before any interpretation: resolution, blur, occlusion, cropping, perspective distortion, compression artifacts, grid visibility, calibration visibility, and lead-label readability. Quarantine unreadable or materially incomplete images rather than fabricating signal values. If a human correction is permitted, record who performed it, why, and the before/after artifact hashes.

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

For clinical or repeated-measurement data, include entity ID in a restricted audit store where necessary, observation/study ID, source-system record ID, acquisition time, quality flags, reason for quarantine, and whether the record remains usable for each task. Never put directly identifying values into public reports or broadly accessible dashboards.

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

For longitudinal data, also inspect leakage through later observations, future reports, post-diagnosis interventions, study accession order, clinician annotations created after the prediction point, and entity-level overlap across partitions. Define the index observation and the information cutoff separately for every task.

### 4.5a Optional physiological-signal and waveform-image EDA

When these modalities are active, describe data quality and distribution before modeling. Report channel/lead availability, sampling-rate and duration distributions, amplitude/unit ranges, missing or corrupted segments, noise and quality scores, acquisition site/device/source differences, image resolution and quality distributions, and the distribution of repeated studies per entity. Inspect labels, outcomes, and prevalence by time, source, device, and clinically meaningful subgroup where permitted.

For waveform signals, examine representative raw and cleaned traces, power spectral density, baseline/noise characteristics, beat/peak detection failure rates, and temporal coverage. For waveform images, inspect representative originals and preprocessed images side by side, including difficult cases. These visual checks support quality assurance; they do not substitute for formal clinical validation.

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

#### Stability across resamples and random seeds: ARI and NMI

When a clustering method is stochastic or the selected number of clusters is uncertain, refit the complete eligible preprocessing-and-clustering pipeline across multiple random seeds and repeated resamples, bootstrap samples, or subsamples. Compare the resulting assignments on the same held-out or overlapping observations using Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI). Higher ARI/NMI indicates more agreement between repeated clusterings; it does not prove that a segmentation is clinically, scientifically, or operationally meaningful.

If a legitimate external reference partition exists, ARI/NMI may also be reported as an external evaluation metric. Such labels must not influence unsupervised fitting or be used in a way that creates leakage.

#### Robust K-selection protocol

K must not be selected from a single elbow chart, one random seed, or the maximum/minimum of one metric. For every eligible K-based candidate:

1. Define and justify the candidate K range before inspecting final results. Use the same cohort, feature set, preprocessing definition, and quality rules for all values of K being compared.
2. Fit multiple independent seeds and repeated resamples. Calculate central tendency and uncertainty, such as mean/median, standard deviation, confidence interval, or percentile interval, for every applicable metric.
3. Apply deployment guardrails before ranking: minimum cluster size, unacceptable noise/outlier share, failed convergence, implausible or unstable profiles, unreasonable runtime, and any domain-specific safety or usefulness constraint.
4. Evaluate agreement among the retained metrics. Inertia/WCSS is diagnostic for diminishing returns, not an independent proof of an optimal K. Silhouette is higher-is-better; Davies–Bouldin is lower-is-better; Calinski–Harabasz is higher-is-better; stability ARI/NMI are higher-is-better.
5. Select a K only when it has adequate stability, satisfies guardrails, and is interpretable for the stated purpose. Use a documented consensus/ranking rule with sensitivity analysis rather than an undocumented visual choice.
6. If metrics conflict materially or no candidate is stable, report **no stable K selected**. Revisit feature engineering, scale, sampling, algorithm family, or the need for clustering; do not force a segmentation merely because a chart is required.
7. Freeze the selected preprocessing, randomization policy, K, model, and profile definitions before downstream reporting. Record candidate metrics, seeds, resample design, excluded candidates, selection rule, and rationale in the experiment log.

The following six K-evaluation plots are the standard maximum set. Include only plots that are mathematically applicable and successfully computed; do not replace a missing metric with invented values.

| Plot | Include when | Direction and role |
|---|---|---|
| Inertia / WCSS | Centroid-based K models for which inertia is defined | Lower; use as a diminishing-returns diagnostic only |
| Silhouette | At least two non-noise clusters and a valid internal-distance calculation | Higher; internal separation/cohesion evidence |
| Davies–Bouldin | At least two valid clusters | Lower; internal compactness/separation evidence |
| Calinski–Harabasz | At least two valid clusters | Higher; between/within-dispersion evidence |
| Resample/seed ARI | Repeated fitted partitions can be compared on common observations | Higher; assignment stability evidence |
| Resample/seed NMI | Repeated fitted partitions can be compared on common observations | Higher; information-agreement stability evidence |

For algorithms without a defined K, or metrics that cannot be computed because of noise, sample size, or model behavior, omit the irrelevant plot and state the reason in the dashboard and experiment log.

### Dashboard requirements

- Distribution plots with numerical summaries
- Missing-value heatmap
- Correlation and association matrices
- Outlier and temporal summaries
- Leakage-risk table
- When clustering is active, an interactive K-selection panel with the applicable subset of the six plots above, linked by method, feature set, cohort, and K
- Hover values, uncertainty bands or intervals across seeds/resamples, candidate/guardrail status, and an explicit selection rationale
- Downloadable long-format metric table including seed, resample ID, method, K, metric values, warnings, and selection status
- The selected K line only after a documented decision; use a neutral “candidate” indicator when selection is unresolved

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

#### Optional physiological-signal and waveform-image feature paths

Choose one or more paths only when supported by the source data and the problem; compare them fairly using the same eligible cohort and leakage controls.

1. **Direct vision path.** Use a suitably prepared waveform image directly with image normalization, resizing, and a validated vision model or visual embedding. Candidate backbones may include CNNs or vision transformers such as ResNet, EfficientNet, or ViT. Preserve aspect ratio, calibration information, and lead layout when clinically relevant; do not crop away information simply to fit a standard image size.
2. **Signal-reconstruction path.** Convert a waveform image to a digitized time series only after validation of calibration, grid scale, lead separation, trace extraction, and reconstruction error. Image processing, OCR, and line-tracing may support this path, but extracted signals must be labeled as image-derived and must not be presented as device-native data.
3. **Native signal path.** Start from the device-native waveform, apply justified quality processing, and derive time-domain, frequency-domain, time-frequency, morphology, and learned representation features as appropriate.

Candidate time-domain features include peak locations and confidence; beat count; heart-rate summary; RR intervals; heart-rate variability; P-wave, QRS, and T-wave morphology; PR, QRS, QT, and corrected-QT intervals; amplitude and axis features; beat-to-beat variation; and signal-quality indicators. Their definitions, units, lead choice, detection method, failure behavior, and clinical assumptions must be documented. These measurements are not universally reliable across all rhythms, leads, devices, populations, or image-derived signals.

Candidate frequency-domain features include Fourier/PSD summaries, band power, spectral entropy, and low-/high-frequency HRV measures when their physiological interpretation is appropriate. Candidate time-frequency representations include STFT spectrograms and wavelet/CWT scalograms. Feature extraction must use only the information available at the stated prediction time.

For repeated measurements, construct longitudinal features only from observations available before the index time: count of prior studies, elapsed time since prior study, within-entity trend, variability, and change-from-baseline. Do not use future studies or outcomes.

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

For multimodal work, ablate modalities and quality gates separately: metadata/tabular baseline; native-signal features; image path; image-derived signal path; and fused model. Report coverage and failure rates for each branch so an apparent performance gain is not caused by evaluating only the easiest records.

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

#### Signal, waveform-image, and longitudinal candidates

- Rule-based or conventional signal-processing baseline
- Regularized linear/logistic model or gradient boosting on validated engineered features
- XGBoost, LightGBM, or CatBoost for tabular, derived-signal, and longitudinal features
- 1D-CNN, temporal convolutional network, RNN, LSTM, GRU, or time-series transformer for native waveform sequences
- CNN, vision transformer, or hybrid vision model for validated waveform images
- Fusion models only when each modality is available at inference time and missing-modality behavior is defined

The candidate list is not a requirement to use deep learning. A model should be activated only when the signal/image quality, sample size, labels, compute, evaluation design, and intended use justify it.

#### Anomaly-detection candidates

- Rule-based baseline
- Robust statistical threshold
- Isolation Forest
- Local Outlier Factor
- One-Class SVM
- Autoencoder

### 7.2 Select a splitting strategy

Use stratified, group, time-series, spatial, entity-aware, or nested cross-validation as appropriate. A general starting point is 70% training, 15% validation, and 15% testing, but the final split must reflect data volume and structure.

For datasets containing repeated observations from the same entity, use a grouped or otherwise entity-aware split for claims about performance on unseen entities. All observations from one entity must remain in one partition. If the intended use is prediction for a known entity at a later time, evaluate that use separately with a strictly forward-in-time split and a documented index time. Report both the split rule and the number of entities and observations in each partition.

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

Evaluate only metrics applicable to the clustering family and data: WCSS/inertia, silhouette, Calinski–Harabasz, Davies–Bouldin, cluster-size balance, noise share, convergence, profile interpretability, runtime, and repeated-fit stability. For K-based work, report seed/resample ARI and NMI when common observation IDs permit assignment comparison. If external reference labels are available, report external ARI/NMI separately and preserve their isolation from unsupervised fitting. Report variation across repeats, not only a best run.

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

For images, candidate visual explanation methods include Grad-CAM, saliency maps, occlusion sensitivity, and attention visualization. For waveform sequences, candidate methods include Integrated Gradients, temporal occlusion, saliency, and feature attribution over validated engineered features. Explanations must be tested for stability and plausibility, shown with the original signal/image and quality context, and never treated as evidence of clinical causality or a substitute for expert review.

### 8.10 Conduct a fairness audit

Where relevant and legally permitted, compare performance, recall, precision, false-positive and false-negative rates, calibration, sample sizes, and confidence intervals across groups.

For high-impact health-related uses, also evaluate clinically relevant subgroups and acquisition conditions where lawful and adequately sampled: age bands, sex where appropriate, device or site, lead configuration, image quality, signal quality, and repeated versus first observation. Small or unrepresentative subgroups must be reported as uncertainty or a limitation rather than used to make broad safety claims.

### 8.10a Clinical and operational safety review for high-impact uses

Before a health-related model is presented for use, define intended users, the decision supported, the required human review, uncertainty display, abstention/rejection policy, escalation path, contraindicated use, validation population, and failure modes. Assess sensitivity to noise, missing leads/channels, preprocessing variation, device/site shift, image quality, repeated observations, and label uncertainty. A retrospective benchmark does not by itself demonstrate clinical safety, prospective validity, regulatory clearance, or fitness for diagnosis.

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

For signal or waveform-image inputs, validate sampling rate, units, lead/channel identity and order, duration, calibration, scale, image orientation, crop completeness, image resolution, quality thresholds, and source format. Reject or route uncertain inputs to human review rather than coercing them silently. The production pipeline must reproduce the validated preprocessing version exactly.

### 9.3 Select the deployment mode

Choose batch processing, online API, streaming inference, edge deployment, embedded application, or human-in-the-loop decision support.

### 9.4 Perform pre-production testing

Conduct unit, integration, parity, schema, leakage, load, latency, security, artifact-integrity, and rollback tests.

### 9.5 Create a model card

Document intended and out-of-scope uses, training data, metrics, threshold, limitations, ethical considerations, known failure cases, version, owner, and review date.

For high-impact clinical or physiological applications, include data source and population, label provenance, acquisition settings, repeated-observation policy, input quality requirements, external/temporal validation status, subgroup results, human oversight, abstention behavior, safety limitations, and explicit statement that the system supports—not replaces—qualified professional judgment unless a separately validated and authorized use permits otherwise.

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

Dashboard charts should be interactive by default, with accessible data tables and static export available as a fallback. Where appropriate, include filters, date selectors, segment selectors, model and metric selectors, feature selectors, tooltips, linked highlighting, zoom/pan/reset controls, downloadable tables, expandable methods, a what-if simulator, and prediction explanations. An interactive control must not change a locked model result or silently recompute a metric without clearly displaying the active cohort, filters, model version, and calculation state.

### What-if simulator safeguards

The simulator must validate inputs, display the active model version, show uncertainty where possible, use only features available at inference, prevent post-outcome features, and state that simulation does not prove causality.

---

## Step 11 — Monitoring, Maintenance, and Feedback Loop

### 11.1 Monitor all relevant dimensions

Monitor data quality, schema, missingness, data drift, concept drift, prediction drift, performance drift, calibration drift, fairness drift, latency, throughput, error rate, cost, and failures.

For signals and waveform images, additionally monitor device/vendor/source distribution, sampling rate, lead/channel availability, signal/image quality, filter/preprocessing version, rejected-input rate, extraction failure rate, missing-modality rate, and distribution of repeat observations. Alert thresholds must be evidence-based and reviewed for the intended setting; a generic threshold is not a clinical safety guarantee.

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
