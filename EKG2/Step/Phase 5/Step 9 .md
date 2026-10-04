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

### 9.2 Validate the input schema

Validate required fields, data types, ranges, categories, missingness, timestamps, file formats, media dimensions, text encoding, batch sizes, and unexpected columns.

For signal or waveform-image inputs, validate sampling rate, units, lead/channel identity and order, duration, calibration, scale, image orientation, crop completeness, image resolution, quality thresholds, and source format. Reject or route uncertain inputs to human review rather than coercing them silently. The production pipeline must reproduce the validated preprocessing version exactly.

### 9.3 Select the deployment mode

Choose batch processing, online API, streaming inference, edge deployment, embedded application, or human-in-the-loop decision support.

### 9.4 Perform pre-production testing

Conduct unit, integration, parity, schema, leakage, load, latency, security, artifact-integrity, and rollback tests.

### 9.5 Create a model card

Document intended and out-of-scope uses, training data, metrics, threshold, limitations, ethical considerations, known failure cases, version, owner, and review date.

For high-impact clinical or physiological applications, include data source and population, label provenance, acquisition settings, repeated-observation policy, input quality requirements, external/temporal validation status, subgroup results, human oversight, abstention behavior, safety limitations, and explicit statement that the system supports—not replaces—qualified professional judgment unless a separately validated and authorized use permits otherwise.

### Dashboard requirements

- Deployment, model, and pipeline status
- Schema-test results
- Latency and throughput
- Readiness checklist
- Rollback version

---