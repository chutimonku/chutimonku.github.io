# MOOC Project Cleanup Audit — 2026-09-29

## Main finding

The K=3 segmentation should not be used as the final learner persona result because it collapses almost all learners into one cluster. The active K=3 profile file showed:

- Cluster 0: 441,385 learners, 98.80%
- Cluster 1: 3,137 learners, 0.70%
- Cluster 2: 2,244 learners, 0.50%

This is statistically valid as a coarse outlier split, but it is not useful as a balanced persona segmentation for presentation or dashboard reporting.

## Final segmentation decision

The dashboard now uses the K=5 segmentation artifacts because they provide more interpretable and balanced learner personas:

- Cluster 0: 46,296 learners, 13.79%
- Cluster 1: 62,225 learners, 18.54%
- Cluster 2: 55,365 learners, 16.49%
- Cluster 3: 97,719 learners, 29.11%
- Cluster 4: 74,045 learners, 22.06%

Active K=5 files retained in the working tree include:

- outputs/tables/final_k5_cluster_profiles.csv
- outputs/tables/final_k5_selection_metrics.csv
- outputs/tables/final_k5_unsupervised_model_comparison.csv
- outputs/figures/tracks/k5_final/

## Dashboard status

The active dashboard is:

- reports/student_segmentation_report.html

It now references K=5 persona charts and contains a correction note explaining why K=3 was rejected for persona reporting. After cleanup, dashboard local image/data references were checked and no missing referenced files were found.

## Cleanup performed

Old/conflicting K=3 artifacts, backup HTML files, and draft candidate decks were moved, not permanently deleted, to:

- archive/unused_after_k5_cleanup_20260929/

See the generated manifest for the exact file list:

- archive/unused_after_k5_cleanup_20260929/cleanup_manifest.json

## Files not removed

Large dependency/cache folders such as `.offline_deps` and `.dashboard_deps` were not removed because they may be required to run or rebuild the local dashboard environment. Raw and processed data files were also not removed.
