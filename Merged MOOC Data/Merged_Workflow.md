# Master Universal Data Science and Machine Learning Workflow

> An enterprise-ready, audit-ready, modality-neutral, reproducible, multilingual, and dashboard-integrated standard.

This framework combines the original workflows into a single neutral standard that can be adapted to classification, regression, clustering, forecasting, anomaly detection, NLP, computer vision, audio, sensor, graph, and multimodal projects.

The workflow must be adapted according to the project objectives, unit of analysis, data modality, target availability, data volume and quality, business risks, privacy requirements, available infrastructure, time, and budget. Algorithms must not be selected merely to satisfy a fixed number. Classification, clustering, deep learning, or other techniques should be used only when appropriate for the problem and data.

## MOOC Project Interpretation Rules

For the current merged MOOC project, the following distinctions are mandatory:

- Student enrollment, click, chapter, forum, and video-play columns are **behavioral interaction data**.
- A video-play count is not video content, spoken language, a caption, or a transcript.
- Behavioral video columns may be used in tabular EDA, clustering, classification, and behavioral feature engineering.
- Content-based NLP or LLM analysis may begin only after actual video/audio, official captions, or verified transcripts have been acquired.
- When raw video is the source, the required order is: **video acquisition → audio extraction → speech-to-text → word-level transcript → sentence segmentation → transcript quality control → LLM/NLP representation → downstream model**.
- Structured sentences generated from numeric behavior columns must be labeled as `behavior_summary_text`; they must never be described as spoken-video transcripts.
- If raw media, captions, and transcripts are unavailable, the content-based LLM track must be reported as **blocked / not available**, while the behavioral analytics tracks may continue independently.

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
│   ├── media/                   # Governed video/audio assets and media manifest
│   ├── transcripts/
│   │   ├── raw_asr/             # Unedited ASR output with timestamps
│   │   ├── cleaned/             # Corrected words and sentence boundaries
│   │   └── aligned/             # Video/audio-to-sentence alignment
│   └── monitoring/              # Production and drift-monitoring data
├── src/
│   ├── ingestion/
│   ├── validation/
│   ├── cleaning/
│   ├── features/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   ├── transcription/
│   ├── nlp/
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
    ├── media_provenance.json
    ├── transcription_audit.json
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
- **Video content:** preserve the source video, extract audio and frames, create a timestamped transcript, divide the transcript into words and complete sentences, validate transcript quality, and only then generate text or multimodal representations
- **Video behavior logs:** treat play counts, replay counts, watch ratios, and interaction events as tabular behavioral features; never treat them as spoken-video content
- **Time series:** lags, rolling statistics, seasonality, or frequency features
- **Graphs:** node, edge, subgraph, or graph embeddings
- **Multimodal:** early, intermediate, or late fusion

### 2.4 Mandatory video-to-text pipeline for LLM/NLP

Content-based LLM analysis must use the following ordered process. No stage may silently substitute numeric video-behavior columns for spoken content.

1. **Acquire governed media or captions**
   - Collect the original video/audio files or official caption files.
   - Record course ID, video ID, language, duration, source, license, checksum, and acquisition date.
   - Preserve the original media as immutable raw data.
2. **Extract and standardize audio**
   - Extract a lossless or high-quality speech channel.
   - Standardize sample rate, channels, and loudness while retaining the original asset.
   - Detect silent, corrupt, clipped, or incomplete audio.
3. **Detect language and speech regions**
   - Run language identification at video or segment level.
   - Apply voice-activity detection to separate speech, silence, music, and noise.
   - Use speaker diarization when multiple speakers matter to the task.
4. **Run automatic speech recognition (ASR)**
   - Produce word-level text with start time, end time, and confidence where supported.
   - Preserve the raw ASR output before correction.
   - Record the ASR model, model version, decoding parameters, language setting, hardware, and runtime.
5. **Normalize words without destroying meaning**
   - Correct encoding, punctuation, casing, repeated fragments, and obvious recognition artifacts.
   - Preserve domain terminology, mathematical notation, code, names, negation, and multilingual expressions.
   - Do not remove stop words or punctuation before retaining an auditable clean transcript.
