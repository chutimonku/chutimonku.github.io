# Project Revision Log

## Scope

The existing project structure and raw dataset were retained. Pipeline code and generated artifacts were revised to match agy_workflow.md; no synthetic records, model scores, clusters, or conclusions were introduced.

## Changes

1. Added executable problem-definition output and workflow-wide run verification.
2. Added source checksum, observed dimensions, unique-student count, data dictionary, and provenance files.
3. Removed pre-lock outcome summaries from the quarantine manifest.
4. Preserved nplay_video=197757 as missing with an availability indicator instead of treating it as zero.
5. Preserved missing age and invalid date uncertainty instead of unsupported imputation.
6. Added cleaning rules and a record-to-student aggregation audit confirming no student loss.
7. Replaced mandatory 50,000-row sampling with full-population EDA; model metric sampling is separately calculated from a documented memory budget.
8. Added full EDA tables, feature screening, and revised figures.
9. Reduced redundant clustering features; demographics are excluded and video is a sensitivity feature set because of substantial missingness.
10. Added a literature review and six distinct clustering families. MiniBatch K-Means is explicitly treated as a K-Means scalability variant.
11. Replaced fixed k=2..8 selection with a data-derived shortlist and multi-metric, resample-stability ranking.
12. Added complete tuning, runtime, failure, optimization, sensitivity, ablation, fairness, ambiguity, and permutation-assignment-importance outputs.
13. Removed hard-coded final K-Means selection. Step 8 reads the provisional result, refits on the full population, writes a model checksum, and only then opens outcomes.
14. Kept cluster assignments physically separate from post-hoc outcomes.
15. Replaced hard-coded personas and interventions with neutral, data-derived cluster descriptors.
16. Moved deployment classes into stable importable modules; the saved pipeline now loads in a fresh Python process.
17. Added schema validation, outcome rejection, batch inference, model card, exact environment versions, examples, and deployment tests.
18. Rebuilt the HTML dashboard from saved artifacts with all required sections and an interactive explorer using the locked preprocessing and centroids.
19. Replaced simulated production drift and universal PSI thresholds with a truthful baseline-only status until a genuine later cohort is supplied.
20. Added run logs, a run manifest, a report manifest, and verification of every required artifact and executable source file.
21. Expanded final verification from 38 core files to file-and-group requirements covering quarantine data, feature comparisons, trained candidate models, figures, inference code, tests, and examples.
22. Corrected neutral cluster-description logic so a feature below the population mean is not described as “higher”; relative feature columns were renamed to avoid implying a positive direction.
23. Added `PRESENTATION_GUIDE_TH.md` with the workflow adaptation, prompt history, before-and-after changes, analytical methods, verified findings, limitations, slide outline, and likely questions.
24. Made `config/project_config.json` the executable source for the raw path, source URL, expected raw schema, unit identifier, and outcome quarantine list.
25. Strengthened deployment validation for dtypes, missing values, ranges, non-finite values, duplicate student rows, and raw-input dates; event intensity is now derived inside the pipeline.
26. Expanded monitoring to calculate schema change, assignment uncertainty, empirical outlier rate, and refit stability while retaining human review for uncalibrated retraining decisions.
27. Expanded the pre-lock review to record cluster-size, runtime, ambiguity, ablation, interpretability, and preprocessing-sensitivity evidence before outcomes are opened.
28. Removed unused duplicate summaries, the obsolete radar figure, a redundant Step 10 wrapper, bytecode caches, and legacy outputs from the active project.
29. Improved dashboard typography, spacing, table readability, cluster-card layout, and full-width analytical figures without changing calculated findings.
30. Added narrow generated-output cleanup so candidate models and future-cohort comparisons from an earlier run cannot be mistaken for current-run artifacts.

## Replaced Outputs

Obsolete generated outputs were removed from the active project and moved to the macOS Trash so they remain recoverable without being confused with current evidence.

## Verified Final Run

- Raw records: 416,921
- Raw columns: 22
- Unique students: 335,650
- Candidate configurations completed: 29
- Distinct clustering families: 6
- Selected model from internal evidence: K-Means with 4 clusters
- Final-fit population: 335,650 students
- Artifact requirements verified: 75 of 75
- Deployment tests: 10 of 10 passed
- Monitoring status: baseline only; no future cohort or drift result was fabricated
