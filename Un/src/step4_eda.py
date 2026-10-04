#!/usr/bin/env python3
"""Step 4: EDA, video-quality audit, grade audit, and outlier reporting.

This step is read-only with respect to raw data. It creates tables and figures
from the cleaned non-outcome data and quarantined outcomes. Outcomes are used
only for descriptive post-hoc auditing, never for clustering feature selection.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


CONFIG_PATH = Path("config/project_config.json")

ENROLLMENTS_PATH = Path("data/processed/enrollments_cleaned.parquet")
STUDENTS_PATH = Path("data/processed/students_cleaned.parquet")
RAW_OUTCOMES_PATH = Path("data/quarantine/raw_outcomes.parquet")

FIGURES_DIR = Path("outputs/figures/eda")
TABLES_DIR = Path("outputs/tables")

EDA_SUMMARY_PATH = TABLES_DIR / "eda_summary.csv"
OUTLIER_TABLE_PATH = TABLES_DIR / "outlier_audit.csv"
VIDEO_AUDIT_PATH = TABLES_DIR / "video_quality_audit_by_course.csv"
GRADE_AUDIT_PATH = TABLES_DIR / "grade_outcome_audit.csv"
CLASS_BALANCE_PATH = TABLES_DIR / "outcome_class_balance_posthoc.csv"


plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Thonburi",
    "Sukhumvit Set",
    "Arial Unicode MS",
    "DejaVu Sans"
]
plt.rcParams["axes.unicode_minus"] = False


BEHAVIOR_LABELS = {
    "mean_course_events_percentile": (
        "Event Activity Percentile",
        "เปอร์เซ็นไทล์กิจกรรมทั้งหมด"
    ),
    "mean_course_active_days_percentile": (
        "Active-Day Percentile",
        "เปอร์เซ็นไทล์จำนวนวันที่มีกิจกรรม"
    ),
    "mean_course_chapters_percentile": (
        "Chapter-Access Percentile",
        "เปอร์เซ็นไทล์จำนวนบทเรียนที่เข้าถึง"
    ),
    "mean_course_forum_posts_percentile": (
        "Forum-Post Percentile",
        "เปอร์เซ็นไทล์การโพสต์ใน Forum"
    )
}


def setup_style() -> None:
    """Apply one consistent visual style to all generated EDA figures."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "#FBFDFF",
        "axes.edgecolor": "#D8E2EF",
        "axes.labelcolor": "#26364A",
        "axes.titleweight": "bold",
        "text.color": "#26364A",
        "xtick.color": "#44546A",
        "ytick.color": "#44546A",
        "grid.color": "#E7EDF5"
    })


def iqr_outlier_mask(series: pd.Series) -> pd.Series:
    """Return an outlier mask using the 1.5 × IQR rule on valid values."""
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()

    if valid.empty:
        return pd.Series(False, index=series.index)

    q1 = valid.quantile(0.25)
    q3 = valid.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        return pd.Series(False, index=series.index)

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return numeric.lt(lower) | numeric.gt(upper)


def add_value_labels(ax, bars) -> None:
    """Show readable values above bars."""
    for bar in bars:
        value = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )


def main() -> None:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing configuration: {CONFIG_PATH}")

    for required_path in [
        ENROLLMENTS_PATH,
        STUDENTS_PATH,
        RAW_OUTCOMES_PATH
    ]:
        if not required_path.exists():
            raise FileNotFoundError(
                f"Missing required input: {required_path}. Run previous steps first."
            )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    behavior_features = config["behavior_features"]

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    setup_style()

    print("=" * 72)
    print("STEP 4: EDA, VIDEO QUALITY, GRADE AUDIT, AND OUTLIER ANALYSIS")
    print("=" * 72)

    enrollments = pd.read_parquet(ENROLLMENTS_PATH)
    students = pd.read_parquet(STUDENTS_PATH)
    outcomes = pd.read_parquet(RAW_OUTCOMES_PATH)

    required_behavior_columns = [
        column for column in behavior_features
        if column not in students.columns
    ]

    if required_behavior_columns:
        raise ValueError(
            "Student table is missing behavioural features: "
            + ", ".join(required_behavior_columns)
        )

    # ------------------------------------------------------------------
    # 1. Descriptive EDA for the four approved behavioural features
    # ------------------------------------------------------------------
    summary_rows = []

    for feature in behavior_features:
        values = pd.to_numeric(students[feature], errors="coerce")
        outlier_mask = iqr_outlier_mask(values)

        summary_rows.append({
            "feature": feature,
            "role": "behavioral_feature_for_clustering",
            "student_count": int(len(students)),
            "non_missing_count": int(values.notna().sum()),
            "missing_count": int(values.isna().sum()),
            "missing_pct": float(values.isna().mean() * 100),
            "mean": float(values.mean()),
            "std": float(values.std()),
            "min": float(values.min()),
            "p25": float(values.quantile(0.25)),
            "median": float(values.median()),
            "p75": float(values.quantile(0.75)),
            "max": float(values.max()),
            "skewness": float(values.skew()),
            "iqr_outlier_count": int(outlier_mask.sum()),
            "iqr_outlier_pct": float(outlier_mask.mean() * 100)
        })

    eda_summary = pd.DataFrame(summary_rows)
    eda_summary.to_csv(EDA_SUMMARY_PATH, index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------------
    # 2. Behaviour percentile distributions
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), facecolor="white")

    for axis, feature in zip(axes.ravel(), behavior_features):
        values = pd.to_numeric(students[feature], errors="coerce").dropna()
        english_label, thai_label = BEHAVIOR_LABELS.get(
            feature,
            (feature, feature)
        )

        sns.histplot(
            values,
            bins=30,
            kde=True,
            color="#2563EB",
            edgecolor="white",
            linewidth=0.4,
            ax=axis
        )

        axis.set_title(f"{thai_label}\n{english_label}")
        axis.set_xlabel("Percentile within course (0–1)")
        axis.set_ylabel("Student count")
        axis.set_xlim(0, 1)

    fig.suptitle(
        "Distribution of the Four Behavioural Features Used for Clustering",
        fontsize=15,
        fontweight="bold"
    )
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(
        FIGURES_DIR / "behavioral_feature_distributions.png",
        dpi=200,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 3. Correlation of the four final model features
    # This chart makes redundancy and sparse behaviour visible before K-Means.
    # ------------------------------------------------------------------
    correlation = students[behavior_features].corr(method="spearman")
    fig, axis = plt.subplots(figsize=(9, 7), facecolor="white")
    sns.heatmap(
        correlation,
        annot=True,
        fmt=".3f",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=.6,
        linecolor="white",
        cbar_kws={"label": "Spearman correlation"},
        ax=axis
    )
    axis.set_title(
        "Correlation Between the Four Behavioural Features\n"
        "Spearman correlation after student-level aggregation",
        fontsize=14,
        fontweight="bold"
    )
    plt.tight_layout()
    fig.savefig(
        FIGURES_DIR / "behavior_feature_correlation.png",
        dpi=220,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 3b. Full EDA correlation: all available numeric non-outcome fields.
    # This is deliberately broader than the locked four-feature model matrix.
    # Identifiers and quarantined outcomes are excluded.
    # ------------------------------------------------------------------
    full_eda_columns = [
        "nevents_clean", "ndays_act_clean", "nplay_video_clean",
        "nchapters_clean", "nforum_posts_clean", "age_clean",
        "activity_span_days"
    ]
    available_full_eda = [
        column for column in full_eda_columns if column in enrollments.columns
    ]
    full_corr = enrollments[available_full_eda].apply(
        pd.to_numeric, errors="coerce"
    ).corr(method="spearman")
    full_corr.to_csv(
        TABLES_DIR / "full_eda_numeric_correlation.csv",
        encoding="utf-8-sig"
    )
    fig, axis = plt.subplots(figsize=(11, 9), facecolor="white")
    sns.heatmap(
        full_corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1,
        vmax=1, center=0, square=True, linewidths=.5, linecolor="white",
        cbar_kws={"label": "Spearman correlation"}, ax=axis
    )
    axis.set_title(
        "Full Exploratory Correlation Audit\n"
        "All numeric non-outcome variables; not the final model feature set",
        fontsize=14, fontweight="bold"
    )
    plt.tight_layout()
    fig.savefig(
        FIGURES_DIR / "full_eda_numeric_correlation.png",
        dpi=220, bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 3. Activity and outlier audit at enrollment level
    # ------------------------------------------------------------------
    enrollment_activity_columns = {
        "nevents_clean": "Total Events",
        "ndays_act_clean": "Active Days",
        "nchapters_clean": "Chapters Accessed",
        "nplay_video_clean": "Video Plays",
        "nforum_posts_clean": "Forum Posts"
    }

    outlier_rows = []

    for column, label in enrollment_activity_columns.items():
        values = pd.to_numeric(enrollments[column], errors="coerce")
        outlier_mask = iqr_outlier_mask(values)
        valid = values.dropna()

        outlier_rows.append({
            "column": column,
            "display_name": label,
            "record_count": int(len(enrollments)),
            "missing_count": int(values.isna().sum()),
            "zero_count": int(values.eq(0).sum()),
            "q1": float(valid.quantile(0.25)) if not valid.empty else None,
            "median": float(valid.quantile(0.50)) if not valid.empty else None,
            "q3": float(valid.quantile(0.75)) if not valid.empty else None,
            "p95": float(valid.quantile(0.95)) if not valid.empty else None,
            "p99": float(valid.quantile(0.99)) if not valid.empty else None,
            "max": float(valid.max()) if not valid.empty else None,
            "iqr_outlier_count": int(outlier_mask.sum()),
            "iqr_outlier_pct": float(outlier_mask.mean() * 100),
            "action": (
                "Retain as observed value; use log-scale for visualisation "
                "and robust preprocessing where required."
            )
        })

    outlier_table = pd.DataFrame(outlier_rows)
    outlier_table.to_csv(
        OUTLIER_TABLE_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    fig, axes = plt.subplots(2, 3, figsize=(17, 9), facecolor="white")

    for axis, (column, label) in zip(
        axes.ravel(),
        enrollment_activity_columns.items()
    ):
        values = pd.to_numeric(enrollments[column], errors="coerce").dropna()

        sns.boxplot(
            x=np.log1p(values),
            color="#A855F7",
            fliersize=1.5,
            linewidth=1,
            ax=axis
        )

        axis.set_title(f"{label}: Outlier Inspection")
        axis.set_xlabel(f"log1p({label})")

    for axis in axes.ravel()[len(enrollment_activity_columns):]:
        axis.axis("off")

    fig.suptitle(
        "Enrollment Activity Outliers: Retained and Documented",
        fontsize=15,
        fontweight="bold"
    )
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(
        FIGURES_DIR / "activity_outlier_inspection.png",
        dpi=200,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 5. Zero and missingness audit for the four raw behavioural signals.
    # Video is intentionally excluded because it is audit-only.
    # ------------------------------------------------------------------
    model_signal_columns = {
        "nevents_clean": "Events",
        "ndays_act_clean": "Active days",
        "nchapters_clean": "Chapters",
        "nforum_posts_clean": "Forum posts"
    }
    sparsity_rows = []
    for column, label in model_signal_columns.items():
        values = pd.to_numeric(enrollments[column], errors="coerce")
        sparsity_rows.append({
            "signal": label,
            "zero_pct": float(values.eq(0).mean() * 100),
            "missing_pct": float(values.isna().mean() * 100),
            "nonzero_pct": float(values.gt(0).mean() * 100)
        })

    sparsity = pd.DataFrame(sparsity_rows)
    fig, axis = plt.subplots(figsize=(11, 6), facecolor="white")
    axis.bar(sparsity["signal"], sparsity["zero_pct"], color="#F97316", label="Zero")
    axis.bar(
        sparsity["signal"],
        sparsity["missing_pct"],
        bottom=sparsity["zero_pct"],
        color="#94A3B8",
        label="Missing"
    )
    axis.bar(
        sparsity["signal"],
        sparsity["nonzero_pct"],
        bottom=sparsity["zero_pct"] + sparsity["missing_pct"],
        color="#10B981",
        label="Observed non-zero"
    )
    axis.set_ylim(0, 100)
    axis.set_ylabel("Enrollment records (%)")
    axis.set_title(
        "Sparsity of the Four Behavioural Signals\n"
        "Important for interpreting K-Means segments",
        fontsize=14,
        fontweight="bold"
    )
    axis.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, -0.12))
    plt.tight_layout()
    fig.savefig(
        FIGURES_DIR / "behavioral_signal_sparsity.png",
        dpi=220,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 6. Video-data quality audit
    # The source has no video-duration field. Analyse play counts only.
    # ------------------------------------------------------------------
    video_by_course = (
        enrollments.groupby("course_id_clean", dropna=False)
        .agg(
            enrollment_records=("userid_DI", "size"),
            missing_video_records=("video_missing_flag", "sum"),
            median_video_plays=("nplay_video_clean", "median"),
            mean_video_plays=("nplay_video_clean", "mean"),
            p95_video_plays=(
                "nplay_video_clean",
                lambda series: pd.to_numeric(
                    series,
                    errors="coerce"
                ).quantile(0.95)
            ),
            max_video_plays=("nplay_video_clean", "max")
        )
        .reset_index()
        .rename(columns={"course_id_clean": "course_id"})
    )

    video_by_course["missing_video_pct"] = (
        video_by_course["missing_video_records"]
        / video_by_course["enrollment_records"].clip(lower=1)
        * 100
    )

    video_by_course = video_by_course.sort_values(
        "missing_video_pct",
        ascending=False
    )

    video_by_course.to_csv(
        VIDEO_AUDIT_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor="white")

    video_plot = video_by_course.sort_values(
        "missing_video_pct",
        ascending=True
    )

    bars = axes[0].barh(
        video_plot["course_id"],
        video_plot["missing_video_pct"],
        color="#F97316"
    )

    axes[0].set_title("Missing Video-Play Data by Course")
    axes[0].set_xlabel("Missing video-play records (%)")
    axes[0].set_ylabel("Course")

    for bar, value in zip(bars, video_plot["missing_video_pct"]):
        axes[0].text(
            value + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center",
            fontsize=8
        )

    video_values = pd.to_numeric(
        enrollments["nplay_video_clean"],
        errors="coerce"
    ).dropna()

    sns.histplot(
        np.log1p(video_values),
        bins=45,
        kde=True,
        color="#06B6D4",
        edgecolor="white",
        linewidth=0.3,
        ax=axes[1]
    )

    axes[1].set_title("Distribution of Video Plays")
    axes[1].set_xlabel("log1p(video plays)")
    axes[1].set_ylabel("Enrollment records")

    fig.suptitle(
        "Video Play Counts and Video-Data Availability\n"
        "The dataset does not include video duration.",
        fontsize=15,
        fontweight="bold"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(
        FIGURES_DIR / "video_quality_and_distribution.png",
        dpi=200,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 7. Post-hoc outcome and grade audit
    # Outcomes are merged only for audit outputs, never clustering inputs.
    # ------------------------------------------------------------------
    outcomes = outcomes.rename(columns={"Unnamed: 0": "source_row_id"}).copy()

    enrollments_for_audit = enrollments.copy()
    enrollments_for_audit["source_row_id"] = (
        enrollments_for_audit["source_row_id"].astype("string")
    )
    outcomes["source_row_id"] = outcomes["source_row_id"].astype("string")

    audit_columns = [
        "source_row_id",
        "certified",
        "grade",
        "viewed",
        "explored",
        "incomplete_flag"
    ]

    posthoc = enrollments_for_audit.merge(
        outcomes[audit_columns],
        on="source_row_id",
        how="left",
        validate="one_to_one"
    )

    posthoc["certified"] = pd.to_numeric(
        posthoc["certified"],
        errors="coerce"
    )

    posthoc["grade_numeric"] = pd.to_numeric(
        posthoc["grade"],
        errors="coerce"
    )

    posthoc["grade_missing_flag"] = (
        posthoc["grade_numeric"].isna()
    ).astype("int8")

    posthoc["grade_out_of_range_flag"] = (
        posthoc["grade_numeric"].lt(0)
        | posthoc["grade_numeric"].gt(1)
    ).astype("int8")

    posthoc["certified_grade_zero_flag"] = (
        posthoc["certified"].eq(1)
        & posthoc["grade_numeric"].eq(0)
    ).astype("int8")

    posthoc["certified_grade_missing_flag"] = (
        posthoc["certified"].eq(1)
        & posthoc["grade_numeric"].isna()
    ).astype("int8")

    grade_audit = (
        posthoc[
            [
                "source_row_id",
                "userid_DI",
                "course_id_clean",
                "institute_clean",
                "year_clean",
                "semester_clean",
                "certified",
                "grade_numeric",
                "grade_missing_flag",
                "grade_out_of_range_flag",
                "certified_grade_zero_flag",
                "certified_grade_missing_flag"
            ]
        ]
        .copy()
    )

    grade_audit["requires_outcome_review"] = (
        grade_audit[
            [
                "grade_out_of_range_flag",
                "certified_grade_zero_flag",
                "certified_grade_missing_flag"
            ]
        ]
        .any(axis=1)
    )

    grade_audit.to_csv(
        GRADE_AUDIT_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    class_balance = (
        posthoc["certified"]
        .value_counts(dropna=False)
        .rename_axis("certified")
        .reset_index(name="record_count")
    )

    class_balance["label"] = class_balance["certified"].map({
        0.0: "Not certified",
        1.0: "Certified"
    }).fillna("Missing or invalid")

    class_balance["percentage"] = (
        class_balance["record_count"]
        / class_balance["record_count"].sum()
        * 100
    )

    class_balance.to_csv(
        CLASS_BALANCE_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    grade_counts = (
        posthoc["grade_numeric"]
        .dropna()
        .round(3)
        .value_counts()
        .sort_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), facecolor="white")

    sns.histplot(
        data=posthoc,
        x="grade_numeric",
        hue="certified",
        bins=30,
        multiple="stack",
        palette={0.0: "#94A3B8", 1.0: "#10B981"},
        ax=axes[0]
    )

    axes[0].axvline(
        0,
        color="#EF4444",
        linestyle="--",
        linewidth=2,
        label="Grade = 0"
    )

    axes[0].set_title("Grade Distribution by Certification Status")
    axes[0].set_xlabel("Observed grade")
    axes[0].set_ylabel("Enrollment records")
    axes[0].legend(title="Certified")

    flag_counts = pd.Series({
        "Certified with grade = 0": int(
            posthoc["certified_grade_zero_flag"].sum()
        ),
        "Certified with missing grade": int(
            posthoc["certified_grade_missing_flag"].sum()
        ),
        "Grade outside 0–1": int(
            posthoc["grade_out_of_range_flag"].sum()
        )
    })

    bars = axes[1].bar(
        flag_counts.index,
        flag_counts.values,
        color=["#EF4444", "#F59E0B", "#8B5CF6"]
    )

    axes[1].set_title("Outcome Quality Flags")
    axes[1].set_ylabel("Record count")
    axes[1].tick_params(axis="x", rotation=18)
    add_value_labels(axes[1], bars)

    fig.suptitle(
        "Post-hoc Grade and Certification Audit\n"
        "Flags are reported; raw records are not silently removed.",
        fontsize=15,
        fontweight="bold"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(
        FIGURES_DIR / "grade_and_outcome_quality_audit.png",
        dpi=200,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 8. Outcome class-balance chart for explanation only
    # ------------------------------------------------------------------
    fig, axis = plt.subplots(figsize=(8, 5), facecolor="white")

    bars = axis.bar(
        class_balance["label"],
        class_balance["percentage"],
        color=["#64748B", "#10B981", "#F59E0B"][:len(class_balance)]
    )

    for bar, count, percentage in zip(
        bars,
        class_balance["record_count"],
        class_balance["percentage"]
    ):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            percentage,
            f"{count:,}\n{percentage:.2f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )

    axis.set_title(
        "Post-hoc Certification Class Balance\n"
        "Not used in unsupervised clustering"
    )
    axis.set_ylabel("Enrollment records (%)")
    axis.set_ylim(0, max(class_balance["percentage"]) * 1.18)

    plt.tight_layout()
    fig.savefig(
        FIGURES_DIR / "posthoc_certification_class_balance.png",
        dpi=200,
        bbox_inches="tight"
    )
    plt.close(fig)

    print(f"[Step 4] EDA summary: {EDA_SUMMARY_PATH}")
    print(f"[Step 4] Outlier audit: {OUTLIER_TABLE_PATH}")
    print(f"[Step 4] Video audit: {VIDEO_AUDIT_PATH}")
    print(f"[Step 4] Grade audit: {GRADE_AUDIT_PATH}")
    print(f"[Step 4] Figures saved to: {FIGURES_DIR}")
    print(
        "[Step 4] Outcomes were used only for post-hoc audit; "
        "they were not added to clustering features."
    )


if __name__ == "__main__":
    main()