6. **Segment words into sentences and semantic chunks**
   - Restore punctuation and divide the transcript into complete sentences.
   - Create semantic chunks that respect sentence boundaries and token limits.
   - Retain `course_id`, `video_id`, `speaker_id`, `sentence_id`, timestamps, language, and confidence for every segment.
7. **Validate transcript quality**
   - Compare a stratified sample with human-verified references.
   - Report Word Error Rate (WER), Character Error Rate (CER), sentence-boundary quality, language-identification accuracy, and low-confidence proportions where references are available.
   - Quarantine transcripts that fail minimum quality thresholds.
8. **Prepare text for the selected model**
   - Use cleaned sentences or semantic chunks as the input to TF-IDF, sentence transformers, BGE, DistilBERT, an LLM, RAG, summarization, classification, or topic modeling.
   - Fit learned preprocessing only on the training partition for predictive tasks.
   - Store embeddings separately from the source transcript and record the embedding model/version.
9. **Generate traceable outputs**
   - Every summary, topic, label, or answer must retain references to the originating video, sentence IDs, and timestamps.
   - Human review is required for high-impact interpretations or low-confidence transcripts.

Required transcript schema:

| Field | Description |
|---|---|
| `course_id` | Course identifier |
| `video_id` | Stable video identifier |
| `speaker_id` | Speaker label when diarization is used |
| `sentence_id` | Stable sentence or chunk identifier |
| `start_time_sec` | Segment start time |
| `end_time_sec` | Segment end time |
| `language` | Detected or verified language |
| `transcript_text` | Cleaned sentence-level text |
| `asr_confidence` | Recognition confidence when available |
| `source_type` | Raw ASR, official caption, or human-verified transcript |
| `transcript_version` | Version of the cleaned transcript |

### 2.5 LLM readiness gate

Before activating the LLM content track, verify all of the following:

- At least one valid content source exists: raw media, official captions, or verified transcripts.
- Words and complete sentences have been generated and stored.
- Language and timestamps are available or their absence is explicitly justified.
- Transcript quality has been measured on a representative sample.
- Personally identifiable or sensitive spoken content has been handled according to policy.
- The model input can be traced back to a source video and transcript segment.

If any critical gate fails, report the content LLM track as blocked. Do not replace it with text fabricated from interaction counts.

### 2.6 Perform initial validation

Check schema consistency, file corruption, counts, unique identifiers, timestamps, label availability, class distribution, consent, unexpected columns, duplicate extraction, and train-serving consistency risks.

### Dashboard requirements

- Data-provenance table
- Record counts and time coverage
- Modality and language summaries
- Dataset version and hash
- Media and transcript availability
- ASR model/version and transcript-quality status
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

### 3.6 Clean and audit media transcripts

For video-derived language data, additionally inspect and record:

- Missing, duplicated, corrupt, or truncated media
- Videos containing no detectable speech
- Incorrect language identification
- Low-confidence ASR words and segments
- Repeated phrases, hallucinated phrases, and timestamp gaps
- Speaker-overlap and diarization errors
- Broken sentence boundaries
- Caption/audio misalignment
- Mathematical notation, source code, acronyms, and domain terminology errors
- Personally identifiable or sensitive spoken content

Preserve three distinct layers:

1. Immutable source media or official captions
2. Raw timestamped ASR output
3. Cleaned and sentence-segmented transcript

All corrections must be represented in `logs/transcription_audit.json` with the video ID, affected segment, correction rule, previous value, updated value, reviewer or automated method, and version.

### Dashboard requirements

- Raw-to-cleaned funnel or Sankey diagram
- Missing-value matrix
- Duplicate summary
- Quality-rule table
- Modified, removed, and quarantined counts
- Data-quality score
- Media-to-transcript processing funnel
- ASR confidence and transcript-quality summaries

---

# Phase 2: Exploratory Analysis and Evidence Review

## Step 4 — Exploratory Data Analysis

### 4.1 Create a complete feature inventory

