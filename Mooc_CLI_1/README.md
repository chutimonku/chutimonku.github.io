# MOOC Data Science Workflow

This project implements the current `Workflow.md` as an end-to-end, reproducible analysis of a supplied HarvardX/MITx-derived person-course dataset. It has two scientifically distinct branches:

1. grouped classification of course certification (`certified`) at the enrollment level; and
2. outcome-free behavioral clustering at the unique-student level.

The supervised branch excludes `grade`, `explored`, and `incomplete_flag`. The clustering branch excludes every known outcome, including `certified`. Grouped train/validation/test splits keep every `userid_DI` in exactly one split. Learned preprocessing is fitted on training data only, model choice uses validation data only, and the selected models are evaluated once on the untouched test split.

Run everything from the repository root:

```bash
python run_project.py
```

The main report is `reports/mooc_data_science_report.html`. Machine-readable evidence is under `outputs/`, fitted artifacts under `models/final/`, and the complete verification result is `outputs/reproducibility/artifact_check.json`.

The original file under `data/raw/` is read-only by convention. Its SHA-256 is recorded before and after every complete run.
