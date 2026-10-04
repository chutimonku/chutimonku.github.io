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