Profile every feature rather than only a convenient subset. For each field, record:

- Business definition, source, modality, and unit
- Data type and inferred semantic type
- Record count, non-null count, and missing percentage
- Unique count, duplicate count, and cardinality ratio
- Mean, median, mode, standard deviation, variance, and coefficient of variation
- Minimum, maximum, range, and the 1st, 5th, 25th, 50th, 75th, 95th, and 99th percentiles
- Interquartile range, median absolute deviation, skewness, and kurtosis
- Zero count, negative count, infinite count, sentinel count, and outlier count
- Constant, near-constant, rare-category, and high-cardinality status
- Earliest/latest timestamps and time coverage when relevant
- Train-time availability, inference-time availability, and leakage-risk status

Export the complete numerical profile and categorical frequency tables as machine-readable files. Charts shown on the dashboard may be prioritized, but the profiling coverage must remain 100%.

### 4.2 Analyze missingness and data completeness

Perform all of the following:

- Missing-value count and percentage by column
- Missing-value count per row or entity
- Missingness co-occurrence and correlation
- Missingness by source, course, institution, time period, demographic group, and target class when legally and methodologically appropriate
- Monotone or systematic missingness patterns
- Comparison of observed vs missing groups for key predictors
- Sentinel-value detection before imputation
- Media, caption, transcript, and ASR availability rates

Required visualizations:

1. Missing-value horizontal bar chart
2. Missingness matrix or heatmap
3. Missingness co-occurrence heatmap
4. Row-level missing-count histogram
5. Missingness by source/course/institution grouped bar chart
6. Raw → valid → cleaned → quarantined data-quality funnel or Sankey diagram

### 4.3 Perform numerical data-distribution analysis

For every important numerical feature, inspect both the raw and transformed distributions. MOOC examples include `total_events`, `total_active_days`, `total_video_plays`, `total_chapters`, `total_forum_posts`, `overall_span_days`, `event_intensity`, `video_intensity`, age, and per-course averages.

Required visualizations should include, where meaningful:

1. Histogram with count scale
2. Histogram with log-scaled y-axis for long-tailed variables
3. KDE or empirical density plot
4. ECDF plot
5. Boxplot
6. Violin plot
7. Q–Q plot against a reference distribution
8. Percentile or quantile plot
9. Raw vs `log1p` side-by-side distribution
10. Before-vs-after scaling distribution
11. Ridgeline or small-multiple distributions by course/institution
12. Distribution by major student segment or model split

Every distribution chart must be accompanied by a compact numerical table containing sample size, missingness, mean, median, standard deviation, IQR, P5, P95, skewness, kurtosis, and detected outlier rate.

Use bin widths selected by an explicit rule such as Freedman–Diaconis, Sturges, or domain-defined bins. Do not allow arbitrary binning to create misleading patterns.

### 4.4 Perform categorical and demographic distribution analysis

For categorical fields such as institution, course, education level, gender, country/region, semester, and enrollment status, calculate counts, proportions, rare levels, entropy, and missingness.

Required visualizations:

- Sorted horizontal bar charts for category frequency
- 100% stacked bar charts for composition comparisons
- Pareto charts for high-cardinality categories
- Treemaps only when hierarchy or composition is important
- Mosaic plots or heatmaps for two categorical variables
- Course × institution and course × semester matrices
- Demographic distribution plots with an explicit missing/unknown category

Pie or donut charts should be limited to a small number of mutually exclusive categories; use bars when precise comparison matters.

### 4.5 Analyze behavior and engagement patterns

For the MOOC context, explicitly examine:

- Enrollment volume and unique students by course and institution
- Number of courses per student
- Cross-institution enrollment
- Event volume, active days, chapters, forum posts, and video plays
- Engagement intensity normalized by active span and course exposure
- Ratios of video, forum, and chapter activity to total events
- Zero-activity, low-activity, sustained-activity, and highly active cohorts
- First-to-last activity span and inactivity gaps
- Engagement consistency across multiple courses
- Course-normalized percentile features to separate student behavior from course design

