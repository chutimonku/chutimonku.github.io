# workflow_docs/phase_1/step_1_1.md

## Phase 1 – Ingestion & Data Foundation

**Goal:** Load the raw PTB‑XL records, extract metadata, and establish the primary key (`ecg_id`) with patient identifier (`patient_id`).

**Key actions**
- Read `ptbxl_database.csv` and `scp_statements.csv` from `data/raw/`.
- Verify waveform files (100 Hz & 500 Hz) using `wfdb.rdsamp`.
- Save interim metadata to `data/interim/ptbxl_interim_metadata.csv`.
- Record provenance (file hashes, record counts) in `logs/data_provenance.json`.

**Reference implementation:** `src/ingestion/load_ptbxl.py`
