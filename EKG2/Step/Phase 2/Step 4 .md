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