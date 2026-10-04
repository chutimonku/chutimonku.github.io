# Model Card: Insurance Claims Intelligence & Settlement Ratio Forecasting

## 1. Model Details
- **Model Name:** Insurance Claims Settlement Forecaster & Operational Segmenter
- **Version:** 2.0.0 (Audit & Governed Release)
- **Model Type:** Panel Autoregressive Regression / Persistence Benchmark + K-Means ($K=3$)
- **Developer:** Antigravity Data Science Team
- **Date:** September 2026
- **License:** Proprietary / Internal Regulatory Analytics

## 2. Intended Use
- **Primary Purpose:** Exploratory analysis, operational segment identification, and predictive benchmarking of next-year life insurance claims settlement rates (`claims_paid_ratio_no`).
- **Target Audience:** Actuarial teams, regulatory compliance officers, insurance risk auditors.
- **Out-of-Scope Uses:** Automated underwriting, claim denial decisions, or individual policyholder claim evaluation. This model operates strictly at the aggregated insurer-year level.

## 3. Training and Evaluation Data
- **Dataset:** IRDAI Public Disclosures (Group Death Claims).
- **Records:** 149 annual insurer records across 45 life insurance companies (2017–2022).
- **Forecast Panel:** 104 consecutive annual pairs.
- **Split Protocol:**
  - Training Period: Target Years $\le 2019$ (52 pairs)
  - Validation Period: Target Year $2020$ (26 pairs)
  - Held-out Test Period: Target Year $2021$ (26 pairs)

## 4. Performance & Baseline Benchmark
| Model | Family | Validation RMSE | Held-Out Test RMSE | Deployment Status |
|---|---|---|---|---|
| **Persistence Baseline** | Domain Heuristic | 0.0384 | 0.0485 | **Champion (Production)** |
| **Ridge Regression** | Regularized Linear | 0.0521 | 0.0705 | Challenger |
| **Random Forest** | Ensemble Bagging | 0.0543 | 0.0768 | Challenger |
| **Gradient Boosting** | Ensemble Boosting | 0.0562 | 0.0782 | Challenger |
| **Mean Baseline** | Naive Baseline | 0.1248 | 0.1312 | Benchmark |

> **Key Decision Rationale:** The machine learning challengers (Random Forest, Gradient Boosting, Ridge) did not beat the domain-native **Persistence Baseline** on the held-out test set. Following strict enterprise governance (**IN_Workflow.md Step 8.6 & 9.5**), ML is **NOT** deployed into automated production. Persistence is locked as champion, and ML models are maintained in experimental tracking.

## 5. Ethical Considerations & Fairness
- Evaluated across public sector (LIC) vs private sector insurers.
- Acknowledges structural market concentration (LIC handles >65% of claims volume).
- Regularization and log-transforms are enforced to prevent single-entity dominance from corrupting smaller insurer predictions.

## 6. Caveats and Limitations
1. Sample size is limited to 149 observations due to annual disclosure frequency.
2. Sudden macroeconomic or pandemic shocks (e.g., COVID-19 in 2020–2021) cause transient ratio deviations.
3. Raw data errors (e.g., Sahara Life reporting anomalies) must be resolved at the provider level.
