#!/usr/bin/env python3
"""Steps 6-7: Select K, train the K-Means clustering model, and save artifacts.

K is selected from four metrics:
- Silhouette: higher is better
- Davies-Bouldin: lower is better
- Calinski-Harabasz: higher is better
- Resample Adjusted Rand Index: higher is more stable

Only the four approved behavioural features are used.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.pipeline import Pipeline


CONFIG_PATH = Path("config/project_config.json")

FEATURE_MATRIX_PATH = Path("data/processed/feature_matrix.parquet")
RAW_BEHAVIOR_PATH = Path("data/processed/behavior_features_unscaled.parquet")
PREPROCESSOR_PATH = Path(
    "models/preprocessing_candidates/behavioral_preprocessor.joblib"
)

CANDIDATES_DIR = Path("models/candidates")
FINAL_DIR = Path("models/final")
TABLES_DIR = Path("outputs/tables")
FIGURES_DIR = Path("outputs/figures/modeling")
DATA_DIR = Path("outputs/data")
REPRO_DIR = Path("outputs/reproducibility")

K_METRICS_PATH = TABLES_DIR / "k_selection_metrics.csv"
K_PLOT_PATH = FIGURES_DIR / "k_selection_four_metrics.png"
ASSIGNMENTS_PATH = DATA_DIR / "cluster_assignments.csv"
PROFILES_PATH = TABLES_DIR / "cluster_profiles.csv"
TRAINING_LOG_PATH = TABLES_DIR / "clustering_training_log.json"
MODEL_CARD_PATH = FINAL_DIR / "model_card.md"
FINAL_MODEL_PATH = FINAL_DIR / "cluster_model.joblib"
FINAL_PIPELINE_PATH = FINAL_DIR / "clustering_pipeline.joblib"


def make_metric_sample(
    X: np.ndarray,
    max_size: int,
    seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Return a deterministic sample for K-metric computation."""
    n_rows = len(X)

    if n_rows <= max_size:
        return X, np.arange(n_rows)

    rng = np.random.default_rng(seed)
    indices = np.sort(
        rng.choice(n_rows, size=max_size, replace=False)
    )

    return X[indices], indices


def calculate_resample_ari(
    X: np.ndarray,
    k: int,
    seed: int,
    repeats: int
) -> tuple[float, float]:
    """Estimate clustering stability using overlapping 80% resamples.

    Two K-Means models are fitted on independently sampled subsets.
    Their predicted labels are compared only on the overlapping observations.
    ARI is label-order invariant, so Cluster 0/1 label swaps do not matter.
    """
    rng = np.random.default_rng(seed)
    n_rows = len(X)
    subset_size = max(k * 3, int(n_rows * 0.80))
    scores: list[float] = []

    for repeat in range(repeats):
        sample_a = np.sort(
            rng.choice(n_rows, size=subset_size, replace=False)
        )
        sample_b = np.sort(
            rng.choice(n_rows, size=subset_size, replace=False)
        )

        overlap = np.intersect1d(sample_a, sample_b)

        if len(overlap) < k * 3:
            continue

        model_a = KMeans(
            n_clusters=k,
            n_init=20,
            random_state=seed + repeat * 2 + 1
        ).fit(X[sample_a])

        model_b = KMeans(
            n_clusters=k,
            n_init=20,
            random_state=seed + repeat * 2 + 2
        ).fit(X[sample_b])

        labels_a = model_a.predict(X[overlap])
        labels_b = model_b.predict(X[overlap])

        scores.append(float(adjusted_rand_score(labels_a, labels_b)))

    if not scores:
        return np.nan, np.nan

    return float(np.mean(scores)), float(np.std(scores))


