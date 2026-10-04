# Exploratory Data Analysis: Key Findings & Downstream Impacts

## 1. Distributional Skewness & Outliers
- **Finding:** The most right-skewed inspected variable is `video_intensity` with observed skewness 71.60; activity variables have long upper tails.
- **Impact on Step 5 (Feature Engineering):** Standard Euclidean algorithms would be distorted by high-magnitude outliers. Therefore, we mandate a `log1p(x) = log(x + 1)` transformation on count metrics combined with `RobustScaler` (median and IQR) to ensure stable scaling.

## 2. Multicollinearity & Redundancy
- **Finding:** The strongest absolute Spearman relationship among inspected numerical variables is `total_events` versus `mean_events_per_course` (rho=0.995).
- **Impact on Steps 6-7 (Model Training):** High-dimensional collinearity creates artificial distance stretching in standard Euclidean space. This justifies non-linear latent compression via Deep Autoencoders and manifold projection (PCA/UMAP) to decorrelate features before clustering.

## 3. Class Imbalance & Student Posture
- **Finding:** 77.8% of students have fewer than 5 recorded active days, while 8.7% have at least 14 active days.
- **Impact on Steps 6-8 (Clustering & Evaluation):** Prevents the use of algorithms that enforce equal cluster sizes. We establish a minimum cluster size threshold of >= 2.0% to guard against trivial singleton clusters while allowing organic population proportions.

## 4. Cross-Institutional Heterogeneity
- **Finding:** Course duration and chapter structures differ between HarvardX humanities/social science courses and MITx engineering/computer science offerings.
- **Impact on Feature Engineering:** We construct normalized intensity ratios (`chapters_per_day`, `video_intensity`, `event_intensity`) that benchmark activity relative to individual learner enrollment span rather than raw course chapter counts.