Required visualizations:

1. Enrollment and unique-student bars by course
2. Student course-count distribution
3. Institution and cross-institution composition
4. Activity-volume small multiples
5. Engagement-ratio distributions
6. Active-days × total-events hexbin or density plot
7. Video plays × chapters scatter/hexbin plot
8. Forum posts × activity intensity plot
9. Engagement profile radar chart for descriptive segments only
10. Course-normalized percentile distributions

### 4.6 Perform temporal and cohort analysis

When timestamps are available, analyze:

- Records, enrollments, events, and active users over time
- Daily, weekly, monthly, semester, and course-run patterns
- Cohort retention and return behavior
- Time since enrollment and time to last activity
- Activity before and after important course milestones
- Seasonality and calendar effects
- Gaps, discontinuities, and changes in collection systems

Required visualizations:

- Time-series line charts with appropriate aggregation
- Calendar or day-of-week × hour heatmaps when event-level timestamps exist
- Cohort retention heatmap
- Survival or Kaplan–Meier curve for time-to-dropout when the definition is valid
- Activity-span and inactivity-gap distributions
- Course-run comparison charts

Never infer within-course sequences from aggregate start and end dates when event-level timestamps do not exist.

### 4.7 Perform bivariate and multivariate analysis

Use methods appropriate to each data-type pair:

- Numerical–numerical: Pearson, Spearman, Kendall, scatter, hexbin, and robust trend line
- Categorical–categorical: contingency tables, chi-square diagnostics, Cramér's V, mosaic plots, and normalized heatmaps
- Numerical–categorical: grouped summary tables, boxplots, violin plots, effect sizes, and suitable statistical tests
- Text–text or embedding data: cosine similarity, semantic-neighbor inspection, and duplicate/near-duplicate checks
- Temporal relationships: lag plots, autocorrelation, cross-correlation, and rolling associations when valid

Required outputs:

1. Pearson correlation heatmap for approximately linear numerical relationships
2. Spearman heatmap for monotonic and skewed relationships
3. Cramér's V matrix for categorical variables
4. Mutual-information ranking
5. Pair plot or sampled scatter-matrix for selected variables
6. Variance Inflation Factor or condition-index table for multicollinearity screening
7. Network view of strong associations when it improves interpretability

Report sample sizes, uncertainty, multiple-comparison considerations, and effect sizes where formal tests are used. Correlation must never be presented as proof of causation.

### 4.8 Analyze outliers, anomalies, and data errors

Use complementary methods such as IQR, robust Z-score, median absolute deviation, Isolation Forest, Local Outlier Factor, multivariate distance, and domain rules.

Required visualizations:

- Boxplots with flagged observations
- Robust Z-score distribution
- Two-dimensional anomaly scatter plot
- Outlier rate by feature, source, course, and institution
- Before/after correction or winsorization comparison when such treatment is justified

Distinguish data errors, rare valid observations, fraud or genuine anomalies, and natural distribution tails. Never remove, cap, or transform an outlier without a documented reason and sensitivity comparison.

### 4.9 Analyze duplicates, identity structure, and source consistency

Evaluate exact duplicates, duplicate identifiers, near-duplicate text/media, repeated enrollment records, the same learner across courses, conflicting values across sources, and entity overlap across data splits.

Required outputs:

- Duplicate-type table
- Entity/course bipartite summary or matrix
- Source reconciliation table
- Conflicting-field heatmap
- Entity-overlap matrix across training, validation, and test partitions

### 4.10 Analyze leakage risk

Check for post-outcome features, target proxies, identifiers that memorize labels, aggregates containing future data, duplicate entities across splits, complete-dataset preprocessing, and human decisions influenced by the outcome.

EDA must be performed in two controlled layers:

1. **Predictor-only EDA:** may use the full pre-split development data only for schema, quality, and unsupervised distribution inspection when this does not learn parameters used by the model.
2. **Outcome-aware EDA:** must be restricted to the training partition. Validation and test targets must remain hidden from feature design and model selection.