def evaluate_k_grid(
    X: np.ndarray,
    k_values: list[int],
    seed: int,
    stability_resamples: int
) -> pd.DataFrame:
    """Calculate all requested K-selection metrics."""
    rows = []

    for k in k_values:
        print(f"[Step 6-7] Evaluating K={k}...")
        started_at = time.perf_counter()

        model = KMeans(
            n_clusters=k,
            n_init=20,
            random_state=seed
        )

        labels = model.fit_predict(X)

        cluster_sizes = (
            pd.Series(labels)
            .value_counts(normalize=True)
            .sort_index()
        )

        # Silhouette uses a smaller deterministic internal sample because
        # pairwise distance calculations become expensive on large cohorts.
        silhouette_sample_size = min(5000, len(X))

        silhouette = silhouette_score(
            X,
            labels,
            sample_size=silhouette_sample_size,
            random_state=seed
        )

        davies_bouldin = davies_bouldin_score(X, labels)
        calinski_harabasz = calinski_harabasz_score(X, labels)

        ari_mean, ari_std = calculate_resample_ari(
            X=X,
            k=k,
            seed=seed,
            repeats=stability_resamples
        )

        rows.append({
            "k": k,
            "silhouette": float(silhouette),
            "davies_bouldin": float(davies_bouldin),
            "calinski_harabasz": float(calinski_harabasz),
            "resample_ari_mean": ari_mean,
            "resample_ari_std": ari_std,
            "inertia": float(model.inertia_),
            "smallest_cluster_pct": float(cluster_sizes.min() * 100),
            "largest_cluster_pct": float(cluster_sizes.max() * 100),
            "silhouette_sample_size": silhouette_sample_size,
            "metric_sample_size": int(len(X)),
            "runtime_seconds": float(time.perf_counter() - started_at),
            "status": "success"
        })

    metrics = pd.DataFrame(rows)

    # Gap Statistic compares observed compactness with uniform null-reference
    # datasets. The one-standard-error rule avoids selecting K solely because
    # internal geometry indices often prefer coarse, nearly spherical splits.
    rng = np.random.default_rng(seed)
    lower, upper = X.min(axis=0), X.max(axis=0)
    gap_rows = []
    for k in range(1, max(k_values) + 1):
        observed = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(X).inertia_
        reference_logs = []
        for repeat in range(10):
            reference = rng.uniform(lower, upper, size=X.shape)
            reference_logs.append(np.log(KMeans(
                n_clusters=k, n_init=5, random_state=seed + 100 + repeat
            ).fit(reference).inertia_))
        gap_rows.append({
            "k": k,
            "gap_statistic": float(np.mean(reference_logs) - np.log(observed)),
            "gap_standard_error": float(np.std(reference_logs, ddof=1) * np.sqrt(1.1)),
        })
    gap_frame = pd.DataFrame(gap_rows)
    metrics = metrics.merge(gap_frame, on="k", how="left")

    # A cluster with less than 1% of the metric sample is considered too small
    # for stable, interpretable support planning.
    metrics["eligible_for_selection"] = (
        metrics["smallest_cluster_pct"] >= 1.0
    )

    eligible = metrics.loc[
        metrics["eligible_for_selection"]
        & metrics["resample_ari_mean"].notna()
    ].copy()

    if eligible.empty:
        raise RuntimeError(
            "No K candidate passed the minimum cluster-size and stability rules."
        )

    eligible["rank_silhouette"] = eligible["silhouette"].rank(
        ascending=False,
        method="min"
    )

    eligible["rank_davies_bouldin"] = eligible["davies_bouldin"].rank(
        ascending=True,
        method="min"
    )

    eligible["rank_calinski_harabasz"] = eligible[
        "calinski_harabasz"
    ].rank(
        ascending=False,
        method="min"
    )

    eligible["rank_resample_ari"] = eligible[
        "resample_ari_mean"
    ].rank(
        ascending=False,
        method="min"
    )

    eligible["mean_metric_rank"] = eligible[
        [
            "rank_silhouette",
            "rank_davies_bouldin",
            "rank_calinski_harabasz",
            "rank_resample_ari"
        ]
    ].mean(axis=1)

    eligible = eligible.sort_values(
        [
            "mean_metric_rank",
            "davies_bouldin",
            "k"
        ],
        ascending=[True, True, True]
    )

    gap_selected_k = None
    for k in k_values[:-1]:
        current = gap_frame.loc[gap_frame["k"].eq(k), "gap_statistic"].iloc[0]
        next_row = gap_frame.loc[gap_frame["k"].eq(k + 1)].iloc[0]
        if current >= next_row["gap_statistic"] - next_row["gap_standard_error"]:
            if k in set(eligible["k"].astype(int)):
                gap_selected_k = int(k)
                break
    selected_k = gap_selected_k if gap_selected_k is not None else int(eligible.iloc[0]["k"])

    rank_columns = [
        "k",
        "rank_silhouette",
        "rank_davies_bouldin",
        "rank_calinski_harabasz",
        "rank_resample_ari",
        "mean_metric_rank"
    ]

    metrics = metrics.merge(
        eligible[rank_columns],
        on="k",
        how="left"
    )

    metrics["selected_by_gap_one_se"] = metrics["k"].eq(selected_k)
    metrics["selected_k"] = metrics["k"].eq(selected_k)

    return metrics.sort_values("k").reset_index(drop=True)


