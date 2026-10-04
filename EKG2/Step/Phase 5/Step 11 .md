## Step 11 — Monitoring, Maintenance, and Feedback Loop

### 11.1 Monitor all relevant dimensions

Monitor data quality, schema, missingness, data drift, concept drift, prediction drift, performance drift, calibration drift, fairness drift, latency, throughput, error rate, cost, and failures.

For signals and waveform images, additionally monitor device/vendor/source distribution, sampling rate, lead/channel availability, signal/image quality, filter/preprocessing version, rejected-input rate, extraction failure rate, missing-modality rate, and distribution of repeat observations. Alert thresholds must be evidence-based and reviewed for the intended setting; a generic threshold is not a clinical safety guarantee.

### 11.2 Calculate the Population Stability Index

$$
PSI=\sum_i(\mathrm{Actual}_i-\mathrm{Expected}_i)\ln\left(\frac{\mathrm{Actual}_i}{\mathrm{Expected}_i}\right)
$$

Suggested initial thresholds:

- $PSI < 0.10$: Normal
- $0.10 \leq PSI < 0.25$: Warning
- $PSI \geq 0.25$: Significant drift

These are guidelines, not universal rules. Adjust them for sample size, feature importance, domain behavior, and business risk.

### 11.3 Define performance triggers

Examples include a recall or F1 decline greater than 15%, excessive calibration error, increased missingness, excessive unknown categories, unacceptable fairness gaps, SLA failures, schema changes, or data-source changes.

### 11.4 Implement the feedback loop

```text
Monitor production
        ↓
Detect degradation
        ↓
Validate the alert and identify the root cause
        ↓
Return to Step 2 if new data is required
Return to Step 3 if cleaning rules must change
Return to Step 6 if features or models must change
        ↓
Retrain and evaluate
        ↓
Review and approve
        ↓
Deploy using shadow or canary testing
        ↓
Complete deployment or roll back
```

### 11.5 Define a retraining policy

Specify the schedule, triggers, minimum new sample size, label delay, approval process, champion–challenger comparison, rollback conditions, artifact retention, and model-retirement policy.

### Dashboard requirements

- PSI gauge and drift trends
- Performance and calibration trends
- Fairness and data-quality status
- Service health and current model version
- Last retraining and next review dates
- Feedback-loop status

---

# Final Deliverables

Each project should provide, where applicable:

1. Problem statement and success criteria
2. Data-provenance log
3. Data dictionary and schema
4. Cleaning-audit log
5. EDA report
6. Literature review
7. Feature-lineage and leakage report
8. Experiment log
9. Model-comparison table
10. Confusion matrix or task-appropriate evaluation plots
11. Error analysis
12. Explainability report
13. Fairness report
14. Serialized inference pipeline
15. Input-schema validator
16. Model card
17. Monitoring and retraining plan
18. Reproducible source code
19. Environment and dependency specification
20. Interactive HTML report

---

# Minimum Quality Gates

| Quality gate | Passing requirement |
|---|---|
| Problem definition | Target, unit of analysis, decision context, and success criteria are clearly defined |
| Data provenance | Source, ownership, license, schema, version, and hash are recorded |
| Privacy | Privacy, consent, access control, and retention requirements are satisfied |
| Data quality | Cleaning decisions are documented and auditable |
| Leakage prevention | No target, temporal, entity, or preprocessing leakage is detected |
| Data splitting | Splits correctly account for class, entity, group, spatial, and temporal structure |
| Feature processing | Learned transformations are fitted only on training data |
| Baseline | Every candidate is compared with an appropriate baseline |
| Model selection | Candidate models are appropriate for the problem and data |
| Evaluation | Validation and test sets remain independent |
| Explainability | The explanation method matches the model and risk level |
| Fairness | Relevant subgroup performance is evaluated |
| Deployment | Unified pipeline, schema, integrity, and rollback tests pass |
| Reproducibility | Data, code, configuration, environment, and seed versions are recorded |
| Monitoring | Drift, performance, alert, retraining, and rollback plans exist |
| Reporting | Results, assumptions, limitations, and risks are communicated transparently |

---

# End-to-End Lifecycle

The workflow is iterative rather than strictly linear:

```text
Define
  → Gather
  → Clean
  → Explore
  → Review Evidence
  → Engineer Features
  → Select and Train Models
  → Evaluate and Optimize
  → Deploy
  → Communicate
  → Monitor
       ↓
  Feedback and Retraining
       ↓
  Return to the appropriate earlier step
```

The final model should not automatically be the most complex model or the model with the highest single metric. It should provide the best justified balance of predictive performance, stability, interpretability, fairness, operational feasibility, risk, and business value.
