# Candidate Model Selection & Architectural Rationale

## 1. Selection Criteria & Theoretical Diversity

To identify the champion model for student risk prediction, we evaluate nine predictive families plus a null baseline. Multiple parameter settings inside one family are reported as configurations, not misrepresented as different algorithms:
1. **Linear Probabilistic Models (L2-Regularized Logistic Regression):** Provides mathematically interpretable coefficients and well-calibrated posterior probabilities. Serves as our primary parametric benchmark.
2. **Sparse Regularized Linear Classifiers (SGD Classifier with ElasticNet):** Evaluates scalable stochastic optimization and feature sparsity under combined L1/L2 penalties.
3. **Gaussian Naive Bayes:** Supplies a fast generative probability benchmark with a conditional-independence assumption.
4. **Calibrated Linear Support Vector Machine:** Tests a maximum-margin boundary; three-fold sigmoid calibration inside the training set converts margins into probabilities for Brier scoring and risk tiers.
5. **Single Decision Tree:** Provides transparent non-linear rules under controlled depth and minimum leaf size.
6. **Bagging Tree Ensembles (Random Forest Classifier):** Aggregates bootstrap-trained randomized trees to capture non-linear engagement thresholds.
7. **Highly Randomized Tree Ensembles (Extra Trees):** Randomizes split thresholds more strongly than Random Forest, creating a distinct bias-variance trade-off.
8. **Gradient Boosted Decision Trees (Histogram GBDT):** Sequentially constructs trees that correct prior residual errors and model tabular interactions.
9. **Feed-Forward Neural Networks (Multi-Layer Perceptron):** Models higher-order non-linear feature representations.
10. **Heuristic Null Baseline (Dummy Classifier):** Predicts the prior class frequency to establish the empirical lower bound.

---

## 2. Imbalanced Learning Strategy

With an observed positive class rate of ~4.13%, unweighted models tend to predict the negative majority class (non-completer) excessively. We evaluate:
- **Cost-Sensitive Weighting (`class_weight='balanced'`):** Inversely weights loss functions proportionally to class frequencies ($w_j = \frac{n}{k \cdot n_j}$).
- **Threshold Optimization:** Deriving operational decision thresholds that maximize F1-score or balance Precision and Recall for targeted academic advising interventions.
- **Continuous Risk Tiering:** Calibrating posterior probabilities $\hat{p} \in [0, 1]$ to partition students into 3 actionable tiers rather than relying on a rigid binary cutoff.

---

## 3. Evaluation & Locking Decision Rule

The champion model is selected before holdout interpretation using the following deterministic validation ranking:
1. **Primary ranking:** highest validation PR-AUC, appropriate for the 4.13% positive class.
2. **First tie-break:** highest validation ROC-AUC.
3. **Second tie-break:** lowest validation Brier Score.

Runtime is reported as an operational trade-off. Fairness and error diagnostics are conducted after selection and are used to qualify deployment, not to search the test set for a more favorable winner.

Upon final selection, the model parameters and pipeline will be cryptographically locked via SHA-256 before holdout test set evaluation.