def plot_k_metrics(
    metrics: pd.DataFrame,
    selected_k: int,
    output_path: Path
) -> None:
    """Create the requested four-metric K-selection graph."""
    chart_specs = [
        ("inertia", "Inertia / WCSS", "Look for diminishing returns", "#0EA5E9"),
        (
            "silhouette",
            "Silhouette Score",
            "Higher is better",
            "#2563EB"
        ),
        (
            "davies_bouldin",
            "Davies–Bouldin Index",
            "Lower is better",
            "#F97316"
        ),
        (
            "calinski_harabasz",
            "Calinski–Harabasz Index",
            "Higher is better",
            "#8B5CF6"
        ),
        (
            "resample_ari_mean",
            "Resample Adjusted Rand Index",
            "Higher is more stable",
            "#10B981"
        ),
        ("gap_statistic", "Gap Statistic", "One-SE rule balances fit against null data", "#DB2777")
    ]

    fig, axes = plt.subplots(
        2,
        3,
        figsize=(18, 10),
        facecolor="white",
        sharex=True
    )

    for axis, (column, title, direction, color) in zip(
        axes.ravel(),
        chart_specs
    ):
        axis.plot(
            metrics["k"],
            metrics[column],
            marker="o",
            markersize=7,
            linewidth=2.5,
            color=color
        )

        selected_value = metrics.loc[
            metrics["k"].eq(selected_k),
            column
        ].iloc[0]

        axis.scatter(
            [selected_k],
            [selected_value],
            s=95,
            color="#EF4444",
            edgecolor="white",
            linewidth=1.5,
            zorder=5
        )

        axis.axvline(
            selected_k,
            color="#EF4444",
            linestyle="--",
            linewidth=2,
            label=f"Selected K = {selected_k}"
        )

        axis.set_title(f"{title}\n{direction}", fontweight="bold")
        axis.set_xlabel("Number of clusters (K)")
        axis.set_ylabel(title)
        axis.set_xticks(metrics["k"].tolist())
        axis.grid(alpha=0.25)
        axis.legend(loc="best")

    fig.suptitle(
        f"K Selection Diagnostics + Gap One-SE Rule — Selected K = {selected_k}",
        fontsize=16,
        fontweight="bold"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def make_cluster_profiles(
    raw_features: pd.DataFrame,
    assignments: pd.DataFrame,
    behavior_features: list[str]
) -> pd.DataFrame:
    """Create interpretable profiles using unscaled percentile values."""
    profile_frame = raw_features.merge(
        assignments[["userid_DI", "cluster"]],
        on="userid_DI",
        how="inner",
        validate="one_to_one"
    )

    cluster_sizes = (
        profile_frame.groupby("cluster")
        .size()
        .rename("student_count")
    )

    profiles = (
        profile_frame.groupby("cluster")[behavior_features]
        .mean()
        .join(cluster_sizes)
        .reset_index()
    )

    profiles["student_pct"] = (
        profiles["student_count"]
        / profiles["student_count"].sum()
        * 100
    )

    profiles["mean_behavior_percentile"] = profiles[
        behavior_features
    ].mean(axis=1)

    profiles["relative_behavior_level"] = np.select(
        [
            profiles["mean_behavior_percentile"].ge(0.67),
            profiles["mean_behavior_percentile"].le(0.33)
        ],
        [
            "Higher relative behavioural activity",
            "Lower relative behavioural activity"
        ],
        default="Moderate relative behavioural activity"
    )

    profiles["cluster_name"] = profiles["cluster"].apply(
        lambda value: f"Cluster {value}"
    )

    return profiles.sort_values("cluster").reset_index(drop=True)


def main() -> None:
    required_paths = [
        CONFIG_PATH,
        FEATURE_MATRIX_PATH,
        RAW_BEHAVIOR_PATH,
        PREPROCESSOR_PATH
    ]

    for required_path in required_paths:
        if not required_path.exists():
            raise FileNotFoundError(
                f"Missing required input: {required_path}. "
                "Run the previous workflow step first."
            )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    behavior_features = config["behavior_features"]
    k_values = config["candidate_k_range"]
    stability_resamples = config["stability_resamples"]
    seed = config["random_seed"]

    for directory in [
        CANDIDATES_DIR,
        FINAL_DIR,
        TABLES_DIR,
        FIGURES_DIR,
        DATA_DIR,
        REPRO_DIR
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("STEPS 6-7: K SELECTION AND K-MEANS CLUSTER MODEL TRAINING")
    print("=" * 72)

    feature_matrix = pd.read_parquet(FEATURE_MATRIX_PATH)
    raw_behavior = pd.read_parquet(RAW_BEHAVIOR_PATH)

    expected_columns = ["userid_DI", *behavior_features]

    if feature_matrix.columns.tolist() != expected_columns:
        raise ValueError(
            "feature_matrix.parquet must contain exactly userid_DI followed by "
            "the four configured behavioural features."
        )

    if feature_matrix["userid_DI"].duplicated().any():
        raise ValueError(
            "feature_matrix.parquet contains duplicate userid_DI values."
        )

    if feature_matrix[behavior_features].isna().any().any():
        raise ValueError(
            "feature_matrix.parquet contains missing model values."
        )

    X_full = feature_matrix[behavior_features].to_numpy(dtype=float)

    # The full cohort is used for final model fitting.
    # A deterministic subset is used only for expensive K metric calculations.
    metric_sample_size = min(12000, len(X_full))
    X_metric, metric_indices = make_metric_sample(
        X_full,
        max_size=metric_sample_size,
        seed=seed
    )

    print(f"[Step 6-7] Full student cohort: {len(X_full):,}")
    print(f"[Step 6-7] K-metric sample: {len(X_metric):,}")
    print(f"[Step 6-7] Candidate K values: {k_values}")

    metrics = evaluate_k_grid(
        X=X_metric,
        k_values=k_values,
        seed=seed,
        stability_resamples=stability_resamples
    )

    selected_k = int(
        metrics.loc[
            metrics["selected_k"],
            "k"
        ].iloc[0]
    )

    metrics.to_csv(
        K_METRICS_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    plot_k_metrics(
        metrics=metrics,
        selected_k=selected_k,
        output_path=K_PLOT_PATH
    )

    print(f"[Step 6-7] Selected K from Gap one-SE rule with metric/stability guardrails: {selected_k}")

    # Train the final K-Means model on all student records.
    final_started_at = time.perf_counter()

    final_model = KMeans(
        n_clusters=selected_k,
        n_init=30,
        random_state=seed
    )

    final_labels = final_model.fit_predict(X_full)

    final_runtime_seconds = float(
        time.perf_counter() - final_started_at
    )

    selected_candidate_path = (
        CANDIDATES_DIR / f"kmeans_k{selected_k}.joblib"
    )

    joblib.dump(final_model, selected_candidate_path)
    joblib.dump(final_model, FINAL_MODEL_PATH)

    # Construct an end-to-end pipeline for future compatible student-level data.
    preprocessor = joblib.load(PREPROCESSOR_PATH)

    deployment_pipeline = Pipeline(
        steps=[
            ("behavioral_preprocessor", preprocessor),
            ("kmeans", final_model)
        ]
    )

    joblib.dump(deployment_pipeline, FINAL_PIPELINE_PATH)

    assignments = pd.DataFrame({
        "userid_DI": feature_matrix["userid_DI"],
        "cluster": final_labels
    })

    assignments.to_csv(
        ASSIGNMENTS_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    profiles = make_cluster_profiles(
        raw_features=raw_behavior,
        assignments=assignments,
        behavior_features=behavior_features
    )

    profiles.to_csv(
        PROFILES_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    selected_row = metrics.loc[
        metrics["k"].eq(selected_k)
    ].iloc[0].to_dict()

    training_log = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_type": "unsupervised_clustering",
        "algorithm": "KMeans",
        "random_seed": seed,
        "full_student_count": int(len(X_full)),
        "metric_sample_count": int(len(X_metric)),
        "metric_sample_indices_saved": False,
        "behavior_features": behavior_features,
        "excluded_columns": {
            "profiles": config["profile_columns"],
            "outcomes": config["outcome_columns"]
        },
        "candidate_k_range": k_values,
        "stability_resamples": stability_resamples,
        "selected_k": selected_k,
        "selection_rule": (
            "Gap Statistic one-standard-error rule, restricted to candidates "
            "passing cluster-size and resampling-stability guardrails; internal "
            "metrics are reported as diagnostics rather than averaged as if "
            "they measured the same construct."
        ),
        "selected_k_metrics": {
            "silhouette": float(selected_row["silhouette"]),
            "davies_bouldin": float(selected_row["davies_bouldin"]),
            "calinski_harabasz": float(
                selected_row["calinski_harabasz"]
            ),
            "resample_ari_mean": float(
                selected_row["resample_ari_mean"]
            ),
            "resample_ari_std": float(
                selected_row["resample_ari_std"]
            ),
            "smallest_cluster_pct": float(
                selected_row["smallest_cluster_pct"]
            ),
            "gap_statistic": float(selected_row["gap_statistic"]),
            "gap_standard_error": float(selected_row["gap_standard_error"])
        },
        "final_fit_runtime_seconds": final_runtime_seconds,
        "artifacts": {
            "k_metrics_table": str(K_METRICS_PATH),
            "k_metrics_figure": str(K_PLOT_PATH),
            "candidate_model": str(selected_candidate_path),
            "final_model": str(FINAL_MODEL_PATH),
            "deployment_pipeline": str(FINAL_PIPELINE_PATH),
            "cluster_assignments": str(ASSIGNMENTS_PATH),
            "cluster_profiles": str(PROFILES_PATH)
        }
    }

    TRAINING_LOG_PATH.write_text(
        json.dumps(training_log, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    model_card = f"""# MOOC Student Behaviour Clustering Model Card

## Purpose

This model segments MOOC learners from four observed behavioural features.
It supports descriptive learner-support planning and does not determine learner
ability, eligibility, or educational value.

## Unit of analysis

One row per `userid_DI`.

## Final algorithm

K-Means with `K = {selected_k}`.

## Input features

{chr(10).join(f"- `{feature}`" for feature in behavior_features)}

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

- Silhouette: {selected_row["silhouette"]:.4f}
- Davies-Bouldin: {selected_row["davies_bouldin"]:.4f}
- Calinski-Harabasz: {selected_row["calinski_harabasz"]:.2f}
- Mean Resample ARI: {selected_row["resample_ari_mean"]:.4f}
- Smallest cluster: {selected_row["smallest_cluster_pct"]:.2f}%

## Limitations

- The source is aggregated person-course data and is not a weekly early-warning dataset.
- Video duration is unavailable. The workflow analyses video-play counts only.
- Clusters describe observed patterns and require contextual interpretation.
- New data must use the same behavioural feature definitions.
"""

    MODEL_CARD_PATH.write_text(model_card, encoding="utf-8")

    print(f"[Step 6-7] K metrics table: {K_METRICS_PATH}")
    print(f"[Step 6-7] K metrics figure: {K_PLOT_PATH}")
    print(f"[Step 6-7] Final model: {FINAL_MODEL_PATH}")
    print(f"[Step 6-7] Deployment pipeline: {FINAL_PIPELINE_PATH}")
    print(f"[Step 6-7] Cluster assignments: {ASSIGNMENTS_PATH}")
    print(f"[Step 6-7] Cluster profiles: {PROFILES_PATH}")
    print(f"[Step 6-7] Final model runtime: {final_runtime_seconds:.2f} seconds")


if __name__ == "__main__":
    main()
