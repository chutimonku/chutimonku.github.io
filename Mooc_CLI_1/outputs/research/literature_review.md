# Literature review and method rationale

## Dataset and context

- HarvardX (2014), *HarvardX Person-Course Academic Year 2013 De-Identified dataset, version 3.0*, Harvard Dataverse, DOI: [10.7910/DVN/26147](https://doi.org/10.7910/DVN/26147). The repository documentation states that each aggregate record represents one individual's activity in one edX course and supplies custom terms that prohibit re-identification.
- Ho, A. et al. (2014), *HarvardX and MITx: The First Year of Open Online Courses*, SSRN: [2381263](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2381263). This report documents the first-year MOOC context and cautions against treating registration as equivalent to sustained participation.

## Classification evidence

- Moreno-Marcos, P. M. et al. (2019), *Prediction in MOOCs: A Review and Future Research Directions*, IEEE Transactions on Learning Technologies, DOI: [10.1109/TLT.2018.2856808](https://doi.org/10.1109/TLT.2018.2856808). The review identifies behavioral, demographic, and course-context features and reports common use of regression and support-vector approaches, while emphasizing generalization limitations.
- Dalipi, F., Imran, A. S., and Kastrati, Z. (2018), *MOOC Dropout Prediction Using Machine Learning Techniques: Review and Research Challenges*, DOI: [10.1109/EDUCON.2018.8363340](https://doi.org/10.1109/EDUCON.2018.8363340). The paper highlights inconsistent outcome definitions and evaluation protocols as obstacles to comparisons.
- Gardner, J. and Brooks, C. (2018), *Student Success Prediction in MOOCs*, arXiv: [1711.06349](https://arxiv.org/abs/1711.06349). The review calls for clearer links between predictors, outcomes, temporal framing, and explanatory claims.

These sources support comparing interpretable linear and tree-based classifiers, using metrics robust to imbalance (PR-AUC, balanced accuracy, per-class recall/F1), and explicitly restricting this dataset's full-course engagement features to retrospective classification rather than claiming early-warning capability.

## Clustering evidence

The data contain strongly skewed, zero-inflated behavioral counts. Five genuinely different clustering families are therefore compared: centroid-based K-means, probabilistic Gaussian mixtures, hierarchical agglomeration, CF-tree BIRCH, and density-based DBSCAN. Log transformations and robust scaling are fitted only on the training split. PCA is used for visualization, not as evidence that the plotted axes are causal constructs.

## Research gap and limits

The supplied local CSV is a derivative whose row and column counts do not exactly match the current canonical Dataverse release. It is therefore described as a local derivative and identified by its own checksum rather than falsely equated with the canonical file. Full-course aggregates also prevent prospective early-intervention claims. Results are dataset-specific, observational, and not causal.
