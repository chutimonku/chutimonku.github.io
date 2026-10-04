# MOOC Student Behaviour Clustering Model Card

## Purpose

This model segments MOOC learners from four observed behavioural features.
It supports descriptive learner-support planning and does not determine learner
ability, eligibility, or educational value.

## Unit of analysis

One row per `userid_DI`.

## Final algorithm

K-Means with `K = 5`.

## Input features

- `mean_course_events_percentile`
- `mean_course_active_days_percentile`
- `mean_course_chapters_percentile`
- `mean_course_forum_posts_percentile`

## Explicit exclusions

- Profile and demographic fields
- Learner identifiers
- Course identifiers
- Certification status
- Grade
- Viewed status
- Explored status
- Incomplete flag

## K-selection metrics

- Silhouette: 0.4275
- Davies-Bouldin: 0.8827
- Calinski-Harabasz: 16546.02
- Mean Resample ARI: 0.9935
- Smallest cluster: 13.23%

## Limitations

- The source is aggregated person-course data and is not a weekly early-warning dataset.
- Video duration is unavailable. The workflow analyses video-play counts only.
- Clusters describe observed patterns and require contextual interpretation.
- New data must use the same behavioural feature definitions.
