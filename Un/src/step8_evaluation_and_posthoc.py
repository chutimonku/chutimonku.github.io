#!/usr/bin/env python3
"""Step 8: Evaluate clustering quality and run post-hoc outcome validation.

Important:
- Outcomes are used only after the clustering model is locked.
- Grade, certification, viewed, explored, and incomplete status never enter
  the clustering feature matrix or model.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


CONFIG_PATH = Path("config/project_config.json")

FEATURE_MATRIX_PATH = Path("data/processed/feature_matrix.parquet")
RAW_BEHAVIOR_PATH = Path("data/processed/behavior_features_unscaled.parquet")
ENROLLMENTS_PATH = Path("data/processed/enrollments_cleaned.parquet")
RAW_OUTCOMES_PATH = Path("data/quarantine/raw_outcomes.parquet")

ASSIGNMENTS_PATH = Path("outputs/data/cluster_assignments.csv")
K_METRICS_PATH = Path("outputs/tables/k_selection_metrics.csv")
PROFILES_PATH = Path("outputs/tables/cluster_profiles.csv")

TABLES_DIR = Path("outputs/tables")
FIGURES_DIR = Path("outputs/figures/evaluation")
REPRO_DIR = Path("outputs/reproducibility")

POSTHOC_SUMMARY_PATH = TABLES_DIR / "posthoc_cluster_summary.csv"
VALIDATION_SUMMARY_PATH = TABLES_DIR / "cluster_validation_summary.json"
PCA_PROJECTION_PATH = TABLES_DIR / "cluster_pca_projection.csv"
PCA_VARIANCE_PATH = TABLES_DIR / "cluster_pca_variance.csv"


plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Thonburi",
    "Sukhumvit Set",
    "Arial Unicode MS",
    "DejaVu Sans"
]
plt.rcParams["axes.unicode_minus"] = False


def validate_one_to_one_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    key: str
) -> None:
    """Ensure student-level tables can safely join without row multiplication."""
    if left[key].duplicated().any():
        raise ValueError(f"Left table contains duplicate {key} values.")

    if right[key].duplicated().any():
        raise ValueError(f"Right table contains duplicate {key} values.")


def main() -> None:
    required_paths = [
        CONFIG_PATH,
        FEATURE_MATRIX_PATH,
        RAW_BEHAVIOR_PATH,
        ENROLLMENTS_PATH,
        RAW_OUTCOMES_PATH,
        ASSIGNMENTS_PATH,
        K_METRICS_PATH,
        PROFILES_PATH
    ]

    for required_path in required_paths:
        if not required_path.exists():
            raise FileNotFoundError(
                f"Missing required input: {required_path}. "
                "Run previous workflow steps first."
            )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    behavior_features = config["behavior_features"]

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPRO_DIR.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")

    print("=" * 72)
    print("STEP 8: CLUSTER EVALUATION AND POST-HOC OUTCOME VALIDATION")
    print("=" * 72)

    feature_matrix = pd.read_parquet(FEATURE_MATRIX_PATH)
    raw_behavior = pd.read_parquet(RAW_BEHAVIOR_PATH)
    assignments = pd.read_csv(ASSIGNMENTS_PATH)
    k_metrics = pd.read_csv(K_METRICS_PATH)
    cluster_profiles = pd.read_csv(PROFILES_PATH)

    expected_feature_columns = ["userid_DI", *behavior_features]

    if feature_matrix.columns.tolist() != expected_feature_columns:
        raise ValueError(
            "Unexpected feature matrix schema. Expected userid_DI and the "
            "four configured behavioural features only."
        )

    validate_one_to_one_merge(
        feature_matrix[["userid_DI"]],
        assignments[["userid_DI"]],
        "userid_DI"
    )

    evaluation = feature_matrix.merge(
        assignments[["userid_DI", "cluster"]],
        on="userid_DI",
        how="inner",
        validate="one_to_one"
    )

    if len(evaluation) != len(feature_matrix):
        raise RuntimeError(
            "Some students have no cluster assignment."
        )

    X = evaluation[behavior_features].to_numpy(dtype=float)
    labels = evaluation["cluster"].to_numpy(dtype=int)

    if len(np.unique(labels)) < 2:
        raise RuntimeError(
            "At least two clusters are required for evaluation."
        )

    silhouette_sample_size = min(5000, len(X))

    final_metrics = {
        "silhouette": float(
            silhouette_score(
                X,
                labels,
                sample_size=silhouette_sample_size,
                random_state=config["random_seed"]
            )
        ),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
        "cluster_count": int(len(np.unique(labels))),
        "student_count": int(len(evaluation)),
        "smallest_cluster_pct": float(
            evaluation["cluster"]
            .value_counts(normalize=True)
            .min()
            * 100
        )
    }

    selected_metric_row = k_metrics.loc[
        k_metrics["selected_k"].astype(bool)
    ]

    if selected_metric_row.empty:
        raise RuntimeError(
            "No selected K was found in k_selection_metrics.csv."
        )

    selected_metric_row = selected_metric_row.iloc[0]

    # ------------------------------------------------------------------
    # 1. PCA visualisation of the final cluster assignments.
    # Three components are retained for a genuine 3D view; PCA remains
    # explanatory only and never participates in model fitting.
    # ------------------------------------------------------------------
    pca = PCA(n_components=3, random_state=config["random_seed"])
    projected = pca.fit_transform(X)

    projection = pd.DataFrame({
        "userid_DI": evaluation["userid_DI"],
        "cluster": labels,
        "pca_component_1": projected[:, 0],
        "pca_component_2": projected[:, 1],
        "pca_component_3": projected[:, 2]
    })

    projection.to_csv(
        PCA_PROJECTION_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    pd.DataFrame({
        "component": ["PC1", "PC2", "PC3"],
        "explained_variance_ratio": pca.explained_variance_ratio_,
        "cumulative_explained_variance_ratio": (
            np.cumsum(pca.explained_variance_ratio_)
        )
    }).to_csv(PCA_VARIANCE_PATH, index=False, encoding="utf-8-sig")

    fig, axis = plt.subplots(figsize=(10, 7), facecolor="white")

    sns.scatterplot(
        data=projection,
        x="pca_component_1",
        y="pca_component_2",
        hue="cluster",
        palette="tab10",
        alpha=0.55,
        s=22,
        linewidth=0,
        ax=axis
    )

    axis.set_title(
        "Cluster Projection in Two Dimensions (PCA)",
        fontsize=14,
        fontweight="bold"
    )
    axis.set_xlabel(
        f"PCA Component 1 ({pca.explained_variance_ratio_[0] * 100:.1f}% variance)"
    )
    axis.set_ylabel(
        f"PCA Component 2 ({pca.explained_variance_ratio_[1] * 100:.1f}% variance)"
    )
    axis.legend(title="Cluster", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    fig.savefig(
        FIGURES_DIR / "cluster_projection_pca.png",
        dpi=220,
        bbox_inches="tight"
    )
    plt.close(fig)

    # A deterministic sample prevents overplotting while retaining the same
    # cluster proportions in the static three-dimensional chart.
    plot_size = min(30000, len(projection))
    plot_projection = projection.sample(
        n=plot_size,
        random_state=config["random_seed"]
    )
    fig = plt.figure(figsize=(11, 8), facecolor="white")
    axis = fig.add_subplot(111, projection="3d")
    palette = sns.color_palette("tab10", n_colors=len(np.unique(labels)))
    for color, cluster in zip(palette, sorted(plot_projection["cluster"].unique())):
        subset = plot_projection.loc[plot_projection["cluster"].eq(cluster)]
        axis.scatter(
            subset["pca_component_1"],
            subset["pca_component_2"],
            subset["pca_component_3"],
            color=color,
            s=5,
            alpha=.32,
            label=f"Cluster {cluster}",
            depthshade=False
        )
    axis.set_title("Three-Dimensional PCA Projection of Behavioural Segments", pad=18, fontweight="bold")
    axis.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f}%)")
    axis.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1] * 100:.1f}%)")
    axis.set_zlabel(f"PC3 ({pca.explained_variance_ratio_[2] * 100:.1f}%)")
    axis.view_init(elev=24, azim=42)
    axis.legend(title="Cluster", loc="upper left")
    plt.tight_layout()
    fig.savefig(
        FIGURES_DIR / "cluster_projection_pca_3d.png",
        dpi=220,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 2. Behaviour profile heatmap
    # Uses unscaled percentile values for readable interpretation.
    # ------------------------------------------------------------------
    profile_columns = [
        "cluster",
        "cluster_name",
        "student_count",
        "student_pct",
        *behavior_features
    ]

    existing_profile_columns = [
        column
        for column in profile_columns
        if column in cluster_profiles.columns
    ]

    profile_display = cluster_profiles[existing_profile_columns].copy()

    heatmap_columns = [
        column
        for column in behavior_features
        if column in profile_display.columns
    ]

    fig, axis = plt.subplots(
        figsize=(11, max(4, len(profile_display) * 1.2)),
        facecolor="white"
    )

    sns.heatmap(
        profile_display.set_index("cluster")[heatmap_columns],
        annot=True,
        fmt=".3f",
        cmap="YlGnBu",
        vmin=0,
        vmax=1,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Mean percentile within course"},
        ax=axis
    )

    axis.set_title(
        "Cluster Behaviour Profiles\nMean Course-Normalized Percentiles",
        fontsize=14,
        fontweight="bold"
    )
    axis.set_xlabel("Behavioural feature")
    axis.set_ylabel("Cluster")

    plt.tight_layout()
    fig.savefig(
        FIGURES_DIR / "cluster_behavior_profile_heatmap.png",
        dpi=220,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 3. Post-hoc outcome validation
    # Merge outcomes only after cluster labels are final.
    # ------------------------------------------------------------------
    enrollments = pd.read_parquet(ENROLLMENTS_PATH)
    outcomes = pd.read_parquet(RAW_OUTCOMES_PATH)

    outcomes = outcomes.rename(
        columns={"Unnamed: 0": "source_row_id"}
    ).copy()

    enrollments["source_row_id"] = (
        enrollments["source_row_id"].astype("string")
    )
    outcomes["source_row_id"] = outcomes["source_row_id"].astype("string")

    outcome_columns = [
        "source_row_id",
        "certified",
        "grade",
        "viewed",
        "explored",
        "incomplete_flag"
    ]

    enrollment_outcomes = enrollments.merge(
        outcomes[outcome_columns],
        on="source_row_id",
        how="left",
        validate="one_to_one"
    )

    for column in [
        "certified",
        "grade",
        "viewed",
        "explored",
        "incomplete_flag"
    ]:
        enrollment_outcomes[column] = pd.to_numeric(
            enrollment_outcomes[column],
            errors="coerce"
        )

    # Build outcome summary at exactly the same student level as the cluster.
    student_outcomes = (
        enrollment_outcomes.groupby("userid_DI", dropna=False)
        .agg(
            certification_rate=("certified", "max"),
            mean_grade=("grade", "mean"),
            max_grade=("grade", "max"),
            viewed_any=("viewed", "max"),
            explored_any=("explored", "max"),
            incomplete_any=("incomplete_flag", "max"),
            certified_grade_zero_records=(
                "certified",
                lambda certified: 0
            )
        )
        .reset_index()
    )

    # Count certified=1 and grade=0 directly from enrollment-level records.
    grade_zero_counts = (
        enrollment_outcomes.assign(
            certified_grade_zero=(
                enrollment_outcomes["certified"].eq(1)
                & enrollment_outcomes["grade"].eq(0)
            ).astype("int8")
        )
        .groupby("userid_DI", as_index=False)["certified_grade_zero"]
        .sum()
        .rename(
            columns={
                "certified_grade_zero": "certified_grade_zero_records"
            }
        )
    )

    student_outcomes = student_outcomes.drop(
        columns=["certified_grade_zero_records"]
    ).merge(
        grade_zero_counts,
        on="userid_DI",
        how="left",
        validate="one_to_one"
    )

    validate_one_to_one_merge(
        assignments[["userid_DI"]],
        student_outcomes[["userid_DI"]],
        "userid_DI"
    )

    posthoc = assignments.merge(
        student_outcomes,
        on="userid_DI",
        how="inner",
        validate="one_to_one"
    )

    posthoc_summary = (
        posthoc.groupby("cluster", dropna=False)
        .agg(
            student_count=("userid_DI", "size"),
            certification_rate=("certification_rate", "mean"),
            mean_grade=("mean_grade", "mean"),
            median_grade=("mean_grade", "median"),
            viewed_rate=("viewed_any", "mean"),
            explored_rate=("explored_any", "mean"),
            incomplete_rate=("incomplete_any", "mean"),
            certified_grade_zero_records=(
                "certified_grade_zero_records",
                "sum"
            )
        )
        .reset_index()
    )

    posthoc_summary["student_pct"] = (
        posthoc_summary["student_count"]
        / posthoc_summary["student_count"].sum()
        * 100
    )

    posthoc_summary = posthoc_summary.merge(
        cluster_profiles[
            [
                "cluster",
                "cluster_name",
                "relative_behavior_level"
            ]
        ],
        on="cluster",
        how="left",
        validate="one_to_one"
    )

    posthoc_summary.to_csv(
        POSTHOC_SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    # ------------------------------------------------------------------
    # 4. Post-hoc outcome charts
    # Outcomes are labels for interpretation, not clustering inputs.
    # ------------------------------------------------------------------
    plot_summary = posthoc_summary.sort_values("cluster").copy()

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), facecolor="white")

    charts = [
        (
            "certification_rate",
            "Certification Rate",
            "Rate",
            "#10B981"
        ),
        (
            "mean_grade",
            "Mean Grade",
            "Grade",
            "#2563EB"
        ),
        (
            "incomplete_rate",
            "Incomplete Rate",
            "Rate",
            "#F97316"
        )
    ]

    for axis, (column, title, ylabel, color) in zip(axes, charts):
        bars = axis.bar(
            plot_summary["cluster"].astype(str),
            plot_summary[column],
            color=color
        )

        axis.set_title(title, fontweight="bold")
        axis.set_xlabel("Cluster")
        axis.set_ylabel(ylabel)

        for bar, value in zip(bars, plot_summary[column]):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )

    fig.suptitle(
        "Post-hoc Outcomes by Cluster\n"
        "Outcomes were not used to create clusters.",
        fontsize=15,
        fontweight="bold"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(
        FIGURES_DIR / "posthoc_outcomes_by_cluster.png",
        dpi=220,
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------------------------------
    # 5. Final validation summary for report/dashboard use
    # ------------------------------------------------------------------
    validation_summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_type": "unsupervised_clustering",
        "outcomes_used_in_model": False,
        "outcomes_used_for_posthoc_validation_only": True,
        "final_cluster_metrics": final_metrics,
        "k_selection_metrics_for_selected_k": {
            "k": int(selected_metric_row["k"]),
            "silhouette": float(selected_metric_row["silhouette"]),
            "davies_bouldin": float(
                selected_metric_row["davies_bouldin"]
            ),
            "calinski_harabasz": float(
                selected_metric_row["calinski_harabasz"]
            ),
            "resample_ari_mean": float(
                selected_metric_row["resample_ari_mean"]
            ),
            "resample_ari_std": float(
                selected_metric_row["resample_ari_std"]
            ),
            "mean_metric_rank": float(
                selected_metric_row["mean_metric_rank"]
            )
        },
        "posthoc_outcome_summary_path": str(POSTHOC_SUMMARY_PATH),
        "grade_quality_rule": (
            "Certified learners with grade equal to zero are reported as "
            "outcome-quality flags. They are not silently removed from raw data."
        ),
        "limitations": [
            "PCA is a visualization only and does not define clusters.",
            "Post-hoc outcomes are descriptive associations, not causal effects.",
            "Clusters must not be used as automated high-stakes decisions."
        ]
    }

    VALIDATION_SUMMARY_PATH.write_text(
        json.dumps(validation_summary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[Step 8] PCA projection: {PCA_PROJECTION_PATH}")
    print(f"[Step 8] PCA variance: {PCA_VARIANCE_PATH}")
    print(f"[Step 8] 3D PCA: {FIGURES_DIR / 'cluster_projection_pca_3d.png'}")
    print(f"[Step 8] Cluster heatmap: {FIGURES_DIR / 'cluster_behavior_profile_heatmap.png'}")
    print(f"[Step 8] Post-hoc outcome chart: {FIGURES_DIR / 'posthoc_outcomes_by_cluster.png'}")
    print(f"[Step 8] Post-hoc summary: {POSTHOC_SUMMARY_PATH}")
    print(f"[Step 8] Validation summary: {VALIDATION_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
