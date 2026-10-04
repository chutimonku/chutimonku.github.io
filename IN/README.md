# Insurance Claims Intelligence & Machine Learning Workflow

An enterprise-ready, audit-ready, reproducible, and bilingual dashboard-integrated machine learning standard compliant with [`IN_Workflow.md`](file:///Users/chingli/Desktop/IN/IN_Workflow.md).

## Project Overview

This project executes an 11-step end-to-end data science lifecycle across three interconnected tracks on the IRDAI life insurance statutory public disclosures:
1. **Track C — KPI Quality & Integrity Audit**: Mathematical consistency verification (`claims_paid_ratio_no = claims_paid_no / total_claims_no`), zero-denominator handling, domain boundary audit, and Data Quality Scoring.
2. **Track A — Unsupervised Operational Segmentation**: Robust-scaled, log-transformed multi-metric K-Means clustering ($K=3$) with candidate algorithm comparison (K-Means, GMM, Agglomerative) and stability testing (Resample ARI).
3. **Track B — Governed Next-Year Forecasting & Ablation**: Contiguous temporal panel split (Train $\le 2019$, Validation $2020$, Test $2021$), feature ablation study, candidate model leaderboard (6 models/baselines), fairness audit, and strict deployment governance.

## Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Run the complete end-to-end pipeline
python3 main.py

# Run all automated tests (100% passing)
pytest
# or
pytest tests.py
```

## Standard Directory Layout
```text
.
├── config/                  # Configuration & schemas (project, data_schema, monitoring)
├── data/                    # Immutable raw, quarantined target, cleaned & processed splits
├── models/                  # Baselines, experiments, candidate models, and final serialized pipelines
├── outputs/                 # EDA, clustering, evaluation, explainability, fairness, monitoring & dashboard
├── reports/                 # Literature review, model card, data sheet, and final report
├── tests/                   # Modular data, pipeline, and model tests (pytest auto-discovery)
└── logs/                    # Provenance, cleaning audit, experiments, evaluation, deployment, and PSI logs
```

## Key Findings & Governance Decisions
- **Persistence Champion:** On the held-out test set (Target Year 2021), the **Persistence Baseline** achieved RMSE = 0.0485, outperforming all complex machine learning models (Ridge: 0.0705, Random Forest: 0.0768, Gradient Boosting: 0.0782).
- **Deployment Status:** In strict compliance with enterprise governance, complex ML models are **not deployed** for automated decision-making. The Persistence Baseline is approved as the production champion, with ML preserved as an experimental challenger.
- **Interactive Dashboard:** Open [`outputs/dashboard/index.html`](file:///Users/chingli/Desktop/IN/outputs/dashboard/index.html) to explore the 11-step workflow, in-depth analytical result explanations, and interactive what-if simulator.
