# Data Sheet: IRDAI Life Insurance Claims Dataset

## 1. Motivation
- **Purpose:** Public regulatory oversight and statutory disclosure of life insurance claims handling in India.
- **Funding/Creators:** Published in accordance with Insurance Regulatory and Development Authority of India (IRDAI) annual disclosure mandates.

## 2. Composition
- **Total Records:** 149 observations.
- **Attributes:** 25 columns covering claim counts, claim monetary amounts, ratios, and entity metadata.
- **Unit of Analysis:** One insurer per business line (Group Death Claims) per financial year.
- **Coverage:** Financial Years 2017-18 through 2021-22.
- **Missing Data:** 0 missing values in core accounting columns. Certain ratios exhibit edge-case zero denominators when total claims are zero.

## 3. Collection Process
- Aggregated from statutory audited filings submitted by licensed life insurance companies.
- Immutable source data is stored at `data/raw/dataset.csv` with SHA-256 hash validation.

## 4. Preprocessing & Hygiene
- Isolated target column `claims_paid_ratio_no` into quarantine (`data/quarantine/target.csv`).
- Generated clean features artifact (`data/cleaned/cleaned_features.csv`).
- Full audit rules logged in `logs/cleaning_audit.json`.
