# Educational Data Mining & MOOC Dropout Prediction: Literature Review

## 1. Context and Problem Significance

Massive Open Online Courses (MOOCs) have democratized access to higher education worldwide, enrolling millions of diverse learners. However, low course completion rates—typically ranging between 2% and 8%—represent a persistent operational and pedagogical challenge (Kizilcec et al., 2013; Reich, 2020). Rather than treating all non-completers homogeneously as "failures", modern learning analytics distinguishes between disengaged dropouts, auditing learners who explore content without certification goals, and certificate-seeking completers (Anderson et al., 2014).

Building supervised machine learning models to predict completion status and segment students into calibrated risk tiers enables academic support teams to intervene proactively. Effective early warning systems direct institutional resources toward learners who need nudges, prerequisite remediation, or technical support (Gardner & Brooks, 2018).

---

## 2. Key Empirical Findings in MOOC Learner Modeling

### 2.1 Behavioral vs. Demographic Predictors
A consistent finding across the educational data mining (EDM) literature is that **fine-grained behavioral and engagement metrics drastically outperform demographic features** in predicting student outcomes:
- **Active Days and Interaction Regularity:** The number of distinct active days (`ndays_act`) and temporal event span consistently serve as the strongest single predictors of course persistence (Anderson et al., 2014; Halawa et al., 2014).
- **Curriculum Breadth vs. Intensity:** Accessing multiple chapters (`nchapters`) reflects curricular commitment. Students who progress beyond the introductory chapters exhibit significantly higher certification propensities (Fei & Yeung, 2015).
- **Social Interaction:** Active participation in discussion forums (`nforum_posts`), although exhibited by only a small fraction of students (<5%), is strongly correlated with completion (Coetzee et al., 2014).
- **Demographic Disparities:** While students with advanced degrees (Master's, Doctorate) complete at higher rates than secondary school students, conditioning on engagement reduces demographic gaps, highlighting the danger of relying heavily on demographic features for automated decisions (Reich, 2014).

### 2.2 Severe Class Imbalance
The primary analytical challenge in MOOC completion modeling is extreme class imbalance (typically 95% negative, 5% positive). Conventional accuracy is completely misleading (e.g., a dummy classifier predicting all non-completion achieves ~96% accuracy). Consequently, EDM researchers mandate evaluation using:
1. **Area Under the ROC Curve (ROC-AUC)**: Measures ranking and discrimination independent of threshold.
2. **Area Under the Precision-Recall Curve (PR-AUC / Average Precision)**: Highly sensitive to the positive minority class, providing an honest measure of precision at operational recall levels (Saito & Rehmsmeier, 2015).
3. **Brier Score & Probability Calibration**: For actionable risk tiering, predicted probabilities must reflect empirical frequencies rather than uncalibrated confidence scores (Niculescu-Mizil & Caruana, 2005).

---

## 3. Methodological Landscape: Supervised Classification in EDM

| Algorithm Family | EDM Precedents | Key Strengths | Critical Limitations |
| :--- | :--- | :--- | :--- |
| **Logistic Regression (L2 / ElasticNet)** | Brooks et al. (2015); Gardner et al. (2018) | Transparent odds ratios; well-calibrated probabilities; fast computation | Cannot capture complex multi-way non-linear feature interactions |
| **Gaussian Naive Bayes** | Xing et al. (2016); Patel & Amin (2024) | Very fast probabilistic baseline; useful contrast to discriminative models | Conditional-independence and Gaussian assumptions can be restrictive |
| **Support Vector Machine (calibrated linear SVM)** | Zhang et al. (2023); Whitehill et al. (2017) | Scalable maximum-margin boundary; class weighting supports minority detection | Raw margins are not probabilities, so calibration is required for risk tiers |
| **Decision Tree** | Chen et al. (2019) | Transparent non-linear rules and interactions | A single tree can be unstable and overfit without depth/leaf constraints |
| **Tree Ensembles (Random Forest)** | Halawa et al. (2014); Xing et al. (2016) | Invariant to monotonic scaling; models non-linear interactions; robust to outliers | Slower prediction; memory-intensive on large student cohorts |
| **Extremely Randomized Trees (Extra Trees)** | Geurts et al. (2006); Patel & Amin (2024) | Extra split randomization reduces correlation among trees and offers a distinct ensemble assumption | Less directly interpretable than one tree; probabilities may require scrutiny |
| **Gradient Boosted Decision Trees (GBDT)** | Dalipi et al. (2018); Chen et al. (2019) | SOTA tabular performance; native handling of missingness; effective class re-weighting | Susceptible to over-fitting if depth/learning rate un-tuned |
| **Multi-Layer Perceptron (MLP)** | Fei & Yeung (2015); Whitehill et al. (2017) | Discovers latent non-linear representations | Requires careful scaling; opaque decision boundaries; longer training |

---

## 4. Governance & Anti-Leakage Imperatives

A prominent failure mode in educational machine learning is target data leakage (Salganik et al., 2020). When variables derived from post-course records—such as final grades, assignment completion flags, or cumulative certificates—are inadvertently included as input features, models exhibit artificially inflated validation performance that collapses upon deployment.

To establish defensible validity, our workflow enforces:
1. **Physical Isolation:** Complete separation of target outcomes (`certified`, `grade`, `incomplete_flag`, `explored`) from input features.
2. **Split-Fitted Preprocessing:** All transformations (imputation, scaling, encoding) fitted strictly on training partitions ($X_{train}$) to eliminate data snooping.
3. **Fairness Audits:** Explicit audits of true positive rate (TPR) parity across demographic subgroups.

---

## 5. References

1. Anderson, A., Huttenlocher, D., Kleinberg, J., & Leskovec, J. (2014). Engaging with massive online courses. *Proceedings of the 23rd International Conference on World Wide Web (WWW)*, 687–698.
2. Brooks, C., Erickson, G., Greer, J., & Gutwin, C. (2015). Modelling student significance using time-series analysis. *Educational Data Mining 2015*, 234–241.
3. Dalipi, F., Imran, A. S., & Kastrati, Z. (2018). MOOC dropout prediction using machine learning techniques: Review and research challenges. *IEEE Global Engineering Education Conference (EDUCON)*, 1007–1014.
4. Fei, M., & Yeung, D. Y. (2015). Temporal models for predicting student dropout in massive open online courses. *IEEE International Conference on Data Mining Workshop (ICDMW)*, 256–263.
5. Gardner, J., & Brooks, C. (2018). Student success prediction in MOOCs. *User Modeling and User-Adapted Interaction*, 28(2), 127–144.
6. Halawa, S., Greene, D., & Mitchell, J. (2014). Dropout prediction to serve increasing enrollment in MOOCs. *eLearning Papers*, 38(1), 1–11.
7. Kizilcec, R. F., Piech, C., & Schneider, E. (2013). Deconstructing disengagement: Analyzing learner subpopulations in massive open online courses. *Proceedings of the 3rd International Conference on Learning Analytics and Knowledge (LAK)*, 170–179.
8. Niculescu-Mizil, A., & Caruana, R. (2005). Predicting good probabilities with supervised learning. *Proceedings of the 22nd International Conference on Machine Learning (ICML)*, 625–632.
9. Reich, J. (2014). MOOC completion and retention: What do the data tell us? *Science*, 344(6184), 606–607.
10. Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. *PLOS ONE*, 10(3), e0118432.
11. Geurts, P., Ernst, D., & Wehenkel, L. (2006). Extremely randomized trees. *Machine Learning*, 63, 3–42. https://doi.org/10.1007/s10994-006-6226-1
12. Chen, W., et al. (2019). MOOC dropout prediction using a hybrid algorithm based on decision tree and extreme learning machine. *Mathematical Problems in Engineering*, 2019, 8404653. https://doi.org/10.1155/2019/8404653
13. Zhang, Y., Ang, L. W., Shi, S., & Palaniappan, S. (2023). Dropout prediction model for college students in MOOCs based on weighted multi-feature and SVM. *Journal of Informatics and Web Engineering*, 2(2). https://doi.org/10.33093/jiwe.2023.2.2.3
14. Patel, K. K., & Amin, K. (2024). Predictive modeling of dropout in MOOCs using machine learning techniques. *International Journal of Intelligent Systems and Applications in Engineering*.
