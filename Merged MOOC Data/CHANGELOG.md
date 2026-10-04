# Changelog

## Version 3.1.0 — Expanded EDA, Segment Comparison, and Corrected LLM Gate

- Expanded student-level EDA with full numerical distribution galleries, robust boxplots, zero/missing/outlier profiles, behavioral hexbin relationships, and downloadable diagnostic tables.
- Added four cross-segment comparisons for All Students, High Engagement, Low Engagement, and Certified Only: mean features, feature distributions, cluster composition, and observed-versus-predicted outcomes.
- Embedded reusable EDA and segment-comparison sections across Overview, Traditional Unsupervised, Deep Learning, Supervised Learning, and LLM readiness views.
- Added a sixth `Results Summary` dashboard view after LLM with track winners, limitations, recommendations, and integrated segment evidence.
- Corrected the LLM track: video interaction counts remain tabular behavior and are no longer converted into pseudo-transcripts or sentence embeddings.
- Enforced the required content pipeline: governed media/captions → audio/language/speech processing → ASR words with timestamps → cleaned sentences → transcript quality gate → LLM/NLP.
- Marked GPT, DistilBERT, BGE, and Gemini content methods as blocked until real sentence-level transcript input exists; no model metric is fabricated.
- Updated automated checks; all 16 active tests and 62 required artifacts pass.

## Version 3.0.0 — Audited Multi-Track Workflow

- Reconciled two source files: 755,144 raw rows → 609,637 deduplicated enrollments → 446,766 students.
- Added complete source inventory, every-column profile/value counts, per-column missing decisions, course-offering profile, outcome-consistency audit, class-balance audit, and processing log.
- Changed reversed valid date pairs from deletion/forced zero to documented swapping with original values and a repair flag.
- Preserved missing demographics as `Unknown`; retained invalid ages as missing for pipeline imputation.
- Added data-selected within-course behavioral percentiles for Traditional/Deep clustering; the current run selected four non-outcome behavioral features after clean merge.
- Replaced the obsolete sentence-embedding experiment with active Traditional Unsupervised, Deep Learning, Supervised Learning, and Generative LLM-supported communication tracks.
- Evaluated Traditional methods across `k=2–10`; the observed elbow was `k=4`, and the selected model was MiniBatch K-Means with three clusters.
- Added Autoencoder 4→3 representation and supervised certification prediction using 34 source features transformed to 75 columns in the current run.
- Added a grounded LLM communication artifact, `outputs/tables/llm_generated_summaries.csv`, built from computed cluster profiles and supervised-model manifests with no fabricated model metric.
- Added test-set Accuracy, Balanced Accuracy, Precision, Recall, F1, PR-AUC, ROC-AUC, Brier score, threshold, training runtime, deployment runtime, and throughput.
- Rebuilt the dashboard with five large track views, Thai/English switching, collapsible sidebar, responsive layout, data downloads, dynamic segments, full tables, plots, citations, and 11-step status.
- Added active deployment contracts/model cards and an honest monitoring baseline with no fabricated future cohort.
- Replaced the master runner so it executes only active modules and verifies 48 required artifacts plus data/model/dashboard/LLM tests.

## Version 2.x — Archived Legacy Experiments

- Earlier iterations established multi-source integration, quarantine, and the first dashboard.
- Their obsolete model code and artifacts are retained under `archive/obsolete_sentence_embedding/` for audit history and are not executed by `run_project.py`.
