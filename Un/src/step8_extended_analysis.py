#!/usr/bin/env python3
"""Extended unsupervised diagnostics for Workflow.md Steps 6-8.

All candidate families use the same locked four-feature matrix.  The module
creates clustering-specific evidence (not supervised SHAP/error metrics):
model-family comparison, centroid separation contribution, assignment
ambiguity, leave-one-feature-out sensitivity, personas, and simulator data.
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
import seaborn as sns
from sklearn.cluster import Birch, KMeans, MiniBatchKMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


CONFIG_PATH = Path("config/project_config.json")
FEATURE_MATRIX_PATH = Path("data/processed/feature_matrix.parquet")
RAW_BEHAVIOR_PATH = Path("data/processed/behavior_features_unscaled.parquet")
ASSIGNMENTS_PATH = Path("outputs/data/cluster_assignments.csv")
PROFILES_PATH = Path("outputs/tables/cluster_profiles.csv")
MODEL_PATH = Path("models/final/cluster_model.joblib")
PREPROCESSOR_PATH = Path("models/preprocessing_candidates/behavioral_preprocessor.joblib")
FEATURE_AUDIT_PATH = Path("outputs/tables/feature_engineering_audit.json")

TABLES_DIR = Path("outputs/tables")
FIGURES_DIR = Path("outputs/figures/evaluation")
DATA_DIR = Path("outputs/data")

MODEL_COMPARISON_PATH = TABLES_DIR / "unsupervised_model_comparison.csv"
FEATURE_CONTRIBUTION_PATH = TABLES_DIR / "cluster_feature_contribution.csv"
AMBIGUITY_PATH = DATA_DIR / "cluster_assignment_diagnostics.csv"
BORDERLINE_PATH = TABLES_DIR / "borderline_learners.csv"
ABLATION_PATH = TABLES_DIR / "feature_ablation_sensitivity.csv"
PERSONA_PATH = TABLES_DIR / "student_persona_dossiers.csv"
SIMULATOR_PATH = DATA_DIR / "interactive_simulator_spec.json"


def metric_sample(X: np.ndarray, max_rows: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    if len(X) <= max_rows:
        return X, np.arange(len(X))
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(len(X), size=max_rows, replace=False))
    return X[idx], idx


def build_model(family: str, k: int, seed: int):
    if family == "K-Means":
        return KMeans(n_clusters=k, n_init=20, random_state=seed)
    if family == "MiniBatch K-Means":
        return MiniBatchKMeans(
            n_clusters=k, n_init=10, batch_size=1024, random_state=seed
        )
    if family == "Gaussian Mixture":
        return GaussianMixture(
            n_components=k, covariance_type="diag", n_init=3,
            reg_covar=1e-6, random_state=seed
        )
    if family == "BIRCH":
        return Birch(n_clusters=k, threshold=0.5)
    raise ValueError(f"Unknown family: {family}")


def fit_predict(model, X: np.ndarray) -> np.ndarray:
    if hasattr(model, "fit_predict"):
        return np.asarray(model.fit_predict(X), dtype=int)
    model.fit(X)
    return np.asarray(model.predict(X), dtype=int)


def safe_metrics(X: np.ndarray, labels: np.ndarray, seed: int) -> dict:
    unique = np.unique(labels)
    if len(unique) < 2 or len(unique) >= len(X):
        return {
            "silhouette": np.nan,
            "davies_bouldin": np.nan,
            "calinski_harabasz": np.nan,
            "smallest_cluster_pct": np.nan,
            "largest_cluster_pct": np.nan,
        }
    counts = pd.Series(labels).value_counts(normalize=True)
    return {
        "silhouette": float(silhouette_score(
            X, labels, sample_size=min(3000, len(X)), random_state=seed
        )),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
        "smallest_cluster_pct": float(counts.min() * 100),
        "largest_cluster_pct": float(counts.max() * 100),
    }


def stability_score(family: str, X: np.ndarray, k: int, seed: int) -> float:
    rng = np.random.default_rng(seed)
    scores = []
    subset_size = int(len(X) * 0.8)
    for repeat in range(3):
        a = np.sort(rng.choice(len(X), subset_size, replace=False))
        b = np.sort(rng.choice(len(X), subset_size, replace=False))
        overlap = np.intersect1d(a, b)
        model_a = build_model(family, k, seed + repeat * 2 + 1)
        model_b = build_model(family, k, seed + repeat * 2 + 2)
        fit_predict(model_a, X[a])
        fit_predict(model_b, X[b])
        if not hasattr(model_a, "predict") or not hasattr(model_b, "predict"):
            continue
        scores.append(adjusted_rand_score(
            model_a.predict(X[overlap]), model_b.predict(X[overlap])
        ))
    return float(np.mean(scores)) if scores else np.nan


def normalize_series(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    span = values.max() - values.min()
    if pd.isna(span) or span == 0:
        result = pd.Series(1.0, index=series.index)
    else:
        result = (values - values.min()) / span
    return result if higher_is_better else 1 - result


def main() -> None:
    required = [
        CONFIG_PATH, FEATURE_MATRIX_PATH, RAW_BEHAVIOR_PATH, ASSIGNMENTS_PATH,
        PROFILES_PATH, MODEL_PATH, PREPROCESSOR_PATH, FEATURE_AUDIT_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing inputs: " + ", ".join(missing))

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    feature_audit = json.loads(FEATURE_AUDIT_PATH.read_text(encoding="utf-8"))
    features = config["behavior_features"]
    seed = int(config["random_seed"])
    matrix = pd.read_parquet(FEATURE_MATRIX_PATH)
    raw_behavior = pd.read_parquet(RAW_BEHAVIOR_PATH)
    assignments = pd.read_csv(ASSIGNMENTS_PATH)
    profiles = pd.read_csv(PROFILES_PATH).sort_values("cluster")
    final_model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    X = matrix[features].to_numpy(float)
    X_sample, sample_idx = metric_sample(X, 12000, seed)
    selected_k = int(assignments["cluster"].nunique())

    # Distances and labels must describe the same learners in the same order.
    matrix_ids = matrix["userid_DI"].astype(str).reset_index(drop=True)
    assignment_ids = assignments["userid_DI"].astype(str).reset_index(drop=True)
    if not matrix_ids.equals(assignment_ids):
        assignments = matrix[["userid_DI"]].merge(
            assignments, on="userid_DI", how="left", validate="one_to_one"
        )
        if assignments["cluster"].isna().any():
            raise ValueError("Feature matrix and assignment learner IDs do not align")

    # Model-family comparison on one identical deterministic sample.
    comparison_rows = []
    family_labels: dict[str, np.ndarray] = {}
    for family in ["K-Means", "MiniBatch K-Means", "Gaussian Mixture", "BIRCH"]:
        started = time.perf_counter()
        model = build_model(family, selected_k, seed)
        labels = fit_predict(model, X_sample)
        family_labels[family] = labels
        row = {
            "model_family": family,
            "k": selected_k,
            "sample_size": len(X_sample),
            **safe_metrics(X_sample, labels, seed),
            "resample_ari": stability_score(family, X_sample, selected_k, seed),
            "runtime_seconds": time.perf_counter() - started,
        }
        comparison_rows.append(row)
    comparison = pd.DataFrame(comparison_rows)
    comparison["score_silhouette"] = normalize_series(comparison["silhouette"])
    comparison["score_db"] = normalize_series(comparison["davies_bouldin"], False)
    comparison["score_ch"] = normalize_series(comparison["calinski_harabasz"])
    comparison["score_stability"] = normalize_series(comparison["resample_ari"])
    comparison["composite_score"] = comparison[
        ["score_silhouette", "score_db", "score_ch", "score_stability"]
    ].mean(axis=1)
    comparison.to_csv(MODEL_COMPARISON_PATH, index=False, encoding="utf-8-sig")

    # Centroid separation contribution: between-cluster variance / total variance.
    joined = raw_behavior.merge(
        assignments[["userid_DI", "cluster"]], on="userid_DI",
        how="inner", validate="one_to_one"
    )
    global_means = joined[features].mean()
    total_var = joined[features].var(ddof=0).replace(0, np.nan)
    counts = joined.groupby("cluster").size()
    between = pd.Series(0.0, index=features)
    for cluster, group in joined.groupby("cluster"):
        between += counts.loc[cluster] * (group[features].mean() - global_means) ** 2
    between /= len(joined)
    importance = (between / total_var).fillna(0)
    importance = importance / importance.sum() if importance.sum() else importance
    contribution = pd.DataFrame({
        "feature": features,
        "centroid_separation_contribution": importance.values,
        "between_cluster_variance": between.values,
        "total_variance": total_var.values,
    }).sort_values("centroid_separation_contribution", ascending=False)
    contribution.to_csv(FEATURE_CONTRIBUTION_PATH, index=False, encoding="utf-8-sig")

    # Assignment ambiguity for final K-Means.
    distances = final_model.transform(X)
    ordered = np.sort(distances, axis=1)
    nearest = ordered[:, 0]
    second = ordered[:, 1]
    margin = (second - nearest) / np.maximum(second, 1e-12)
    diagnostics = assignments[["userid_DI", "cluster"]].copy()
    diagnostics["distance_to_centroid"] = nearest
    diagnostics["second_centroid_distance"] = second
    diagnostics["assignment_confidence"] = margin.clip(0, 1)
    threshold = float(np.quantile(margin, 0.05))
    diagnostics["borderline_flag"] = diagnostics["assignment_confidence"].le(threshold)
    diagnostics.to_csv(AMBIGUITY_PATH, index=False, encoding="utf-8-sig")
    diagnostics.loc[diagnostics["borderline_flag"]].sort_values(
        "assignment_confidence"
    ).head(5000).to_csv(BORDERLINE_PATH, index=False, encoding="utf-8-sig")

    # Leave-one-feature-out sensitivity, compared with baseline K-Means labels.
    baseline_labels = KMeans(
        n_clusters=selected_k, n_init=20, random_state=seed
    ).fit_predict(X_sample)
    ablation_rows = []
    for feature in features:
        keep = [name for name in features if name != feature]
        columns = [features.index(name) for name in keep]
        X_ab = X_sample[:, columns]
        labels = KMeans(
            n_clusters=selected_k, n_init=20, random_state=seed
        ).fit_predict(X_ab)
        ablation_rows.append({
            "removed_feature": feature,
            "remaining_feature_count": len(keep),
            "ari_vs_full_model": adjusted_rand_score(baseline_labels, labels),
            **safe_metrics(X_ab, labels, seed),
        })
    ablation = pd.DataFrame(ablation_rows)
    ablation.to_csv(ABLATION_PATH, index=False, encoding="utf-8-sig")

    # Human-readable persona dossiers derived only from observed profiles.
    persona_rows = []
    feature_short = {
        features[0]: "events", features[1]: "active days",
        features[2]: "chapters", features[3]: "forum posts",
    }
    for _, row in profiles.iterrows():
        ranked = sorted(features, key=lambda name: row[name], reverse=True)
        highest, lowest = ranked[0], ranked[-1]
        cluster = int(row["cluster"])
        persona_rows.append({
            "cluster": cluster,
            "persona_name": f"Persona {cluster + 1}: {feature_short[highest].title()}-led learners",
            "student_count": int(row["student_count"]),
            "student_pct": float(row["student_pct"]),
            "dominant_behavior": feature_short[highest],
            "lowest_behavior": feature_short[lowest],
            "behavioral_dossier": (
                f"Highest relative signal: {feature_short[highest]} "
                f"({row[highest]:.3f}); lowest: {feature_short[lowest]} "
                f"({row[lowest]:.3f})."
            ),
            "assignment_file": str(ASSIGNMENTS_PATH),
        })
    personas = pd.DataFrame(persona_rows)
    personas.to_csv(PERSONA_PATH, index=False, encoding="utf-8-sig")

    # Simulator specification replicates median imputation and the identity
    # transform used for the bounded percentile feature space.
    simulator = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "features": features,
        "feature_labels": feature_short,
        "allowed_range": [0.0, 1.0],
        "imputer_statistics": feature_audit["median_imputation_statistics"],
        "scaler_center": feature_audit["robust_scaler_center"],
        "scaler_scale": feature_audit["robust_scaler_scale"],
        "cluster_centers_scaled": final_model.cluster_centers_.tolist(),
        "persona_by_cluster": {
            str(row["cluster"]): row["persona_name"]
            for _, row in personas.iterrows()
        },
        "method": "Nearest locked K-Means centroid after median imputation; percentile geometry is preserved without rescaling.",
        "disclaimer": "Scenario exploration only; not a high-stakes learner decision.",
    }
    SIMULATOR_PATH.write_text(
        json.dumps(simulator, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Visual evidence.
    colors = ["#2563EB", "#7C3AED", "#10B981", "#F97316", "#EC4899"]
    fig, ax = plt.subplots(figsize=(8, 6), facecolor="white")
    ax.pie(
        personas["student_count"], labels=personas["persona_name"],
        autopct="%1.2f%%", startangle=90, colors=colors[:len(personas)],
        wedgeprops={"width": .38, "edgecolor": "white"}
    )
    ax.set_title("Discovered Student Personas — Cohort Share", fontweight="bold")
    fig.savefig(FIGURES_DIR / "persona_cluster_donut.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    labels_short = [feature_short[name].title() for name in features]
    angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(9, 8), subplot_kw={"polar": True}, facecolor="white")
    for idx, (_, row) in enumerate(profiles.iterrows()):
        values = [float(row[name]) for name in features]
        values += values[:1]
        ax.plot(angles, values, linewidth=2, color=colors[idx], label=f"Cluster {int(row['cluster'])}")
        ax.fill(angles, values, color=colors[idx], alpha=.10)
    ax.set_xticks(angles[:-1], labels_short)
    ax.set_ylim(0, 1)
    ax.set_title("Persona Radar — Relative Behaviour Profiles", pad=25, fontweight="bold")
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.12))
    fig.savefig(FIGURES_DIR / "persona_behavior_radar.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    sns.barplot(data=contribution, x="centroid_separation_contribution", y="feature", palette="viridis", ax=ax)
    ax.set_title("Clustering Feature Importance — Centroid Separation Contribution", fontweight="bold")
    ax.set_xlabel("Share of between-cluster separation")
    ax.set_ylabel("")
    fig.savefig(FIGURES_DIR / "cluster_feature_contribution.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), facecolor="white")
    sns.barplot(data=comparison, x="model_family", y="composite_score", palette="Set2", ax=axes[0])
    axes[0].tick_params(axis="x", rotation=18)
    axes[0].set_title("Model-Family Composite Comparison")
    axes[0].set_ylim(0, 1.05)
    radar_metrics = ["score_silhouette", "score_db", "score_ch", "score_stability"]
    radar_names = ["Silhouette", "DB", "CH", "Stability"]
    radar_angles = np.linspace(0, 2*np.pi, len(radar_metrics), endpoint=False).tolist()
    radar_angles += radar_angles[:1]
    axes[1].remove()
    radar = fig.add_subplot(1, 2, 2, polar=True)
    for idx, (_, row) in enumerate(comparison.iterrows()):
        values = [float(row[name]) for name in radar_metrics] + [float(row[radar_metrics[0]])]
        radar.plot(radar_angles, values, color=colors[idx], label=row["model_family"])
    radar.set_xticks(radar_angles[:-1], radar_names)
    radar.set_ylim(0, 1)
    radar.set_title("Model-Family Radar")
    radar.legend(loc="upper right", bbox_to_anchor=(1.45, 1.15), fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "model_family_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), facecolor="white")
    sns.histplot(diagnostics["assignment_confidence"], bins=40, color="#2563EB", ax=axes[0])
    axes[0].axvline(threshold, color="#EF4444", linestyle="--", label="5% borderline cutoff")
    axes[0].legend()
    axes[0].set_title("Assignment Confidence Distribution")
    sample_diag = diagnostics.sample(min(20000, len(diagnostics)), random_state=seed)
    sns.scatterplot(data=sample_diag, x="distance_to_centroid", y="assignment_confidence", hue="cluster", alpha=.35, s=12, palette="tab10", ax=axes[1])
    axes[1].set_title("Distance-to-Centroid vs Confidence")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "cluster_ambiguity_analysis.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5), facecolor="white")
    sns.barplot(data=ablation, y="removed_feature", x="ari_vs_full_model", color="#7C3AED", ax=axes[0])
    axes[0].set_xlim(0, 1)
    axes[0].set_title("Ablation: Agreement with Full Model")
    sns.barplot(data=ablation, y="removed_feature", x="silhouette", color="#10B981", ax=axes[1])
    axes[1].set_title("Ablation: Silhouette after Feature Removal")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "feature_ablation_sensitivity.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor="white")
    sns.barplot(data=personas, x="persona_name", y="student_count", palette="bright", ax=ax)
    ax.tick_params(axis="x", rotation=18)
    ax.set_title("Cluster Size by Discovered Persona", fontweight="bold")
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "persona_cluster_sizes.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    print(f"[Extended Step 8] Model comparison: {MODEL_COMPARISON_PATH}")
    print(f"[Extended Step 8] Personas: {PERSONA_PATH}")
    print(f"[Extended Step 8] Ambiguity diagnostics: {AMBIGUITY_PATH}")
    print(f"[Extended Step 8] Simulator spec: {SIMULATOR_PATH}")


if __name__ == "__main__":
    main()
