# workflow_docs/phase_2/step_2_1.md

## Phase 2 – Signal Denoising & SQI Audit

**Goal:** Load raw waveforms, apply baseline‑wander removal (0.5–45 Hz Butterworth band‑pass) and power‑line notch (50 Hz), compute Signal Quality Index (SQI) metrics, and quarantine low‑quality segments.

**Key actions**
- Read 12‑lead raw arrays from `data/raw/records100/` or `records500/`.
- Apply Butterworth band‑pass filter & 50 Hz notch filter (SciPy).
- Compute SNR, kurtosis, skewness for each lead.
- Flag recordings that fail configurable thresholds and write a quarantine list.
- Persist cleaned arrays to `data/cleaned/` and log parameters to `logs/cleaning_audit.json`.

**Reference implementation:** `src/cleaning/filter_signals.py`