Export a leakage audit table with feature name, availability time, source time, prediction time, suspected leakage type, decision, and reviewer.

### 4.11 Analyze text, transcript, and video-content distributions

This subsection is activated only when real captions or transcripts exist. It must not run on video-play counts presented as text.

Measure:

- Videos, transcript segments, sentences, words, and unique tokens
- Transcript duration and speaking rate
- Sentence length, chunk length, and token count
- Language distribution and code-switching
- ASR confidence and low-confidence word rate
- WER/CER on the human-verified sample
- Vocabulary frequency, n-grams, keywords, named entities, and domain terminology
- Topic prevalence and topic change by course/video/time
- Duplicate and near-duplicate sentences
- Semantic embedding norms, similarity, and coverage
- Toxic, sensitive, or personally identifiable content flags where authorized

Required visualizations:

1. Transcript availability by course and video
2. Media duration and transcript-length distributions
3. Words-per-minute distribution
4. Sentence- and chunk-token histograms
5. Language distribution
6. ASR confidence histogram and confidence-by-course boxplot
7. WER/CER comparison by language, course, speaker, or audio-quality band
8. Top unigram, bigram, and trigram bars after documented normalization
9. TF-IDF keyword heatmap by course or topic
10. Topic-prevalence stacked bars or heatmap
11. Sentence-embedding PCA/UMAP projection colored by course/topic/language
12. Semantic-similarity distribution and near-duplicate network/table
13. Transcript timeline showing sentence/topic alignment to video timestamps
14. Word cloud only as a supplementary display, never as the sole text analysis

Every content result must link back to `video_id`, `sentence_id`, and timestamps.

### 4.12 Evaluate dimensionality and manifold structure

Before using dimensionality reduction, fit imputation and scaling on the permitted training or exploratory sample only. Evaluate:

- PCA explained variance and loading stability
- Number of components needed for selected variance thresholds
- UMAP or t-SNE sensitivity to seeds and hyperparameters
- Neighborhood preservation or trustworthiness
- Whether visible groups remain stable across samples and methods

Required visualizations:

- PCA scree and cumulative-variance plot
- PCA loading heatmap or biplot
- PCA projection colored separately by course, institution, and non-target behavioral intensity
- UMAP projection with clearly reported parameters
- Side-by-side projections across seeds or methods

Two-dimensional visual separation is exploratory evidence, not proof of real clusters.

### 4.13 Evaluate clustering feasibility

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

Required clustering diagnostics:

- Four-metric K-selection panel across a documented K range
- WCSS elbow plot with a vertical candidate-K line
- Silhouette-score curve and silhouette plot for each finalist
- Calinski–Harabasz and Davies–Bouldin curves
- Cluster-size distribution and minimum-cluster-size check
- Cluster profile heatmap and standardized centroid plot
- Stability across random seeds, bootstrap samples, and preprocessing variants
- PCA/UMAP visualization colored by cluster, used only as supporting evidence
- External validity comparisons where independent variables or labels legitimately exist

### 4.14 Analyze supervised target distributions when authorized

After splitting, use only the training partition to inspect:

- Class count and percentage
- Target prevalence by course, institution, time, and permitted demographic subgroup
- Numerical predictor distributions by class
- Categorical predictor composition by class
- Potential label inconsistency and label noise
- Rare-class and subgroup sample sufficiency

Required visualizations:

- Class-balance bar chart
- Target rate with confidence intervals by course/institution
- Predictor-by-class box/violin plots
- Categorical composition by class
- Outcome-consistency audit chart

Do not use validation or test outcome distributions to redesign features, thresholds, or models.

### 4.15 Statistical and visual integrity requirements

- Display the denominator and missing-value treatment for every percentage.
- Label whether axes are raw, log-transformed, standardized, or normalized.
- Show uncertainty intervals for estimates when useful.
- Use color-blind-safe palettes and readable labels.
- Avoid truncated axes unless clearly marked and justified.
- Use consistent units, category order, and feature names across charts.
- Record the dataset version, filter, sample size, seed, and code version for every exported figure.
- Use representative sampling only when computationally necessary; publish a sampling report and compare the sample with the full cohort.
- Export the numerical data behind each important chart as CSV or Parquet.
- Record each EDA finding together with its downstream implication for cleaning, features, modeling, evaluation, or monitoring.

