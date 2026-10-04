# Supervised Model Experiment Log

Generated from the completed Step 6-7 training artifacts. All reported values below
come from the fixed validation partition; the untouched test partition is not used
to choose the provisional winner.

## Reproducibility

- Random seed: `42`
- Training students: `234,955`
- Validation students: `50,347`
- Transformed feature count: `57`
- Candidate configurations: `14`
- Algorithm families: `10`
- Selection rule: highest validation PR-AUC; ROC-AUC, Brier score, threshold metrics,
  runtime, and model-family rationale are retained as supporting evidence.

## Validation Results

| Rank | Model | Family | Validation ROC-AUC | Validation PR-AUC | Brier | Time (s) |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | Random Forest (Depth=15, 100 Trees) | Bagging Ensemble | 0.9931 | 0.8529 | 0.0219 | 3.79 |
| 2 | HistGradientBoosting (lr=0.10, max_iter=150) | Boosting Ensemble | 0.9934 | 0.8512 | 0.0278 | 1.80 |
| 3 | HistGradientBoosting (lr=0.05, max_iter=150) | Boosting Ensemble | 0.9934 | 0.8510 | 0.0279 | 3.28 |
| 4 | Multi-Layer Perceptron (64, 32) | Neural Network | 0.9929 | 0.8459 | 0.0130 | 21.45 |
| 5 | Random Forest (Depth=10, 100 Trees) | Bagging Ensemble | 0.9927 | 0.8372 | 0.0284 | 3.62 |
| 6 | Extra Trees (Depth=15, 150 Trees) | Randomized Tree Ensemble | 0.9923 | 0.8362 | 0.0335 | 4.03 |
| 7 | Logistic Regression (C=1.0, Unweighted) | Linear | 0.9903 | 0.8162 | 0.0147 | 2.93 |
| 8 | Decision Tree (Depth=10) | Single Tree | 0.9829 | 0.8021 | 0.0319 | 1.22 |
| 9 | Logistic Regression (C=1.0, Balanced) | Linear | 0.9906 | 0.7956 | 0.0370 | 5.16 |
| 10 | SGD Classifier (ElasticNet) | Linear / Sparse | 0.9887 | 0.7938 | 0.0159 | 1.74 |
| 11 | Calibrated Linear SVM | Max-Margin | 0.9906 | 0.7934 | 0.0150 | 3.89 |
| 12 | Logistic Regression (C=0.1, Balanced) | Linear | 0.9899 | 0.7848 | 0.0388 | 3.71 |
| 13 | Gaussian Naive Bayes | Probabilistic | 0.9674 | 0.4604 | 0.1110 | 0.10 |
| 14 | Dummy Baseline | Baseline | 0.5000 | 0.0414 | 0.0396 | 0.00 |

## Provisional Selection

- Model ID: `random_forest_d15`
- Model: `Random Forest (Depth=15, 100 Trees)`
- Validation PR-AUC: `0.8529`
- Validation ROC-AUC: `0.9931`
- Validation Brier score: `0.0219`
- Validation-selected threshold: `0.8404`

The provisional candidate is evaluated and locked in Step 8. Test results must not
be used to replace it after holdout interpretation.
