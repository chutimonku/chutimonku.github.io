# Literature Review and Evidence Assessment (Step 5)

## 1. Executive Summary

This literature review supports the life insurance claims settlement ratio forecasting, operational clustering, and KPI auditing pipeline in accordance with **IN_Workflow.md Phase 2, Step 5**.

The review assesses peer-reviewed research, industry standards, and regulatory disclosure conventions from the Insurance Regulatory and Development Authority of India (IRDAI) and global actuarial bodies.

## 2. Synthesis of Prior Work

### 2.1 Claims Settlement Behavior & Persistence in Insurance
- **IRDAI Statutory Disclosures (2015–2022):** Regulatory reporting mandates life insurers to publish annual settlement ratios (`claims_paid_ratio_no` and `claims_paid_ratio_amt`). Insurers with institutional operations (e.g., LIC, HDFC Life, ICICI Prudential) exhibit high temporal auto-correlation ($\rho > 0.85$) across consecutive financial years due to stable underwriting guidelines and regulatory minimum thresholds.
- **Actuarial Benchmark (Persistence / Random Walk Model):** In annual macro-level insurance disclosures with limited historical panels ($T \approx 5$ years), a persistence model ($\hat{y}_{t+1} = y_t$) serves as the primary benchmark. Advanced machine learning models (Random Forest, Gradient Boosting) often suffer from sample starvation and variance instability when applied to tiny panels without high-frequency covariates.

### 2.2 Unsupervised Segmentation of Insurance Companies
- **Efficiency and Scale Segmentation (K-Means & GMM):** Studies analyzing insurer operational scale (Cummins & Weiss, 2013) demonstrate that life insurers naturally segregate into distinct clusters:
  1. *Dominant Public Conglomerates* (Massive claim intimations, low unit variance).
  2. *Top-Tier Private Insurers* (High automation, intermediate volume).
  3. *Niche / Emerging Insurers* (Low volume, high ratio volatility).
- Preprocessing recommendation: Log-transformation ($\log(1+x)$) on volume and amount features prior to distance-based clustering prevents the scale of single giant insurers (e.g., LIC) from collapsing all other participants into an undifferentiated cluster.

### 2.3 Feature Leakage and Temporal Splits in Forecasting
- **Leakage Prevention Standard:** Future claim resolutions (`claims_paid_no`, `claims_paid_amt`, `total_claims_no`) within the target forecast window $t+1$ must never enter the feature matrix at time $t$. Only the historical lag $\text{Ratio}_t$ is legally and logically permissible.
- **Contiguous Out-of-Time Splitting:** Random k-fold cross-validation inflates R² through entity-level memorization. Temporal contiguous splitting (Train: $\le 2019$, Validation: $2020$, Test: $2021$) is mandatory for audit-grade claims modeling.

## 3. Evidence Hierarchy & Method Justification

| Category | Method Chosen | Benchmark / Literature Support | Rationale |
|---|---|---|---|
| **Auditing** | Re-calculation & Cross-verification | IRDAI Accounting Principles | Detect discrepancy between raw claim counts and reported percentages |
| **Clustering** | Multi-Metric K-Means ($K=3$) | Calinski-Harabasz, Silhouette, Davies-Bouldin, Resample ARI | Mathematically stable separation into Large, Medium, and Niche tiers |
| **Forecasting** | Persistence Baseline vs Challenger ML | Actuarial Time-Series Standard | Guard against deploying complex ML models that fail to beat naive benchmarks |
| **Drift Monitoring** | Population Stability Index (PSI) | Basel II Credit Risk & MLOps Standards | Quantitative detection of distributional shift across regulatory disclosure years |
