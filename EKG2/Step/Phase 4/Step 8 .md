# Phase 4: Evaluation, Explainability, and Decision-Making

## Step 8 — Model Evaluation, Optimization, and Error Analysis

### 8.1 Establish a baseline

Compare every model with an appropriate majority, random, mean, median, seasonal-naive, rule-based, or current-process baseline.

### 8.2 Classification metrics

$$
Accuracy=\frac{TP+TN}{TP+TN+FP+FN}
$$

$$
Precision=\frac{TP}{TP+FP}
$$

$$
Recall=\frac{TP}{TP+FN}
$$

$$
F1=2\times\frac{Precision\times Recall}{Precision+Recall}
$$

$$
Brier=\frac{1}{N}\sum_{i=1}^{N}(p_i-y_i)^2
$$

Also consider specificity, balanced accuracy, ROC-AUC, PR-AUC, log loss, Matthews correlation coefficient, top-k accuracy, and calibration error.

### 8.3 Regression metrics

Use appropriate combinations of MAE, RMSE, median absolute error, R-squared, MAPE or sMAPE, and prediction-interval coverage.

### 8.4 Forecasting metrics

Use MAE, RMSE, MASE, sMAPE, forecast bias, interval coverage, and backtesting performance as appropriate.

### 8.5 Clustering metrics

Evaluate only metrics applicable to the clustering family and data: WCSS/inertia, silhouette, Calinski–Harabasz, Davies–Bouldin, cluster-size balance, noise share, convergence, profile interpretability, runtime, and repeated-fit stability. For K-based work, report seed/resample ARI and NMI when common observation IDs permit assignment comparison. If external reference labels are available, report external ARI/NMI separately and preserve their isolation from unsupervised fitting. Report variation across repeats, not only a best run.

### 8.6 Protect evaluation integrity

- Use the test set only after model selection is complete.
- Report cross-validation means and variation.
- Use confidence intervals or bootstrapping where appropriate.
- Examine training, validation, and test performance gaps.
- Compare results with predefined success criteria.
- Never select a model using only one metric.

### 8.7 Optimize thresholds and calibration

Choose classification thresholds with validation data, assess precision–recall trade-offs, inspect calibration, apply Platt or isotonic calibration if necessary, and evaluate the final locked configuration on the test set.

### 8.8 Conduct error analysis

Analyze false positives, false negatives, large residuals, subgroup errors, temporal errors, source-specific errors, missingness patterns, confidence bands, label noise, and distribution shifts.

### 8.9 Apply explainable AI

Use model coefficients, feature importance, permutation importance, partial dependence, ICE, SHAP, LIME, or counterfactual explanations as appropriate. Feature importance must not be presented as proof of causality.

For images, candidate visual explanation methods include Grad-CAM, saliency maps, occlusion sensitivity, and attention visualization. For waveform sequences, candidate methods include Integrated Gradients, temporal occlusion, saliency, and feature attribution over validated engineered features. Explanations must be tested for stability and plausibility, shown with the original signal/image and quality context, and never treated as evidence of clinical causality or a substitute for expert review.

### 8.10 Conduct a fairness audit

Where relevant and legally permitted, compare performance, recall, precision, false-positive and false-negative rates, calibration, sample sizes, and confidence intervals across groups.

For high-impact health-related uses, also evaluate clinically relevant subgroups and acquisition conditions where lawful and adequately sampled: age bands, sex where appropriate, device or site, lead configuration, image quality, signal quality, and repeated versus first observation. Small or unrepresentative subgroups must be reported as uncertainty or a limitation rather than used to make broad safety claims.

### 8.10a Clinical and operational safety review for high-impact uses

Before a health-related model is presented for use, define intended users, the decision supported, the required human review, uncertainty display, abstention/rejection policy, escalation path, contraindicated use, validation population, and failure modes. Assess sensitivity to noise, missing leads/channels, preprocessing variation, device/site shift, image quality, repeated observations, and label uncertainty. A retrospective benchmark does not by itself demonstrate clinical safety, prospective validity, regulatory clearance, or fitness for diagnosis.

### 8.11 Apply the optimization cycle

Repeat Steps 6–8 when criteria are unmet, leakage is discovered, error analysis identifies a fixable issue, features are unstable, or the model fails to generalize.

Stop when criteria are met, improvements fall below a predefined minimum, resources are exhausted, complexity is unjustified, or data quality prevents further progress.

### Dashboard requirements

- Model-comparison table
- Training, validation, and test metrics
- Confusion matrix and task-appropriate curves
- Calibration and residual plots
- Explainability results
- Error and fairness analyses
- Final model-selection rationale

---