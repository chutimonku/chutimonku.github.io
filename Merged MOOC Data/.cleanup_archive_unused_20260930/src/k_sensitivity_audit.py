"""Multi-seed sensitivity audit for the provisional unsupervised k choice.

This audit does not overwrite the deployed segmentation. It evaluates whether
the apparent k preference persists across random initializations and reports
uncertainty explicitly for the dashboard.
"""

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler


ROOT = Path(__file__).resolve().parents[1]
FEATURES = [
    "mean_course_forum_posts_percentile",
    "mean_course_chapters_percentile",
    "mean_course_active_days_percentile",
    "mean_course_events_percentile",
]
K_VALUES = range(2, 13)
SEEDS = (42, 143, 244)


def main() -> None:
    students = pd.read_parquet(ROOT / "data/processed/students_cleaned.parquet", columns=FEATURES)
    rng = np.random.default_rng(42)
    sample_idx = rng.choice(len(students), min(50_000, len(students)), replace=False)
    sample = students.iloc[sample_idx]
    transform = make_pipeline(SimpleImputer(strategy="median"), RobustScaler())
    values = transform.fit_transform(sample)
    train_idx, eval_idx = train_test_split(np.arange(len(values)), test_size=10_000, random_state=42)
    train, evaluation = values[train_idx], values[eval_idx]

    run_rows = []
    stability_rows = []
    for k in K_VALUES:
        labels_by_seed = []
        for seed in SEEDS:
            model = MiniBatchKMeans(
                n_clusters=k, batch_size=2048, n_init=20, random_state=seed
            ).fit(train)
            labels = model.predict(evaluation)
            labels_by_seed.append(labels)
            shares = np.bincount(labels, minlength=k) / len(labels) * 100
            run_rows.append({
                "k": k,
                "seed": seed,
                "inertia": float(model.inertia_),
                "silhouette": silhouette_score(evaluation, labels, sample_size=3000, random_state=seed),
                "davies_bouldin": davies_bouldin_score(evaluation, labels),
                "calinski_harabasz": calinski_harabasz_score(evaluation, labels),
                "smallest_cluster_pct": shares.min(),
                "smallest_cluster_check": bool(shares.min() >= 0.25),
            })
        pairwise = [adjusted_rand_score(labels_by_seed[a], labels_by_seed[b]) for a, b in combinations(range(len(SEEDS)), 2)]
        pairwise_nmi = [normalized_mutual_info_score(labels_by_seed[a], labels_by_seed[b]) for a, b in combinations(range(len(SEEDS)), 2)]
        stability_rows.append({
            "k": k,
            "pairwise_seed_ari_mean": float(np.mean(pairwise)),
            "pairwise_seed_ari_std": float(np.std(pairwise, ddof=1)),
            "pairwise_seed_nmi_mean": float(np.mean(pairwise_nmi)),
            "pairwise_seed_nmi_std": float(np.std(pairwise_nmi, ddof=1)),
        })

    detailed = pd.DataFrame(run_rows)
    summary = detailed.groupby("k", as_index=False).agg(
        silhouette_mean=("silhouette", "mean"),
        silhouette_std=("silhouette", "std"),
        davies_bouldin_mean=("davies_bouldin", "mean"),
        davies_bouldin_std=("davies_bouldin", "std"),
        calinski_harabasz_mean=("calinski_harabasz", "mean"),
        calinski_harabasz_std=("calinski_harabasz", "std"),
        smallest_cluster_pct_mean=("smallest_cluster_pct", "mean"),
        smallest_cluster_pct_std=("smallest_cluster_pct", "std"),
        smallest_cluster_check_rate=("smallest_cluster_check", "mean"),
    ).merge(pd.DataFrame(stability_rows), on="k", validate="one_to_one")
    manifest_path = ROOT / "outputs/reproducibility/unsupervised_track_manifest.json"
    selected_k = 3
    if manifest_path.exists():
        selected_k = int(json.loads(manifest_path.read_text(encoding="utf-8")).get("selected_k", selected_k))
    summary["is_current_operational_k"] = summary["k"].eq(selected_k)
    summary["audit_interpretation"] = np.select(
        [summary["k"].eq(selected_k)],
        [
            f"Selected k={selected_k}; highest weighted six-metric composite score in the current run",
        ],
        default="Not selected in the current weighted six-metric decision",
    )
    tables = ROOT / "outputs/tables"
    detailed.to_csv(tables / "k_sensitivity_multiseed_runs.csv", index=False)
    summary.to_csv(tables / "k_sensitivity_multiseed_audit.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
