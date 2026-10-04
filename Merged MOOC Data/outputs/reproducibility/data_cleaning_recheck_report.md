# Data Cleaning Recheck Report

## Scope

This recheck audits the current MOOC data layer from the actual project files only. No values were manually invented. Evidence was computed from:

- `data/interim/HXPC13_harmonized.parquet`
- `data/interim/big_student_harmonized.parquet`
- `data/processed/enrollments_cleaned.parquet`
- `data/processed/students_cleaned.parquet`
- `data/quarantine/*.parquet`

## Verified Counts

| Item | Count |
|---|---:|
| Harmonized raw rows from both sources | 755,144 |
| Unique students in harmonized data | 446,766 |
| Current cleaned enrollment rows using `userid_DI + course_id` | 575,060 |
| Enrollment rows if using course-run key `userid_DI + institute + course_id + year + semester` | 624,674 |
| Current cleaned student rows | 446,766 |
| Supervised-eligible outcome rows | 574,982 |
| Quarantined enrollment outcome rows | 575,060 |

## What Looks Correct

1. Student-level unit is consistent: `students_cleaned.parquet` has 446,766 rows and 446,766 unique `userid_DI` values.
2. Outcome columns are not present in `students_cleaned.parquet`.
3. Outcome/target fields are stored separately under `data/quarantine/`.
4. Cleaned enrollment table has no duplicate rows under its current key `userid_DI + course_id`.
5. Date inversion repair is active and the cleaned table has no remaining cases where `clean_last_dt < clean_start_dt`.

## Main Data-Cleaning Issue Found

The current deduplication key is:

```text
userid_DI + course_id
```

This collapses multiple course-run contexts for the same student and course. The audit found:

| Issue | Evidence |
|---|---:|
| Groups collapsed by current key that have multiple course-run contexts | 49,614 |
| Raw rows inside those collapsed groups | 99,228 |
| Course offerings in combined harmonized data | 19 |
| Course offerings remaining in current cleaned data | 16 |
| Course offerings missing from current cleaned data | 3 |

The missing offerings are HarvardX `CS50x` semester-specific rows:

- HarvardX / CS50x / 2012 / Fall
- HarvardX / CS50x / 2012 / Spring
- HarvardX / CS50x / 2012 / Summer

These were collapsed into HarvardX / CS50x / 2012 / Unknown.

## Field Conflicts Inside Collapsed Groups

Among the 49,614 collapsed student-course groups with multiple course-run contexts:

| Field | Groups with conflicting values |
|---|---:|
| grade | 47,466 |
| nevents | 3,121 |
| ndays_act | 2,748 |
| nplay_video | 2,623 |
| nchapters | 2,644 |
| viewed | 877 |
| explored | 471 |
| certified | 147 |
| nforum_posts | 91 |

Because `grade`, behavior counts, and some outcome flags conflict inside collapsed groups, these rows should not be treated as simple duplicates without further justification.

## Conclusion

The current cleaned student unit is internally consistent, but the current enrollment-level cleaning is not fully safe because the deduplication key collapses some distinct course-run contexts.

Recommended correction:

```text
Use course-run key:
userid_DI + institute + course_id + year + semester
```

or explicitly document that the project intentionally uses student-course aggregation and accepts the loss of semester-level course-run information.

For the current dashboard, the important caveat is:

> Student-level rows are consistent, but enrollment/course-run cleaning needs revision or explicit justification before reporting enrollment-level counts and course offering comparisons.

## Evidence Files

- `outputs/tables/data_reclean_key_count_audit.csv`
- `outputs/tables/data_reclean_collapsed_course_run_groups.csv`
- `outputs/tables/data_reclean_collapsed_field_conflicts.csv`
- `outputs/tables/data_reclean_offering_loss_audit.csv`
- `outputs/reproducibility/data_reclean_audit_summary.json`