### Dashboard requirements

- Dataset overview and feature inventory
- Numerical and categorical distribution gallery
- Raw-vs-transformed distribution comparisons
- Missingness, duplicate, and cleaning-flow views
- Course, institution, demographic, behavior, and temporal views
- Pearson, Spearman, Cramér's V, mutual-information, and multicollinearity views
- Outlier and anomaly diagnostics
- Transcript/ASR/content EDA when real transcripts exist
- PCA/UMAP diagnostics and sampling evidence
- Leakage-risk table
- K-selection metrics, silhouette diagnostics, cluster stability, and profiles
- Training-only target-distribution views for supervised tasks
- Downloadable statistical tables and chart-source data
- Clear annotations stating the finding, limitation, and downstream action for every major visualization

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

For real video transcripts, candidate features may include:

- Sentence, token, and speaking-rate statistics
- Language and code-switch indicators
- ASR confidence and transcript-quality indicators
- TF-IDF features fitted on training text only
- Topic proportions fitted on training text only
- Named-entity and domain-term counts
- Sentence or document embeddings with recorded model/version
- Timestamp-aligned topic, difficulty, and semantic-change features
- Aggregations from sentence → video → course → learner, with explicit lineage

Do not create transcript features when only video interaction counts are available. Behavioral counts and transcript content are separate modalities and must remain separately named until an explicitly documented fusion step.

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

#### Transcript, NLP, and LLM candidates

Activate this family only after the LLM readiness gate in Step 2 has passed.

- Keyword and TF-IDF baselines
- Logistic regression, linear SVM, or Naive Bayes over text features
- Topic models such as NMF, LDA, or BERTopic when topic discovery is the objective
- Sentence-transformer or BGE embeddings with an appropriate downstream model
- DistilBERT or another encoder fine-tuned for the defined supervised task
- Retrieval-Augmented Generation over sentence-level, timestamped transcript chunks
- Generative LLM summarization, extraction, classification, or question answering with grounded citations
- Multimodal fusion of transcript, visual, audio, and behavioral features when each modality is genuinely available

For generative tasks, compare against a simple extractive or retrieval baseline. Record prompts, system instructions, model/version, temperature, retrieval configuration, context-window strategy, and output schema.

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

### 8.6 ASR, transcript, and LLM metrics

When the video-content track is active, evaluate each stage separately:

- **ASR:** Word Error Rate, Character Error Rate, insertion/deletion/substitution counts, timestamp alignment, and low-confidence rate
- **Sentence segmentation:** boundary precision, recall, and F1 when a reference sample exists
- **Retrieval:** Recall@K, Precision@K, MRR, nDCG, and evidence coverage
- **Text classification:** accuracy, precision, recall, F1, PR-AUC, ROC-AUC, and calibration as appropriate
- **Summarization:** factual consistency, evidence coverage, omission rate, redundancy, and human rubric scores; lexical metrics may be supplementary
- **Generative question answering:** answer correctness, groundedness, citation correctness, refusal quality, and hallucination rate
- **Multilingual outputs:** meaning preservation, terminology consistency, language correctness, and subgroup performance by language

Human evaluation must use a documented rubric, blinded sampling where practical, multiple reviewers for subjective criteria, and inter-rater agreement. An LLM-as-judge may assist but must not be the only evaluator for high-impact claims.

### 8.7 Protect evaluation integrity

- Use the test set only after model selection is complete.
- Report cross-validation means and variation.
- Use confidence intervals or bootstrapping where appropriate.
- Examine training, validation, and test performance gaps.
- Compare results with predefined success criteria.
- Never select a model using only one metric.

### 8.8 Optimize thresholds and calibration

Choose classification thresholds with validation data, assess precision–recall trade-offs, inspect calibration, apply Platt or isotonic calibration if necessary, and evaluate the final locked configuration on the test set.

### 8.9 Conduct error analysis

Analyze false positives, false negatives, large residuals, subgroup errors, temporal errors, source-specific errors, missingness patterns, confidence bands, label noise, and distribution shifts.

### 8.10 Apply explainable AI

Use model coefficients, feature importance, permutation importance, partial dependence, ICE, SHAP, LIME, or counterfactual explanations as appropriate. Feature importance must not be presented as proof of causality.

### 8.11 Conduct a fairness audit

Where relevant and legally permitted, compare performance, recall, precision, false-positive and false-negative rates, calibration, sample sizes, and confidence intervals across groups.

### 8.12 Apply the optimization cycle

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

For video-content and LLM systems, the deployed pipeline must expose the complete upstream conversion:

```text
Video/audio/caption input
→ Media and schema validation
→ Audio extraction and speech-region detection
→ Language identification
→ ASR with word timestamps
→ Transcript normalization
→ Sentence segmentation and semantic chunking
→ Transcript-quality gate
→ Text encoding, retrieval, or LLM processing
→ Grounded output with video/sentence/timestamp references
→ Safety and output-schema validation
→ Logging and monitoring
```

If the system receives verified captions or transcripts, it may begin at transcript validation, but it must still preserve source, version, sentence boundaries, and timestamps where available.

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

The EDA section must include a navigable visualization catalog covering distributions, missingness, categorical composition, behavior, time, associations, outliers, dimensionality, and task-specific diagnostics. Every major chart must show or link to its numerical source table and include a concise finding, limitation, and downstream action.

When the LLM content track is requested, show the complete readiness chain:

```text
Media availability
→ Audio extraction
→ ASR completion
→ Word-level transcript
→ Sentence segmentation
→ Transcript quality
→ LLM/NLP input readiness
→ Model evaluation
```

If the available data contains only video-play behavior columns, the dashboard must state that the content LLM track is unavailable. It must not display behavior-summary text as a video transcript.

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

For video-to-text-to-LLM systems, also monitor media-ingestion failures, language mix, speech/no-speech rate, ASR confidence, WER/CER on audited samples, transcript-length and token distributions, sentence/chunk truncation, retrieval hit rate, evidence coverage, citation correctness, hallucination rate, safety-filter activation, and model/prompt/index versions.

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
21. Complete EDA figure catalog and chart-source tables
22. Media-provenance and transcript-readiness manifest
23. Raw-ASR, cleaned-sentence, and alignment schemas when the content track is active
24. ASR and transcript-quality evaluation report
25. LLM prompt, retrieval, grounding, and citation-evaluation report

---

# Minimum Quality Gates

| Quality gate | Passing requirement |
|---|---|
| Problem definition | Target, unit of analysis, decision context, and success criteria are clearly defined |
| Data provenance | Source, ownership, license, schema, version, and hash are recorded |
| Privacy | Privacy, consent, access control, and retention requirements are satisfied |
| Data quality | Cleaning decisions are documented and auditable |
| Media provenance | Every video/audio/caption source has an identifier, license, checksum, language, duration, and version |
| Transcript readiness | Content LLM work uses real captions or ASR output segmented into traceable words and sentences; behavior counts are not treated as transcripts |
| Transcript quality | ASR and sentence-segmentation quality are measured on a representative human-verified sample |
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

For video-content and LLM analysis, the content branch inside the lifecycle is:

```text
Acquire Video/Audio/Captions
  → Extract Audio
  → Detect Language and Speech
  → Transcribe Words with Timestamps
  → Normalize and Segment into Sentences
  → Validate Transcript Quality
  → Perform Transcript EDA
  → Build Text Features, Retrieval Index, or LLM Input
  → Train/Evaluate the Selected NLP or LLM Method
  → Produce Grounded Outputs with Source References
  → Monitor ASR, Retrieval, Grounding, and Generation Quality
```

The final model should not automatically be the most complex model or the model with the highest single metric. It should provide the best justified balance of predictive performance, stability, interpretability, fairness, operational feasibility, risk, and business value.
