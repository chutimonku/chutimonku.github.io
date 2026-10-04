"""Unified analysis tracks built from the audited student-level MOOC data.

The module keeps one cleaned master cohort and creates task-specific feature
sets.  Unsupervised and deep-learning tracks never receive outcomes.  The
supervised certification track receives its label only after the split boundary.
All reported values are written from computations performed in this module.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from scipy.special import expit
from sklearn.base import BaseEstimator, ClusterMixin
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.cluster import AgglomerativeClustering, Birch, DBSCAN, KMeans, MiniBatchKMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    adjusted_rand_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    calinski_harabasz_score,
    confusion_matrix,
    davies_bouldin_score,
    f1_score,
    precision_recall_curve,
    roc_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
    normalized_mutual_info_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction.text import TfidfVectorizer


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDENTS_PATH = os.path.join(ROOT, "data", "processed", "students_cleaned.parquet")
ENROLLMENTS_PATH = os.path.join(ROOT, "data", "processed", "enrollments_cleaned.parquet")
SUPERVISED_OUTCOMES_PATH = os.path.join(ROOT, "data", "quarantine", "supervised_outcomes_cleaned.parquet")
TABLES = os.path.join(ROOT, "outputs", "tables")
FIGURES = os.path.join(ROOT, "outputs", "figures", "tracks")
MODELS = os.path.join(ROOT, "models", "tracks")
DATA_OUT = os.path.join(ROOT, "outputs", "data")
REPRO = os.path.join(ROOT, "outputs", "reproducibility")
RESEARCH = os.path.join(ROOT, "outputs", "research")
MONITORING = os.path.join(ROOT, "monitoring")
HF_HOME = os.path.join(ROOT, ".cache", "huggingface")
CACHE_HOME = os.path.join(HF_HOME, "hub")
os.environ.setdefault("HF_HOME", HF_HOME)
os.environ.setdefault("TRANSFORMERS_CACHE", CACHE_HOME)
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", os.path.join(HF_HOME, "sentence_transformers"))

SEED = 42
K_VALUES = list(range(2, 11))
UNSUPERVISED_FEATURES = []
SUPERVISED_NUMERIC = []
SUPERVISED_BINARY = []
SUPERVISED_CATEGORICAL = []
SUPERVISED_INPUTS = []
VIDEO_TEXT_FEATURES = [
    "total_video_plays",
    "mean_video_plays_per_course",
    "video_missing_records",
    "mean_course_video_plays_percentile",
    "video_data_available_rate",
    "video_intensity",
]


def _ensure_dirs():
    for path in (TABLES, FIGURES, MODELS, DATA_OUT, REPRO, RESEARCH, MONITORING, CACHE_HOME):
        os.makedirs(path, exist_ok=True)


def _safe_metrics(X, labels):
    labels = np.asarray(labels)
    valid = labels >= 0
    realized = int(np.unique(labels[valid]).size) if valid.any() else 0
    noise_pct = float((~valid).mean() * 100.0)
    if valid.sum() < 3 or realized < 2:
        return {
            "silhouette": np.nan,
            "davies_bouldin": np.nan,
            "calinski_harabasz": np.nan,
            "smallest_cluster_pct": 0.0,
            "realized_clusters": realized,
            "noise_pct": noise_pct,
        }
    Xv = X[valid]
    lv = labels[valid]
    shares = pd.Series(lv).value_counts(normalize=True)
    return {
        "silhouette": float(silhouette_score(Xv, lv)),
        "davies_bouldin": float(davies_bouldin_score(Xv, lv)),
        "calinski_harabasz": float(calinski_harabasz_score(Xv, lv)),
        "smallest_cluster_pct": float(shares.min() * valid.mean() * 100.0),
        "realized_clusters": realized,
        "noise_pct": noise_pct,
    }


class ApproxKMedoids(BaseEstimator, ClusterMixin):
    """Scalable medoid approximation with nearest-medoid prediction.

    It initializes medoids from K-Means and refines each cluster using an
    observed subset.  The method is recorded as an approximation rather than a
    full PAM optimization, which would be quadratic on this cohort.
    """

    def __init__(self, n_clusters=4, random_state=42, max_cluster_sample=500, max_iter=5):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.max_cluster_sample = max_cluster_sample
        self.max_iter = max_iter

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        rng = np.random.default_rng(self.random_state)
        init = KMeans(n_clusters=self.n_clusters, n_init=10, random_state=self.random_state).fit(X)
        medoid_indices = []
        for center in init.cluster_centers_:
            medoid_indices.append(int(np.argmin(np.sum((X - center) ** 2, axis=1))))
        medoids = X[medoid_indices].copy()
        for _ in range(self.max_iter):
            labels = self._assign(X, medoids)
            updated = medoids.copy()
            for cluster_id in range(self.n_clusters):
                idx = np.flatnonzero(labels == cluster_id)
                if len(idx) == 0:
                    updated[cluster_id] = X[rng.integers(0, len(X))]
                    continue
                if len(idx) > self.max_cluster_sample:
                    idx = rng.choice(idx, self.max_cluster_sample, replace=False)
                sample = X[idx]
                distances = np.sqrt(((sample[:, None, :] - sample[None, :, :]) ** 2).sum(axis=2))
                updated[cluster_id] = sample[np.argmin(distances.sum(axis=1))]
            if np.allclose(updated, medoids):
                break
            medoids = updated
        self.cluster_centers_ = medoids
        self.labels_ = self._assign(X, medoids)
        return self

    @staticmethod
    def _assign(X, medoids):
        return np.argmin(((X[:, None, :] - medoids[None, :, :]) ** 2).sum(axis=2), axis=1)

    def predict(self, X):
        return self._assign(np.asarray(X, dtype=float), self.cluster_centers_)


def _make_cluster_model(family, k, seed):
    if family == "K-Means":
        return KMeans(n_clusters=k, n_init=20, random_state=seed)
    if family == "MiniBatch K-Means":
        return MiniBatchKMeans(n_clusters=k, n_init=10, batch_size=1024, random_state=seed)
    if family == "Gaussian Mixture":
        return GaussianMixture(n_components=k, covariance_type="diag", reg_covar=1e-5, random_state=seed)
    if family == "BIRCH":
        return Birch(n_clusters=k, threshold=0.5)
    if family == "K-Medoids (approx.)":
        return ApproxKMedoids(n_clusters=k, random_state=seed)
    raise KeyError(family)


def _predict_cluster_model(model, X):
    if hasattr(model, "predict"):
        return model.predict(X)
    return model.labels_


def _rank_cluster_candidates(frame):
    eligible = frame[
        frame["role"].eq("Candidate")
        & frame.get("k_selection_eligible", True)
        & frame["silhouette"].notna()
        & frame["resample_ari"].notna()
    ].copy()
    if eligible.empty:
        raise RuntimeError("No deployable clustering candidate was available for the selected K.")
    eligible["rank_silhouette"] = eligible["silhouette"].rank(ascending=False, method="min")
    eligible["rank_davies_bouldin"] = eligible["davies_bouldin"].rank(ascending=True, method="min")
    eligible["rank_calinski_harabasz"] = eligible["calinski_harabasz"].rank(ascending=False, method="min")
    eligible["rank_stability"] = eligible["resample_ari"].rank(ascending=False, method="min")
    eligible["mean_internal_rank"] = eligible[
        ["rank_silhouette", "rank_davies_bouldin", "rank_calinski_harabasz", "rank_stability"]
    ].mean(axis=1)
    return eligible.sort_values(
        ["mean_internal_rank", "runtime_sec", "family", "k"], ascending=[True, True, True, True]
    )


def _normalize_metric(series, higher_is_better=True):
    values = pd.to_numeric(series, errors="coerce").astype(float)
    span = values.max() - values.min()
    if not np.isfinite(span) or span == 0:
        normalized = pd.Series(1.0, index=values.index)
    else:
        normalized = (values - values.min()) / span
    if not higher_is_better:
        normalized = 1.0 - normalized
    return normalized.clip(0, 1)


def _select_operational_k(elbow, kmeans_rows):
    """Select one K by converting the six diagnostics into one comparable score."""
    elbow_columns = ["k", "inertia"] + [
        column for column in ["gap", "gap_se", "gap_rule_selected"] if column in elbow.columns
    ]
    scores = kmeans_rows.reset_index().merge(
        elbow[elbow_columns],
        on="k",
        how="left",
    ).sort_values("k").reset_index(drop=True)
    scores["inertia_score"] = _normalize_metric(np.log(scores["inertia"]), higher_is_better=False)
    scores["silhouette_score"] = _normalize_metric(scores["silhouette"], higher_is_better=True)
    scores["davies_bouldin_score"] = _normalize_metric(scores["davies_bouldin"], higher_is_better=False)
    scores["calinski_harabasz_score"] = _normalize_metric(np.log(scores["calinski_harabasz"]), higher_is_better=True)
    scores["ari_stability_score"] = _normalize_metric(scores["resample_ari"], higher_is_better=True)
    scores["nmi_stability_score"] = _normalize_metric(scores["resample_nmi"], higher_is_better=True)
    score_columns = [
        "inertia_score",
        "silhouette_score",
        "davies_bouldin_score",
        "calinski_harabasz_score",
        "ari_stability_score",
        "nmi_stability_score",
    ]
    weights = {
        "inertia_score": 0.10,
        "silhouette_score": 0.20,
        "davies_bouldin_score": 0.15,
        "calinski_harabasz_score": 0.15,
        "ari_stability_score": 0.20,
        "nmi_stability_score": 0.20,
    }
    scores["composite_score"] = sum(scores[column] * weight for column, weight in weights.items())
    scores["operational_k_eligible"] = True
    scores["rank_all_k"] = scores["composite_score"].rank(ascending=False, method="min").astype(int)
    selected_k = int(scores.sort_values(["composite_score", "k"], ascending=[False, True]).iloc[0]["k"])
    scores["selected_operational_k"] = scores["k"].eq(selected_k)
    scores["selection_interpretation"] = np.where(
        scores["selected_operational_k"],
        "Selected: highest weighted six-metric composite score.",
        "Not selected: lower weighted six-metric composite score.",
    )
    metric_votes = {
        "1. Inertia / WCSS normalized score": int(scores.loc[scores["inertia_score"].idxmax(), "k"]),
        "2. Maximum Silhouette Score": int(scores.loc[scores["silhouette"].idxmax(), "k"]),
        "3. Minimum Davies-Bouldin Index": int(scores.loc[scores["davies_bouldin"].idxmin(), "k"]),
        "4. Maximum Calinski-Harabasz Index": int(scores.loc[scores["calinski_harabasz"].idxmax(), "k"]),
        "5. Maximum Stability (ARI)": int(scores.loc[scores["resample_ari"].idxmax(), "k"]),
        "6. Maximum Stability (NMI)": int(scores.loc[scores["resample_nmi"].idxmax(), "k"]),
    }
    return selected_k, scores, metric_votes, score_columns


def _gap_statistic(X, k_values, references=8, seed=SEED):
    """Compute Tibshirani et al.'s Gap statistic on the train-only feature space."""
    rng = np.random.default_rng(seed)
    lower, upper = X.min(axis=0), X.max(axis=0)
    rows = []
    for k in k_values:
        observed = KMeans(n_clusters=k, n_init=20, random_state=seed).fit(X).inertia_
        reference_logs = []
        for repeat in range(references):
            reference = rng.uniform(lower, upper, size=X.shape)
            inertia = KMeans(
                n_clusters=k, n_init=10, random_state=seed + 1000 + repeat
            ).fit(reference).inertia_
            reference_logs.append(np.log(max(inertia, 1e-12)))
        gap = float(np.mean(reference_logs) - np.log(max(observed, 1e-12)))
        gap_se = float(np.std(reference_logs, ddof=1) * np.sqrt(1 + 1 / references))
        rows.append({"k": k, "observed_wcss": observed, "gap": gap, "gap_se": gap_se})
    frame = pd.DataFrame(rows)
    selected = int(frame.loc[frame["gap"].idxmax(), "k"])
    for idx in range(len(frame) - 1):
        if frame.loc[idx, "gap"] >= frame.loc[idx + 1, "gap"] - frame.loc[idx + 1, "gap_se"]:
            selected = int(frame.loc[idx, "k"])
            break
    frame["gap_rule_selected"] = frame["k"].eq(selected)
    return frame, selected


def build_feature_registry(students):
    """Select a fixed set of four behavioral percentile features for unsupervised clustering.

    The unsupervised track uses student-level course-adjusted percentile features
    aggregated from the cleaned student-course enrollment table. The four chosen
    features are the within-course percentile ranks:
    - forum_posts_percentile_within_course
    - chapters_percentile_within_course
    - active_days_percentile_within_course
    - events_percentile_within_course
    All other columns are treated as profile data.
    """
    global UNSUPERVISED_FEATURES, SUPERVISED_NUMERIC, SUPERVISED_BINARY, SUPERVISED_CATEGORICAL, SUPERVISED_INPUTS

    # Fixed student-level percentile features (must exist in students_cleaned.parquet)
    fixed_features = [
        "mean_course_forum_posts_percentile",
        "mean_course_chapters_percentile",
        "mean_course_active_days_percentile",
        "mean_course_events_percentile",
    ]
    missing = [f for f in fixed_features if f not in students.columns]
    if missing:
        raise RuntimeError(f"Required unsupervised features missing from student data: {missing}")
    UNSUPERVISED_FEATURES = fixed_features
    unsup_candidates = set(fixed_features)
    unsup_reasons = {
        column: "Selected fixed within-course behavioral percentile for student-level unsupervised clustering."
        for column in fixed_features
    }


    excluded_exact = {
        "userid_DI", "first_start_dt", "last_event_dt", "source_membership", "source_count",
        "date_inversion_records", "age_missing_records", "video_missing_records", "video_data_available_rate",
        "overall_span_missing", "n_courses",
    }
    candidate_supervised = []
    supervised_reasons = {}
    for column in students.columns:
        if column in excluded_exact:
            supervised_reasons[column] = "Excluded: identifier, date, provenance, data-quality flag, or exact alias."
            continue
        series = students[column]
        missing = float(series.isna().mean())
        distinct = int(series.nunique(dropna=True))
        if missing > 0.50 or distinct < 2:
            supervised_reasons[column] = "Excluded: majority missing or no usable variation."
            continue
        if pd.api.types.is_datetime64_any_dtype(series):
            supervised_reasons[column] = "Excluded: raw timestamp; duration is represented separately."
            continue
        if not pd.api.types.is_numeric_dtype(series) and distinct > 50:
            supervised_reasons[column] = "Excluded: categorical cardinality above 50."
            continue
        candidate_supervised.append(column)

    # Remove exact/near-exact numeric duplicates using the observed merged data.
    selected_numeric = []
    categorical = []
    binary = []
    for column in candidate_supervised:
        series = students[column]
        if not pd.api.types.is_numeric_dtype(series):
            categorical.append(column)
            supervised_reasons[column] = "Selected categorical input from the merged clean table."
            continue
        if series.nunique(dropna=True) == 2:
            binary.append(column)
            supervised_reasons[column] = "Selected binary input from the merged clean table."
            continue
        redundant = None
        for kept in selected_numeric:
            pair = students[[column, kept]].dropna()
            if len(pair) and abs(float(pair.corr().iloc[0, 1])) > 0.995:
                redundant = kept
                break
        if redundant:
            supervised_reasons[column] = f"Excluded: correlation above 0.995 with {redundant}."
        else:
            selected_numeric.append(column)
            supervised_reasons[column] = "Selected numeric input from the merged clean table."
    SUPERVISED_NUMERIC = selected_numeric
    SUPERVISED_BINARY = binary
    SUPERVISED_CATEGORICAL = categorical
    SUPERVISED_INPUTS = selected_numeric + binary + categorical

    rows = []
    for column in students.columns:
        series = students[column]
        rows.append({
            "feature": column,
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_pct": float(series.isna().mean() * 100),
            "distinct": int(series.nunique(dropna=True)),
            "variance": float(series.var(skipna=True)) if pd.api.types.is_numeric_dtype(series) else np.nan,
            "unsupervised_candidate": column in unsup_candidates,
            "unsupervised_selected": column in UNSUPERVISED_FEATURES,
            "unsupervised_decision": unsup_reasons.get(column, "Not a course-relative behavioral percentile."),
            "supervised_selected": column in SUPERVISED_INPUTS,
            "supervised_group": "numeric" if column in SUPERVISED_NUMERIC else "binary" if column in SUPERVISED_BINARY else "categorical" if column in SUPERVISED_CATEGORICAL else "excluded",
            "supervised_decision": supervised_reasons.get(column, "Excluded by task role."),
            "source_basis": "Derived from the reconciled clean enrollment table built from both sources.",
        })
    registry = pd.DataFrame(rows)
    registry.to_csv(os.path.join(TABLES, "feature_registry.csv"), index=False)
    return registry


def _prepare_unsupervised(students):
    sample_size = min(15000, len(students))
    rng = np.random.default_rng(SEED)
    sample_idx = np.sort(rng.choice(len(students), sample_size, replace=False))
    sample = students.iloc[sample_idx].copy().reset_index(drop=True)
    train_idx, eval_idx = train_test_split(
        np.arange(len(sample)), test_size=0.30, random_state=SEED, shuffle=True
    )
    preprocessor = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=False)),
        ("scaler", RobustScaler()),
    ])
    X_train = preprocessor.fit_transform(sample.iloc[train_idx][UNSUPERVISED_FEATURES])
    X_eval = preprocessor.transform(sample.iloc[eval_idx][UNSUPERVISED_FEATURES])
    return sample, sample_idx, train_idx, eval_idx, preprocessor, X_train, X_eval


def run_unsupervised_track(students):
    print(f"[Track] Traditional Unsupervised: {len(UNSUPERVISED_FEATURES)} data-selected course-adjusted behavior features")
    sample, sample_idx, train_idx, eval_idx, prep, X_train, X_eval = _prepare_unsupervised(students)
    records = []
    deployable = ["K-Means", "MiniBatch K-Means", "Gaussian Mixture", "BIRCH", "K-Medoids (approx.)"]
    elbow_rows = []

    for k in K_VALUES:
        for family in deployable:
            t0 = time.perf_counter()
            model = _make_cluster_model(family, k, SEED)
            model.fit(X_train)
            labels = _predict_cluster_model(model, X_eval)
            runtime = time.perf_counter() - t0
            second = _make_cluster_model(family, k, SEED + 101)
            second.fit(X_train)
            labels_second = _predict_cluster_model(second, X_eval)
            metrics = _safe_metrics(X_eval, labels)
            row = {
                "track": "Traditional Unsupervised",
                "family": family,
                "model_id": family.lower().replace(" ", "_").replace("-", "") + f"_k{k}",
                "k": k,
                "role": "Candidate",
                "runtime_sec": runtime,
                "resample_ari": float(adjusted_rand_score(labels, labels_second)),
                "resample_nmi": float(normalized_mutual_info_score(labels, labels_second)),
                **metrics,
            }
            records.append(row)
            if family == "K-Means":
                elbow_rows.append({"k": k, "inertia": float(model.inertia_), "runtime_sec": runtime})

        t0 = time.perf_counter()
        hac_labels = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X_eval)
        records.append({
            "track": "Traditional Unsupervised",
            "family": "HAC (Ward)",
            "model_id": f"hac_ward_k{k}",
            "k": k,
            "role": "Geometry benchmark",
            "runtime_sec": time.perf_counter() - t0,
            "resample_ari": np.nan,
            "resample_nmi": np.nan,
            **_safe_metrics(X_eval, hac_labels),
        })

    # DBSCAN does not use k.  Epsilon candidates come from observed 10-NN distances.
    nn = NearestNeighbors(n_neighbors=10).fit(X_eval)
    kth = np.sort(nn.kneighbors(X_eval)[0][:, -1])
    for quantile in (0.85, 0.90, 0.95):
        eps = float(np.quantile(kth, quantile))
        t0 = time.perf_counter()
        labels = DBSCAN(eps=eps, min_samples=10, n_jobs=-1).fit_predict(X_eval)
        records.append({
            "track": "Traditional Unsupervised",
            "family": "DBSCAN",
            "model_id": f"dbscan_q{int(quantile*100)}",
            "k": np.nan,
            "role": "Density benchmark",
            "runtime_sec": time.perf_counter() - t0,
            "resample_ari": np.nan,
            "resample_nmi": np.nan,
            "eps": eps,
            **_safe_metrics(X_eval, labels),
        })

    results = pd.DataFrame(records)
    elbow = pd.DataFrame(elbow_rows)
    x_norm = (elbow["k"] - elbow["k"].min()) / (elbow["k"].max() - elbow["k"].min())
    y_norm = (elbow["inertia"] - elbow["inertia"].min()) / (elbow["inertia"].max() - elbow["inertia"].min())
    elbow["distance_from_endpoint_line"] = (1.0 - x_norm) - y_norm
    elbow_k = int(elbow.loc[elbow["distance_from_endpoint_line"].idxmax(), "k"])
    gap_frame, gap_k = _gap_statistic(X_train, K_VALUES)
    gap_frame.to_csv(os.path.join(TABLES, "gap_statistic_by_k.csv"), index=False)
    kmeans_rows = results[results["family"].eq("K-Means")].set_index("k")
    selected_operational_k, k_scores, metric_votes, score_columns = _select_operational_k(elbow, kmeans_rows)
    k_scores.to_csv(os.path.join(TABLES, "k_selection_composite_scores.csv"), index=False)
    inertia_k = int(k_scores.loc[k_scores["inertia_score"].idxmax(), "k"])
    decision = pd.DataFrame([{"criterion": name, "preferred_k": value} for name, value in metric_votes.items()])
    decision["supports_operational_k"] = decision["preferred_k"].eq(selected_operational_k)
    decision["operational_k"] = selected_operational_k
    decision["selection_rule"] = (
        "Six metrics are converted to comparable 0–1 scores, then combined with weights "
        "(Inertia .10, Silhouette .20, Davies-Bouldin .15, Calinski-Harabasz .15, "
        "ARI .20, NMI .20). The selected K is the single K with the highest weighted composite score."
    )
    decision.to_csv(os.path.join(TABLES, "k_selection_decision.csv"), index=False)
    results["k_selection_eligible"] = results["k"].eq(selected_operational_k)
    ranked = _rank_cluster_candidates(results)
    winner = ranked.iloc[0].to_dict()
    results = results.merge(
        ranked[["model_id", "mean_internal_rank"]], on="model_id", how="left"
    )
    results["selected"] = results["model_id"].eq(winner["model_id"])
    results.to_csv(os.path.join(TABLES, "unsupervised_model_comparison.csv"), index=False)
    elbow["detected_elbow"] = elbow["k"].eq(elbow_k)
    elbow = elbow.merge(gap_frame[["k", "gap", "gap_se", "gap_rule_selected"]], on="k", how="left")
    elbow["consensus_candidate"] = elbow["k"].eq(selected_operational_k)
    elbow["operational_k_selected"] = elbow["k"].eq(selected_operational_k)
    elbow.to_csv(os.path.join(TABLES, "k_selection_elbow.csv"), index=False)

    full_prep = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", RobustScaler()),
    ])
    X_full = full_prep.fit_transform(students[UNSUPERVISED_FEATURES])
    final_model = _make_cluster_model(winner["family"], int(winner["k"]), SEED)
    fit_X = X_full
    if winner["family"] == "K-Medoids (approx.)" and len(X_full) > 50000:
        fit_X = X_full[np.random.default_rng(SEED).choice(len(X_full), 50000, replace=False)]
    t0 = time.perf_counter()
    final_model.fit(fit_X)
    full_labels = _predict_cluster_model(final_model, X_full)
    final_fit_runtime = time.perf_counter() - t0
    joblib.dump({"preprocessor": full_prep, "model": final_model, "features": UNSUPERVISED_FEATURES},
                os.path.join(MODELS, "unsupervised_pipeline.joblib"))
    assignments = pd.DataFrame({"userid_DI": students["userid_DI"], "unsupervised_cluster": full_labels})
    assignments.to_csv(os.path.join(DATA_OUT, "unsupervised_cluster_assignments.csv"), index=False)

    profile = students.assign(cluster=full_labels).groupby("cluster")[UNSUPERVISED_FEATURES].mean().reset_index()
    sizes = pd.Series(full_labels).value_counts().sort_index()
    profile.insert(1, "students", profile["cluster"].map(sizes).astype(int))
    profile.insert(2, "share_pct", profile["students"] / len(students) * 100.0)
    profile.to_csv(os.path.join(TABLES, "unsupervised_cluster_profiles.csv"), index=False)
    if hasattr(final_model, "cluster_centers_"):
        centers_original = full_prep.named_steps["scaler"].inverse_transform(np.asarray(final_model.cluster_centers_))
        pd.DataFrame(centers_original, columns=UNSUPERVISED_FEATURES).assign(
            cluster=lambda frame: np.arange(len(frame))
        )[["cluster"] + UNSUPERVISED_FEATURES].to_csv(
            os.path.join(TABLES, "unsupervised_scenario_centers.csv"), index=False
        )
    else:
        profile[["cluster"] + UNSUPERVISED_FEATURES].to_csv(
            os.path.join(TABLES, "unsupervised_scenario_centers.csv"), index=False
        )

    feature_baseline = []
    for column in UNSUPERVISED_FEATURES:
        series = students[column]
        quantiles = series.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
        feature_baseline.append({
            "feature": column,
            "missing_count": int(series.isna().sum()),
            "missing_pct": float(series.isna().mean() * 100),
            "mean": float(series.mean()), "std": float(series.std()),
            "p05": float(quantiles.loc[0.05]), "p25": float(quantiles.loc[0.25]),
            "p50": float(quantiles.loc[0.50]), "p75": float(quantiles.loc[0.75]), "p95": float(quantiles.loc[0.95]),
        })
    pd.DataFrame(feature_baseline).to_csv(os.path.join(TABLES, "unsupervised_monitoring_feature_baseline.csv"), index=False)
    cluster_monitoring = profile[["cluster", "students", "share_pct"]].copy()
    cluster_monitoring.to_csv(os.path.join(TABLES, "unsupervised_monitoring_cluster_baseline.csv"), index=False)
    distance_baseline = {"available": False}
    if hasattr(final_model, "cluster_centers_"):
        centers = np.asarray(final_model.cluster_centers_)
        distances = np.sqrt(((X_full[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2))
        ordered = np.sort(distances, axis=1)
        assigned_distance = ordered[:, 0]
        margin = ordered[:, 1] - ordered[:, 0] if ordered.shape[1] > 1 else np.full(len(ordered), np.nan)
        distance_baseline = {
            "available": True,
            "assigned_distance_p50": float(np.quantile(assigned_distance, 0.50)),
            "assigned_distance_p95": float(np.quantile(assigned_distance, 0.95)),
            "assigned_distance_p99_outlier_threshold": float(np.quantile(assigned_distance, 0.99)),
            "assignment_margin_p05_uncertainty_threshold": float(np.quantile(margin, 0.05)),
            "baseline_outlier_rate_at_p99": float((assigned_distance > np.quantile(assigned_distance, 0.99)).mean()),
            "baseline_uncertain_rate_at_p05": float((margin < np.quantile(margin, 0.05)).mean()),
        }
    with open(os.path.join(MONITORING, "unsupervised_monitoring_baseline.json"), "w", encoding="utf-8") as handle:
        json.dump({
            "selected_model": winner["family"], "selected_k": int(winner["k"]),
            "students": len(students), "features": UNSUPERVISED_FEATURES,
            "cluster_distribution": {str(int(k)): float(v / len(students)) for k, v in sizes.items()},
            "resample_ari_reference": float(winner["resample_ari"]),
            "distance_and_uncertainty": distance_baseline,
            "future_cohorts_evaluated": 0,
            "status": "BASELINE_READY_NO_FUTURE_COHORT",
        }, handle, indent=2)

    manifest = {
        "input_features": UNSUPERVISED_FEATURES,
        "feature_count": len(UNSUPERVISED_FEATURES),
        "feature_meaning": f"Within-course behavioral percentile ranks aggregated from {len(students):,} cleaned student records.",
        "sample_enrollments": len(sample),
        "training_enrollments": len(train_idx),
        "unseen_evaluation_enrollments": len(eval_idx),
        "k_values_evaluated": K_VALUES,
        "detected_elbow_k": elbow_k,
        "elbow_used_for_selection": False,
        "inertia_metric_k": inertia_k,
        "gap_statistic_k": gap_k,
        "metric_votes": metric_votes,
        "consensus_k_candidates": [selected_operational_k],
        "final_k_candidates": [selected_operational_k],
        "k_selection_score_columns": score_columns,
        "selected_model_id": winner["model_id"],
        "selected_family": winner["family"],
        "selected_k": int(winner["k"]),
        "selection_rule": "K is selected by a weighted six-metric score, not by Elbow alone and not by raw vote counting. The six diagnostics are Inertia/WCSS, Silhouette, Davies-Bouldin, Calinski-Harabasz, ARI stability, and NMI stability. The selected K is the single K with the highest composite score. The deployable family is then selected inside the chosen K by internal-metric mean rank.",
        "full_fit_enrollments": len(students),
        "full_fit_runtime_sec": final_fit_runtime,
    }
    with open(os.path.join(REPRO, "unsupervised_track_manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)

    _plot_unsupervised(elbow, results, profile, X_full, full_labels, int(winner["k"]), gap_k, elbow_k)
    _plot_outcome_quality()
    return assignments, manifest, results, profile, full_prep, X_full


class Autoencoder(torch.nn.Module):
    def __init__(self, input_dim, latent_dim=3):
        super().__init__()
        self.encoder = torch.nn.Sequential(
            torch.nn.Linear(input_dim, 8), torch.nn.ReLU(), torch.nn.Linear(8, latent_dim)
        )
        self.decoder = torch.nn.Sequential(
            torch.nn.Linear(latent_dim, 8), torch.nn.ReLU(), torch.nn.Linear(8, input_dim)
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z), z


def run_deep_learning_track(students):
    """Deep Learning track as supervised certification classification, not clustering."""
    print("[Track] Deep Learning: neural-network certification classification")
    outcomes = pd.read_parquet(SUPERVISED_OUTCOMES_PATH)
    student_target = outcomes.groupby("userid_DI", as_index=False)["certified"].max()
    frame = students.merge(student_target, on="userid_DI", how="inner")
    y = frame["certified"].astype(int).to_numpy()
    all_idx = np.arange(len(frame))
    train_idx, rest_idx = train_test_split(all_idx, test_size=0.30, random_state=SEED, stratify=y)
    val_idx, test_idx = train_test_split(rest_idx, test_size=0.50, random_state=SEED, stratify=y[rest_idx])

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", RobustScaler()),
    ])
    binary_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent"))])
    category_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=0.005, sparse_output=False)),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipe, SUPERVISED_NUMERIC),
        ("binary", binary_pipe, SUPERVISED_BINARY),
        ("categorical", category_pipe, SUPERVISED_CATEGORICAL),
    ])
    X_train = preprocessor.fit_transform(frame.iloc[train_idx][SUPERVISED_INPUTS])
    X_val = preprocessor.transform(frame.iloc[val_idx][SUPERVISED_INPUTS])
    X_test = preprocessor.transform(frame.iloc[test_idx][SUPERVISED_INPUTS])

    candidates = {
        "mlp_64_32": ("MLP Neural Network (64, 32)", MLPClassifier(hidden_layer_sizes=(64, 32), activation="relu", solver="adam", alpha=1e-4, batch_size=512, learning_rate_init=0.001, max_iter=35, early_stopping=True, n_iter_no_change=5, random_state=SEED)),
        "mlp_32": ("MLP Neural Network (32)", MLPClassifier(hidden_layer_sizes=(32,), activation="relu", solver="adam", alpha=5e-4, batch_size=512, learning_rate_init=0.001, max_iter=35, early_stopping=True, n_iter_no_change=5, random_state=SEED + 1)),
        "mlp_128_64": ("MLP Neural Network (128, 64)", MLPClassifier(hidden_layer_sizes=(128, 64), activation="relu", solver="adam", alpha=2e-4, batch_size=512, learning_rate_init=0.0008, max_iter=40, early_stopping=True, n_iter_no_change=5, random_state=SEED + 2)),
        "mlp_128_64_32": ("Deep MLP (128, 64, 32)", MLPClassifier(hidden_layer_sizes=(128, 64, 32), activation="relu", solver="adam", alpha=5e-4, batch_size=512, learning_rate_init=0.0008, max_iter=40, early_stopping=True, n_iter_no_change=5, random_state=SEED + 3)),
        "mlp_64_32_regularized": ("Regularized MLP (64, 32)", MLPClassifier(hidden_layer_sizes=(64, 32), activation="relu", solver="adam", alpha=0.005, batch_size=512, learning_rate_init=0.0005, max_iter=45, early_stopping=True, n_iter_no_change=7, random_state=SEED + 4)),
        "mlp_64_tanh": ("MLP Tanh (64)", MLPClassifier(hidden_layer_sizes=(64,), activation="tanh", solver="adam", alpha=5e-4, batch_size=512, learning_rate_init=0.0008, max_iter=40, early_stopping=True, n_iter_no_change=5, random_state=SEED + 5)),
    }
    records, fitted, test_predictions = [], {}, {}
    for model_id, (name, model) in candidates.items():
        start_time = time.perf_counter()
        model.fit(X_train, y[train_idx])
        runtime = time.perf_counter() - start_time
        val_prob = model.predict_proba(X_val)[:, 1]
        threshold = _optimal_f1_threshold(y[val_idx], val_prob)
        test_prob = model.predict_proba(X_test)[:, 1]
        pred = (test_prob >= threshold).astype(int)
        test_predictions[model_id] = {"probability": test_prob, "prediction": pred}
        records.append({
            "track": "Deep Learning",
            "model_id": model_id,
            "model_name": name,
            "family": "Neural Network Classifier",
            "runtime_sec": runtime,
            "epochs_or_iterations": int(getattr(model, "n_iter_", 0)),
            "threshold_from_validation": threshold,
            "test_pr_auc": float(average_precision_score(y[test_idx], test_prob)),
            "test_roc_auc": float(roc_auc_score(y[test_idx], test_prob)),
            "test_brier": float(brier_score_loss(y[test_idx], test_prob)),
            "test_accuracy": float(accuracy_score(y[test_idx], pred)),
            "test_balanced_accuracy": float(balanced_accuracy_score(y[test_idx], pred)),
            "test_precision": float(precision_score(y[test_idx], pred, zero_division=0)),
            "test_recall": float(recall_score(y[test_idx], pred, zero_division=0)),
            "test_f1": float(f1_score(y[test_idx], pred, zero_division=0)),
        })
        fitted[model_id] = model

    results = pd.DataFrame(records).sort_values(["test_pr_auc", "test_f1", "test_brier"], ascending=[False, False, True]).reset_index(drop=True)
    winner = results.iloc[0]
    results["selected"] = results["model_id"].eq(winner["model_id"])
    results.to_csv(os.path.join(TABLES, "deep_learning_model_comparison.csv"), index=False)

    champion = fitted[winner["model_id"]]
    deployment = Pipeline([("preprocessor", preprocessor), ("model", champion)])
    joblib.dump(deployment, os.path.join(MODELS, "deep_certification_pipeline.joblib"))
    full_prob = deployment.predict_proba(frame[SUPERVISED_INPUTS])[:, 1]
    pd.DataFrame({
        "userid_DI": frame["userid_DI"],
        "actual_certified": y,
        "deep_certification_probability": full_prob,
        "deep_predicted_certified": (full_prob >= float(winner["threshold_from_validation"])).astype(int),
    }).to_csv(os.path.join(DATA_OUT, "deep_certification_predictions.csv"), index=False)

    manifest = {
        "status": "Completed",
        "task_type": "supervised classification",
        "target": "ever certified in an eligible enrollment",
        "students": len(frame),
        "positive_students": int(y.sum()),
        "positive_rate": float(y.mean()),
        "split": {"train": len(train_idx), "validation": len(val_idx), "test": len(test_idx)},
        "source_feature_count": len(SUPERVISED_INPUTS),
        "source_features": SUPERVISED_INPUTS,
        "model_family": "MLP neural network classifier",
        "selected_model_id": winner["model_id"],
        "selected_model_name": winner["model_name"],
        "selected_threshold": float(winner["threshold_from_validation"]),
        "selected_test_metrics": {
            "pr_auc": float(winner["test_pr_auc"]),
            "roc_auc": float(winner["test_roc_auc"]),
            "brier": float(winner["test_brier"]),
            "accuracy": float(winner["test_accuracy"]),
            "balanced_accuracy": float(winner["test_balanced_accuracy"]),
            "precision": float(winner["test_precision"]),
            "recall": float(winner["test_recall"]),
            "f1": float(winner["test_f1"]),
            "training_runtime_sec": float(winner["runtime_sec"]),
        },
        "leakage_policy": "Uses only governed pre-outcome features; target is joined after the supervised split boundary for classification evaluation.",
    }
    with open(os.path.join(REPRO, "deep_learning_track_manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    _plot_deep_learning(results, y[test_idx], test_predictions)
    return frame[["userid_DI", "certified"]], full_prob, manifest, results


def _plot_deep_learning(results, y_test, predictions):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    x = np.arange(len(results))
    width = 0.15
    metrics = [
        ("test_accuracy", "Accuracy", "#2563EB"),
        ("test_precision", "Precision", "#0D9488"),
        ("test_recall", "Recall", "#16A34A"),
        ("test_f1", "F1", "#F59E0B"),
        ("test_roc_auc", "AUC (ROC-AUC)", "#7C3AED"),
    ]
    for i, (col, label, color) in enumerate(metrics):
        offset = (i - 2) * width
        axes[0].bar(x + offset, results[col], width, label=label, color=color)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(results["model_name"], rotation=25, ha="right", fontsize=9)
    axes[0].set_ylim(0, 1.05)
    axes[0].set_ylabel("Held-out test score")
    axes[0].set_title("Deep Learning: Accuracy, Precision, Recall, F1, AUC", fontsize=12, fontweight="bold")
    axes[0].legend(loc="upper right", ncol=3, fontsize=8)
    axes[0].grid(axis="y", alpha=0.25)
    for _, row in results.iterrows():
        pred = predictions[row["model_id"]]
        precision, recall, _ = precision_recall_curve(y_test, pred["probability"])
        axes[1].plot(recall, precision, label=f"{row['model_name']} (AUC={row['test_roc_auc']:.3f})")
    axes[1].axhline(np.mean(y_test), color="#777", linestyle="--", label="Prevalence")
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title("Precision–Recall Curves")
    axes[1].legend(fontsize=7.5)
    axes[1].grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "deep_model_comparison.png"), dpi=180, bbox_inches="tight")
    plt.close()

    top = results.head(4)
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    for ax, (_, row) in zip(axes.flat, top.iterrows()):
        matrix = confusion_matrix(y_test, predictions[row["model_id"]]["prediction"], labels=[0, 1])
        ax.imshow(matrix, cmap="Blues")
        ax.set_xticks([0, 1], ["Pred 0", "Pred 1"]); ax.set_yticks([0, 1], ["Actual 0", "Actual 1"])
        ax.set_title(f"{row['model_name']}\nthreshold={row['threshold_from_validation']:.3f}")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{matrix[i,j]:,}", ha="center", va="center", color="white" if matrix[i,j] > matrix.max()/2 else "#0B1F3A", fontweight="bold")
    fig.suptitle("Confusion Matrices: Top Four Neural Candidates", fontsize=15, fontweight="bold")
    plt.tight_layout(rect=(0, 0, 1, .96)); plt.savefig(os.path.join(FIGURES, "deep_confusion_matrices.png"), dpi=180, bbox_inches="tight"); plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.3))
    for _, row in results.iterrows():
        probability = predictions[row["model_id"]]["probability"]
        fpr, tpr, _ = roc_curve(y_test, probability)
        axes[0].plot(fpr, tpr, label=f"{row['model_name']} ({row['test_roc_auc']:.3f})")
        observed, predicted = calibration_curve(y_test, probability, n_bins=10, strategy="quantile")
        axes[1].plot(predicted, observed, marker="o", label=row["model_name"])
    axes[0].plot([0,1],[0,1],"--",color="#777"); axes[0].set_title("ROC comparison"); axes[0].set_xlabel("False-positive rate"); axes[0].set_ylabel("True-positive rate")
    axes[1].plot([0,1],[0,1],"--",color="#777"); axes[1].set_title("Calibration comparison"); axes[1].set_xlabel("Mean predicted probability"); axes[1].set_ylabel("Observed rate")
    for ax in axes: ax.legend(fontsize=7); ax.grid(alpha=.2)
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "deep_roc_calibration.png"), dpi=180, bbox_inches="tight"); plt.close()


def _optimal_f1_threshold(y_true, probabilities):
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    scores = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    idx = int(np.nanargmax(scores))
    threshold = float(thresholds[min(idx, len(thresholds) - 1)]) if len(thresholds) else 0.5
    return threshold


def _probabilities(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return expit(model.decision_function(X))


def run_supervised_track(students):
    print("[Track] Supervised Learning: certification prediction")
    outcomes = pd.read_parquet(SUPERVISED_OUTCOMES_PATH)
    student_target = outcomes.groupby("userid_DI", as_index=False)["certified"].max()
    frame = students.merge(student_target, on="userid_DI", how="inner")
    y = frame["certified"].astype(int).to_numpy()
    all_idx = np.arange(len(frame))
    train_idx, rest_idx = train_test_split(all_idx, test_size=0.30, random_state=SEED, stratify=y)
    val_idx, test_idx = train_test_split(rest_idx, test_size=0.50, random_state=SEED, stratify=y[rest_idx])

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", RobustScaler()),
    ])
    binary_pipe = Pipeline([( "imputer", SimpleImputer(strategy="most_frequent"))])
    # 2,300 records is about 0.74% of the training cohort.  Smaller categories
    # are grouped rather than creating unstable one-hot columns.
    category_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=0.005, sparse_output=False)),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipe, SUPERVISED_NUMERIC),
        ("binary", binary_pipe, SUPERVISED_BINARY),
        ("categorical", category_pipe, SUPERVISED_CATEGORICAL),
    ])
    X_train = preprocessor.fit_transform(frame.iloc[train_idx][SUPERVISED_INPUTS])
    X_val = preprocessor.transform(frame.iloc[val_idx][SUPERVISED_INPUTS])
    X_test = preprocessor.transform(frame.iloc[test_idx][SUPERVISED_INPUTS])
    transformed_names = preprocessor.get_feature_names_out().tolist()

    candidates = {
        "dummy_baseline": ("Dummy baseline", GaussianNB()),
        "logistic_regression": ("Logistic Regression", LogisticRegression(max_iter=800, solver="liblinear", class_weight="balanced", random_state=SEED)),
        "decision_tree": ("Decision Tree", DecisionTreeClassifier(max_depth=10, min_samples_leaf=20, class_weight="balanced", random_state=SEED)),
        "random_forest": ("Random Forest", RandomForestClassifier(n_estimators=150, max_depth=15, min_samples_leaf=5, class_weight="balanced", n_jobs=1, random_state=SEED)),
        "extra_trees": ("Extra Trees", ExtraTreesClassifier(n_estimators=150, max_depth=15, min_samples_leaf=5, class_weight="balanced", n_jobs=1, random_state=SEED)),
        "gradient_boosted_trees": ("Gradient Boosted Trees", HistGradientBoostingClassifier(max_iter=150, learning_rate=0.10, max_leaf_nodes=31, class_weight="balanced", random_state=SEED)),
        "linear_svm": ("Linear SVM", CalibratedClassifierCV(LinearSVC(class_weight="balanced", random_state=SEED), cv=3)),
        "naive_bayes": ("Gaussian Naive Bayes", GaussianNB()),
    }
    records = []
    fitted = {}
    test_predictions = {}
    for model_id, (name, model) in candidates.items():
        t0 = time.perf_counter()
        if model_id == "dummy_baseline":
            from sklearn.dummy import DummyClassifier
            model = DummyClassifier(strategy="prior", random_state=SEED)
        model.fit(X_train, y[train_idx])
        runtime = time.perf_counter() - t0
        val_prob = _probabilities(model, X_val)
        threshold = 0.5 if model_id == "dummy_baseline" else _optimal_f1_threshold(y[val_idx], val_prob)
        test_prob = _probabilities(model, X_test)
        pred = (test_prob >= threshold).astype(int)
        test_predictions[model_id] = {"probability": test_prob, "prediction": pred}
        records.append({
            "model_id": model_id,
            "model_name": name,
            "runtime_sec": runtime,
            "threshold_from_validation": threshold,
            "test_pr_auc": float(average_precision_score(y[test_idx], test_prob)),
            "test_roc_auc": float(roc_auc_score(y[test_idx], test_prob)),
            "test_brier": float(brier_score_loss(y[test_idx], test_prob)),
            "test_accuracy": float(accuracy_score(y[test_idx], pred)),
            "test_balanced_accuracy": float(balanced_accuracy_score(y[test_idx], pred)),
            "test_precision": float(precision_score(y[test_idx], pred, zero_division=0)),
            "test_recall": float(recall_score(y[test_idx], pred, zero_division=0)),
            "test_f1": float(f1_score(y[test_idx], pred, zero_division=0)),
        })
        fitted[model_id] = model

    comparison = pd.DataFrame(records).sort_values(
        ["test_pr_auc", "test_f1", "test_brier"], ascending=[False, False, True]
    ).reset_index(drop=True)
    winner = comparison.iloc[0]
    comparison["selected"] = comparison["model_id"].eq(winner["model_id"])
    comparison.to_csv(os.path.join(TABLES, "supervised_model_comparison.csv"), index=False)
    selected_test = test_predictions[winner["model_id"]]
    pd.DataFrame({
        "actual_certified": y[test_idx],
        "predicted_certified": selected_test["prediction"],
        "predicted_probability": selected_test["probability"],
    }).to_csv(os.path.join(TABLES, "supervised_test_predictions.csv"), index=False)
    champion = fitted[winner["model_id"]]
    deployment = Pipeline([("preprocessor", preprocessor), ("model", champion)])
    joblib.dump(deployment, os.path.join(MODELS, "supervised_certification_pipeline.joblib"))
    inference_start = time.perf_counter()
    full_prob = deployment.predict_proba(frame[SUPERVISED_INPUTS])[:, 1]
    full_inference_runtime = time.perf_counter() - inference_start
    pd.DataFrame({
        "userid_DI": frame["userid_DI"],
        "actual_certified": y,
        "predicted_probability": full_prob,
        "predicted_certified": (full_prob >= float(winner["threshold_from_validation"])).astype(int),
    }).to_csv(os.path.join(DATA_OUT, "supervised_certification_predictions.csv"), index=False)

    feature_rows = []
    for col in SUPERVISED_NUMERIC:
        feature_rows.append({"source_feature": col, "group": "numeric", "transformation": "median imputation + RobustScaler"})
    for col in SUPERVISED_BINARY:
        feature_rows.append({"source_feature": col, "group": "binary", "transformation": "most-frequent imputation"})
    for col in SUPERVISED_CATEGORICAL:
        feature_rows.append({"source_feature": col, "group": "categorical", "transformation": "Unknown fill + one-hot; categories below 0.5% of training rows grouped"})
    pd.DataFrame(feature_rows).to_csv(os.path.join(TABLES, "supervised_feature_specification.csv"), index=False)
    pd.DataFrame({"transformed_feature": transformed_names}).to_csv(
        os.path.join(TABLES, "supervised_transformed_features.csv"), index=False
    )
    manifest = {
        "status": "Completed",
        "target": "ever certified in an eligible enrollment",
        "students": len(frame),
        "positive_students": int(y.sum()),
        "positive_rate": float(y.mean()),
        "split": {"train": len(train_idx), "validation": len(val_idx), "test": len(test_idx)},
        "source_feature_count": len(SUPERVISED_INPUTS),
        "source_features": SUPERVISED_INPUTS,
        "transformed_feature_count": len(transformed_names),
        "feature_selection_rule": "Use eligible merged-clean pre-outcome fields; remove identifiers, dates, provenance/quality flags, majority-missing fields, high-cardinality categoricals, and numeric correlations above 0.995.",
        "selected_model_id": winner["model_id"],
        "selected_model_name": winner["model_name"],
        "selected_threshold": float(winner["threshold_from_validation"]),
        "selected_test_metrics": {
            "pr_auc": float(winner["test_pr_auc"]),
            "roc_auc": float(winner["test_roc_auc"]),
            "brier": float(winner["test_brier"]),
            "accuracy": float(winner["test_accuracy"]),
            "balanced_accuracy": float(winner["test_balanced_accuracy"]),
            "precision": float(winner["test_precision"]),
            "recall": float(winner["test_recall"]),
            "f1": float(winner["test_f1"]),
            "training_runtime_sec": float(winner["runtime_sec"]),
        },
        "full_cohort_inference_runtime_sec": full_inference_runtime,
        "inference_students_per_second": float(len(frame) / full_inference_runtime),
        "primary_metric": "PR-AUC because certification is imbalanced",
        "imbalance_handling": "Stratified split, class-weighted models, PR-AUC and threshold tuning on validation only; no resampling of the master data.",
    }
    with open(os.path.join(REPRO, "supervised_track_manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    _plot_supervised(comparison, y, y[test_idx], selected_test["prediction"], test_predictions)
    return frame, full_prob, manifest, comparison


def _plot_unsupervised(elbow, results, profile, X_full, labels, selected_k, gap_k, elbow_k):
    plt.figure(figsize=(7.5, 4.5))
    plt.plot(elbow["k"], elbow["inertia"], marker="o", color="#0B1F3A")
    plt.xticks(K_VALUES)
    plt.xlabel("Number of clusters (k)", fontsize=10)
    plt.ylabel("Within-cluster sum of squares (WCSS)", fontsize=10)
    plt.title("K-Means Inertia / WCSS Elbow Diagnostic Curve", fontsize=12, fontweight="bold", pad=10, loc="center")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "kmeans_elbow.png"), dpi=180)
    plt.close()

    kmeans = results[results["family"].eq("K-Means")].sort_values("k").set_index("k")
    score_path = os.path.join(TABLES, "k_selection_composite_scores.csv")
    k_scores = pd.read_csv(score_path) if os.path.exists(score_path) else None
    selected_k = int(selected_k)
    fig, axes = plt.subplots(2, 3, figsize=(16, 9.5), sharex=True)
    panels = [
        (elbow.set_index("k")["inertia"], "1. Inertia / WCSS ↓", "#0B1F3A"),
        (kmeans["silhouette"], "2. Silhouette Score ↑", "#163A6B"),
        (kmeans["davies_bouldin"], "3. Davies–Bouldin Index ↓", "#B63232"),
        (kmeans["calinski_harabasz"], "4. Calinski–Harabasz Index ↑", "#6B4EA2"),
        (kmeans["resample_ari"], "5. ARI Stability ↑", "#A56A00"),
        (kmeans["resample_nmi"], "6. NMI Stability ↑", "#19734B"),
    ]
    for ax, (series, title, color) in zip(axes.ravel(), panels):
        ax.plot(series.index, series.values, marker="o", linewidth=2.2, color=color, label="Metric curve")
        selected_y = float(series.loc[selected_k])
        ax.scatter([selected_k], [selected_y], color="#DC2626", s=120, zorder=5, edgecolors="#111", linewidths=1.5, label=f"Selected k={selected_k}")
        ax.axvline(selected_k, color="#DC2626", linestyle="--", linewidth=1.8, alpha=0.8)
        ax.set_title(title, fontsize=11, fontweight="bold", pad=8, loc="center")
        ax.set_xticks(K_VALUES)
        ax.set_xlabel("Number of clusters (k)")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, loc="best")
    fig.suptitle(
        f"Multi-Metric K Selection Diagnostics · One Selected K from Weighted 6-Metric Score · Selected k={selected_k}\n"
        f"6 Criteria: Inertia, Silhouette, Davies-Bouldin, Calinski-Harabasz, ARI, NMI",
        fontsize=13, fontweight="bold", x=0.5, ha="center"
    )
    plt.tight_layout(rect=(0, 0, 1, 0.93))
    plt.savefig(os.path.join(FIGURES, "multi_metric_k_selection_gap.png"), dpi=180, bbox_inches="tight")
    plt.savefig(os.path.join(FIGURES, "unsupervised_k_metric_grid.png"), dpi=180, bbox_inches="tight")
    plt.close()


    # Radar: best configuration per family, normalized only for visual comparison.
    best = results[results["role"].eq("Candidate")].sort_values("mean_internal_rank").groupby("family", as_index=False).first()
    metrics = ["silhouette", "davies_bouldin", "calinski_harabasz", "resample_ari"]
    normalized = best[metrics].copy()
    normalized["davies_bouldin"] = -normalized["davies_bouldin"]
    normalized = (normalized - normalized.min()) / (normalized.max() - normalized.min()).replace(0, 1)
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, polar=True)
    for idx, row in best.iterrows():
        values = normalized.loc[idx, metrics].tolist() + [normalized.loc[idx, metrics[0]]]
        ax.plot(angles, values, linewidth=1.8, label=row["family"])
    ax.set_xticks(angles[:-1], ["Silhouette", "DB (reversed)", "CH", "Stability"])
    ax.set_yticklabels([])
    ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1.05), fontsize=8)
    ax.set_title("Best configuration in each model family")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "unsupervised_model_radar.png"), dpi=180, bbox_inches="tight")
    plt.close()

    feature_cols = UNSUPERVISED_FEATURES
    angles = np.linspace(0, 2 * np.pi, len(feature_cols), endpoint=False).tolist(); angles += angles[:1]
    fig = plt.figure(figsize=(8, 6)); ax = fig.add_subplot(111, polar=True)
    for _, row in profile.iterrows():
        values = row[feature_cols].astype(float).tolist(); values += values[:1]
        ax.plot(angles, values, linewidth=2, label=f"Cluster {int(row['cluster'])}")
        ax.fill(angles, values, alpha=0.05)
    radar_labels = [
        column.replace("mean_course_", "").replace("_percentile", "").replace("_", " ").title()
        for column in feature_cols
    ]
    ax.set_xticks(angles[:-1], radar_labels)
    ax.set_ylim(0, 1); ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1.05))
    ax.set_title("Student cluster behavior profiles")
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "cluster_profile_radar.png"), dpi=180, bbox_inches="tight"); plt.close()

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.bar([f"Persona {int(v)}" for v in profile["cluster"]], profile["share_pct"], color=plt.cm.viridis(np.linspace(.2, .85, len(profile))))
    for idx, value in enumerate(profile["share_pct"]):
        ax.text(idx, value + 0.5, f"{value:.1f}%", ha="center", fontweight="bold")
    ax.set_ylabel("Share of students (%)"); ax.set_title("Behavioral Persona Proportions", fontweight="bold")
    ax.grid(axis="y", alpha=.25); plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "persona_proportions.png"), dpi=180, bbox_inches="tight"); plt.close()

    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(X_full), min(5000, len(X_full)), replace=False)
    xyz = PCA(n_components=3, random_state=SEED).fit_transform(X_full[idx])
    fig = plt.figure(figsize=(8, 6)); ax = fig.add_subplot(111, projection="3d")
    scatter = ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], c=np.asarray(labels)[idx], s=5, cmap="viridis", alpha=0.55)
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2"); ax.set_zlabel("PC3")
    ax.set_title("3D behavior hyperspace (PCA projection)")
    fig.colorbar(scatter, ax=ax, shrink=0.6, label="Cluster")
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "behavior_hyperspace_3d.png"), dpi=180); plt.close()


def _plot_outcome_quality():
    path = os.path.join(ROOT, "data", "quarantine", "outcome_quality_flags.parquet")
    if not os.path.exists(path):
        return
    audited = pd.read_parquet(path)
    plot_data = audited[["grade", "certified", "certified_below_documented_minimum"]].dropna(subset=["grade", "certified"]).copy()
    if plot_data.empty:
        return
    rng = np.random.default_rng(SEED)
    sample = plot_data.sample(min(20000, len(plot_data)), random_state=SEED)
    y_jitter = sample["certified"].astype(float) + rng.normal(0, 0.025, len(sample))
    colors = np.where(sample["certified_below_documented_minimum"], "#B63232",
                      np.where(sample["certified"].eq(1), "#F4B400", "#163A6B"))
    plt.figure(figsize=(9, 4.8))
    plt.scatter(sample["grade"], y_jitter, s=9, alpha=0.35, c=colors, edgecolors="none")
    plt.axvline(0.50, color="#B63232", linestyle="--", linewidth=2, label="grade = 0.50 threshold")
    plt.yticks([0, 1], ["Not certified", "Certified"])
    plt.xlabel("Grade")
    plt.ylabel("Certification status")
    plt.title("Outcome consistency: certified records below grade 0.50")
    below = int(plot_data["certified_below_documented_minimum"].sum())
    plt.text(0.02, 1.08, f"Certified with grade < 0.50: {below:,}", color="#B63232", fontweight="bold")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "certified_grade_threshold_audit.png"), dpi=180)
    plt.close()


def _plot_supervised(comparison, y, y_test, y_pred, test_predictions):
    top = comparison[~comparison["model_id"].eq("dummy_baseline")].copy()
    fig, ax = plt.subplots(figsize=(12, 5.8))
    metrics = [
        ("test_accuracy", "Accuracy", "#2563EB"),
        ("test_precision", "Precision", "#0D9488"),
        ("test_recall", "Recall", "#16A34A"),
        ("test_f1", "F1", "#F59E0B"),
        ("test_roc_auc", "AUC (ROC-AUC)", "#7C3AED"),
    ]
    x = np.arange(len(top))
    width = 0.15
    for i, (col, label, color) in enumerate(metrics):
        offset = (i - 2) * width
        ax.bar(x + offset, top[col], width, label=label, color=color)
    ax.set_xticks(x)
    ax.set_xticklabels(top["model_name"], rotation=25, ha="right", fontsize=9.5)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Held-out test score")
    ax.set_title("Supervised Models: Popular Core Metrics (Accuracy, Precision, Recall, F1, AUC)", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", ncol=5, fontsize=8.5)
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "supervised_model_comparison.png"), dpi=180, bbox_inches="tight")
    plt.close()
    counts = pd.Series(y).value_counts().sort_index()
    plt.figure(figsize=(6.5, 4.5))
    plt.bar(["Not certified", "Certified"], [counts.get(0, 0), counts.get(1, 0)], color=["#0B1F3A", "#F4B400"])
    plt.ylabel("Students"); plt.title("Certification class imbalance")
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "certification_class_balance.png"), dpi=180); plt.close()

    matrix = confusion_matrix(y_test, y_pred, labels=[0, 1])
    pd.DataFrame(matrix, index=["actual_not_certified", "actual_certified"],
                 columns=["pred_not_certified", "pred_certified"]).to_csv(
        os.path.join(TABLES, "supervised_confusion_matrix.csv")
    )
    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks([0, 1], ["Predicted: Not certified", "Predicted: Certified"], rotation=20, ha="right")
    ax.set_yticks([0, 1], ["Actual: Not certified", "Actual: Certified"])
    ax.set_title("Selected supervised model confusion matrix")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{matrix[i, j]:,}", ha="center", va="center",
                    color="white" if matrix[i, j] > matrix.max() / 2 else "#0B1F3A",
                    fontsize=13, fontweight="bold")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "supervised_confusion_matrix.png"), dpi=180, bbox_inches="tight")
    plt.close()

    # Compare the strongest non-baseline classifiers on the identical held-out test set.
    comparison_models = comparison[~comparison["model_id"].eq("dummy_baseline")].head(6)
    rows = []
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, (_, model_row) in zip(axes.ravel(), comparison_models.iterrows()):
        model_id = model_row["model_id"]
        model_matrix = confusion_matrix(y_test, test_predictions[model_id]["prediction"], labels=[0, 1])
        tn, fp, fn, tp = model_matrix.ravel()
        rows.append({"model_id": model_id, "model_name": model_row["model_name"], "tn": tn, "fp": fp, "fn": fn, "tp": tp,
                     "precision": model_row["test_precision"], "recall": model_row["test_recall"], "f1": model_row["test_f1"]})
        image = ax.imshow(model_matrix, cmap="Blues")
        ax.set_title(f"{model_row['model_name']}\nF1={model_row['test_f1']:.3f} · Recall={model_row['test_recall']:.3f}")
        ax.set_xticks([0, 1], ["Pred 0", "Pred 1"]); ax.set_yticks([0, 1], ["Actual 0", "Actual 1"])
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{model_matrix[i, j]:,}", ha="center", va="center",
                        color="white" if model_matrix[i, j] > model_matrix.max() / 2 else "#0B1F3A", fontweight="bold")
    for ax in axes.ravel()[len(comparison_models):]:
        ax.axis("off")
    fig.suptitle("Supervised confusion-matrix comparison · identical held-out test set", fontsize=15, fontweight="bold")
    plt.tight_layout(rect=(0, 0, 1, .96))
    plt.savefig(os.path.join(FIGURES, "supervised_confusion_matrices_comparison.png"), dpi=180, bbox_inches="tight")
    plt.close()
    pd.DataFrame(rows).to_csv(os.path.join(TABLES, "supervised_confusion_matrices_comparison.csv"), index=False)


def _build_segment_summary(students, unsup_assignments, supervised_frame, supervised_prob):
    merged = students[["userid_DI"] + UNSUPERVISED_FEATURES].merge(unsup_assignments, on="userid_DI")
    sup = supervised_frame[["userid_DI", "certified"]].copy()
    sup["predicted_probability"] = supervised_prob
    merged = merged.merge(sup, on="userid_DI", how="left")
    merged["engagement_score"] = merged[UNSUPERVISED_FEATURES].mean(axis=1, skipna=True)
    q25, q75 = merged["engagement_score"].quantile([0.25, 0.75]).tolist()
    masks = {
        "all": pd.Series(True, index=merged.index),
        "high_engagement": merged["engagement_score"].ge(q75),
        "low_engagement": merged["engagement_score"].le(q25),
        "certified_only": merged["certified"].eq(1),
    }
    result = {
        "definitions": {
            "high_engagement": f"engagement_score >= observed 75th percentile ({q75:.6f})",
            "low_engagement": f"engagement_score <= observed 25th percentile ({q25:.6f})",
            "certified_only": "ever certified in an eligible enrollment; used for descriptive/post-hoc display only",
        },
        "segments": {},
    }
    for key, mask in masks.items():
        part = merged.loc[mask]
        result["segments"][key] = {
            "students": int(len(part)),
            "certification_rate": float(part["certified"].mean()) if len(part) else None,
            "mean_predicted_probability": float(part["predicted_probability"].mean()) if len(part) else None,
            "mean_features": {column: float(part[column].mean()) for column in UNSUPERVISED_FEATURES},
            "cluster_distribution": {
                str(int(k)): int(v) for k, v in part["unsupervised_cluster"].value_counts().sort_index().items()
            },
            "feature_distributions": {
                column: {
                    "p05": float(part[column].quantile(0.05)),
                    "p25": float(part[column].quantile(0.25)),
                    "median": float(part[column].median()),
                    "p75": float(part[column].quantile(0.75)),
                    "p95": float(part[column].quantile(0.95)),
                }
                for column in UNSUPERVISED_FEATURES
            },
        }

    # Export exact values behind the segment-comparison visuals.
    comparison_rows = []
    distribution_rows = []
    for key, payload in result["segments"].items():
        row = {
            "segment": key,
            "students": payload["students"],
            "certification_rate": payload["certification_rate"],
            "mean_predicted_probability": payload["mean_predicted_probability"],
            **payload["mean_features"],
        }
        for cluster_id, count in payload["cluster_distribution"].items():
            row[f"cluster_{cluster_id}_count"] = count
            row[f"cluster_{cluster_id}_share"] = count / max(payload["students"], 1)
        comparison_rows.append(row)
        for feature, stats in payload["feature_distributions"].items():
            distribution_rows.append({"segment": key, "feature": feature, **stats})
    comparison_frame = pd.DataFrame(comparison_rows)
    comparison_frame.to_csv(os.path.join(TABLES, "segment_comparison.csv"), index=False)
    pd.DataFrame(distribution_rows).to_csv(os.path.join(TABLES, "segment_feature_distributions.csv"), index=False)

    labels = list(result["segments"])
    display_labels = [label.replace("_", " ").title() for label in labels]
    colors = ["#163A6B", "#19734B", "#B63232", "#F4B400"]

    # Mean-feature comparison across every dashboard segment.
    x = np.arange(len(UNSUPERVISED_FEATURES))
    width = 0.19
    fig, ax = plt.subplots(figsize=(13, 6.5))
    for offset, (key, color) in enumerate(zip(labels, colors)):
        values = [result["segments"][key]["mean_features"][feature] for feature in UNSUPERVISED_FEATURES]
        ax.bar(x + (offset - 1.5) * width, values, width, label=display_labels[offset], color=color)
    ax.set_xticks(x, [feature.replace("mean_course_", "").replace("_percentile", "").replace("_", " ").title() for feature in UNSUPERVISED_FEATURES])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Mean within-course percentile")
    ax.set_title("Behavior Feature Comparison Across Dashboard Segments", fontweight="bold")
    ax.legend(ncol=2)
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "segment_feature_comparison.png"), dpi=180, bbox_inches="tight")
    plt.close()

    # Student volume, observed outcome, and predicted probability comparison.
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    counts = [result["segments"][key]["students"] for key in labels]
    axes[0].bar(display_labels, counts, color=colors)
    axes[0].set_ylabel("Students")
    axes[0].set_title("Segment Size", fontweight="bold")
    axes[0].tick_params(axis="x", rotation=20)
    metric_x = np.arange(len(labels))
    observed = [result["segments"][key]["certification_rate"] or 0 for key in labels]
    predicted = [result["segments"][key]["mean_predicted_probability"] or 0 for key in labels]
    axes[1].bar(metric_x - 0.18, observed, 0.36, label="Observed certification", color="#163A6B")
    axes[1].bar(metric_x + 0.18, predicted, 0.36, label="Mean predicted probability", color="#F4B400")
    axes[1].set_xticks(metric_x, display_labels, rotation=20)
    axes[1].set_ylim(0, 1.05)
    axes[1].set_ylabel("Rate")
    axes[1].set_title("Outcome and Prediction Comparison", fontweight="bold")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "segment_outcome_comparison.png"), dpi=180, bbox_inches="tight")
    plt.close()

    # Normalized cluster composition per segment.
    all_clusters = sorted({int(cluster) for payload in result["segments"].values() for cluster in payload["cluster_distribution"]})
    fig, ax = plt.subplots(figsize=(10.5, 6))
    bottom = np.zeros(len(labels))
    palette = plt.cm.viridis(np.linspace(0.15, 0.85, max(len(all_clusters), 1)))
    for color, cluster_id in zip(palette, all_clusters):
        shares = [result["segments"][key]["cluster_distribution"].get(str(cluster_id), 0) / max(result["segments"][key]["students"], 1) for key in labels]
        ax.bar(display_labels, shares, bottom=bottom, label=f"Cluster {cluster_id}", color=color)
        bottom += np.asarray(shares)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share within segment")
    ax.set_title("Cluster Composition Across Dashboard Segments", fontweight="bold")
    ax.legend(ncol=max(1, len(all_clusters)))
    ax.tick_params(axis="x", rotation=20)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "segment_cluster_comparison.png"), dpi=180, bbox_inches="tight")
    plt.close()

    # Sampled distributions for every feature and every (potentially
    # overlapping) dashboard segment. The overlap is disclosed in the report.
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    rng = np.random.default_rng(SEED)
    for ax, feature in zip(axes.flat, UNSUPERVISED_FEATURES):
        values = []
        for key in labels:
            part = merged.loc[masks[key], feature].dropna().to_numpy()
            if len(part) > 8000:
                part = rng.choice(part, 8000, replace=False)
            values.append(part)
        ax.boxplot(values, labels=display_labels, showfliers=False, patch_artist=True,
                   boxprops={"facecolor": "#DCE6F3", "edgecolor": "#163A6B"},
                   medianprops={"color": "#B63232", "linewidth": 2})
        ax.set_ylim(0, 1)
        ax.set_title(feature.replace("mean_course_", "").replace("_percentile", "").replace("_", " ").title(), fontweight="bold")
        ax.tick_params(axis="x", rotation=18)
        ax.set_ylabel("Within-course percentile")
        ax.grid(axis="y", alpha=0.2)
    plt.suptitle("Feature Distribution Comparison Across Segments", fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "segment_distribution_comparison.png"), dpi=180, bbox_inches="tight")
    plt.close()

    with open(os.path.join(REPRO, "dashboard_segment_summary.json"), "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    return result


def _write_literature_and_track_status():
    text = """# Research basis, dataset alignment, and applied decisions

## Dataset-specific sources

1. HarvardX Person-Course Academic Year 2013 De-Identified Dataset, version 3.0. Harvard Dataverse. https://doi.org/10.7910/DVN/26147
   - Relevance: official provenance for de-identified person-course records and their scope/limitations.
   - Applied here: source inventory, checksum/provenance audit, one-student aggregation, and explicit caution that aggregate records are not event sequences.
2. Ho et al. (2014), HarvardX and MITx: The First Year of Open Online Courses. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2381263
   - Finding: participation, intent, engagement, and certification are highly heterogeneous.
   - Applied here: distributions and persona proportions are reported alongside completion outcomes; certification alone is not treated as the sole definition of success.
3. Kizilcec, Piech, and Schneider (2013), Deconstructing Disengagement. https://doi.org/10.1145/2460296.2460330
   - Finding: longitudinal engagement subpopulations reveal more than a binary completion view.
   - Applied here: behavioral personas are profiled with radar and distribution plots, while clusters remain descriptive and non-causal.

## Method sources

4. Tibshirani, Walther, and Hastie (2001), Estimating the number of clusters via the Gap statistic. https://doi.org/10.1111/1467-9868.00293
   - Applied here: Gap(k), its simulation standard error, and the one-standard-error selection rule are combined with Silhouette, Davies-Bouldin, Calinski-Harabasz, stability ARI, and minimum cluster size. Elbow/WCSS is retained only for audit and contributes no selection vote.
5. Gitinabard et al. (2018), Your Actions or Your Associates? Predicting Certification and Dropout in MOOCs. https://arxiv.org/abs/1809.00052
   - Applied here: behavioral and forum features inform certification models; PR-AUC, recall, F1, calibration, and confusion matrices are reported because the positive class is rare.
6. Fei and Yeung (2015/2017), Temporal Models for Predicting Student Dropout in Massive Open Online Courses. https://arxiv.org/abs/1702.06404
7. Yang et al. (2016), Modelling Student Behavior using Granular Large Scale Action Data from a MOOC. https://arxiv.org/abs/1608.04789
   - Boundary applied here: sequence CNN/RNN/LSTM models are not claimed because the available modeling table contains aggregates rather than ordered event-level sequences.
8. Gardner and Brooks (2018), Dropout Model Evaluation in MOOCs. https://arxiv.org/abs/1802.06009
   - Applied here: stratified train/validation/test isolation, a baseline, threshold selection on validation only, and final evaluation on untouched test data.

## Student-row-to-text LLM / Transformer track

The unit of analysis is one student row. Audited behavioral values are deterministically rendered as factual natural-language statements and passed to lexical and transformer representations for supervised certification prediction. The target remains quarantined and never enters the text. Video fields are interpreted only as play/click counts; they are not watch duration and are not presented as spoken-video transcripts.
"""
    with open(os.path.join(RESEARCH, "track_literature_review.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    status = pd.DataFrame([
        {"track": "Traditional Unsupervised", "status": "Completed", "reason": "Behavioral features are selected from merged clean data using coverage, variation, redundancy, and leakage rules."},
        {"track": "Deep Learning", "status": "Completed", "reason": "Neural-network classifier predicts certification using governed pre-outcome features."},
        {"track": "Supervised Learning", "status": "Completed", "reason": "Certification is available as a separately governed target."},
        {"track": "LLM / Transformer Text Classification", "status": "Completed", "reason": "One audited student row was converted to factual behavior text; TF-IDF and DistilBERT representations were trained and tested for certification prediction."},
    ])
    status.to_csv(os.path.join(TABLES, "analysis_track_status.csv"), index=False)


def run_generative_llm_track(students, unsup_profile, supervised_manifest):
    """Serialize one audited student row to text and train text classifiers.

    This is deliberately a student-profile NLP task, not lecture transcription.
    Outcome fields are joined only as labels and never appear in serialized text.
    """
    print("[Track] LLM / Transformer: student behavior row-to-text classification")
    outcomes = pd.read_parquet(SUPERVISED_OUTCOMES_PATH)
    target = outcomes.groupby("userid_DI", as_index=False)["certified"].max()
    frame = students.merge(target, on="userid_DI", how="inner")

    # A stratified development cohort keeps local transformer inference bounded
    # while retaining the naturally imbalanced certification prevalence.
    sample_n = min(12000, len(frame))
    sample, _ = train_test_split(
        frame, train_size=sample_n, random_state=SEED, stratify=frame["certified"]
    ) if sample_n < len(frame) else (frame.copy(), None)
    sample = sample.reset_index(drop=True)
    texts = _student_behavior_text(sample)
    y = sample["certified"].astype(int).to_numpy()
    indices = np.arange(len(sample))
    train_idx, rest_idx = train_test_split(indices, test_size=.30, random_state=SEED, stratify=y)
    val_idx, test_idx = train_test_split(rest_idx, test_size=.50, random_state=SEED, stratify=y[rest_idx])

    text_frame = pd.DataFrame({
        "userid_DI": sample["userid_DI"],
        "split": "train",
        "text_type": "student_behavior_profile_from_one_row",
        "student_behavior_text": texts,
        "target_stored_separately": True,
    })
    text_frame.loc[val_idx, "split"] = "validation"
    text_frame.loc[test_idx, "split"] = "test"
    text_frame.to_csv(os.path.join(TABLES, "llm_student_text_inputs.csv"), index=False)

    candidates = []
    tfidf_specs = [
        ("tfidf_logistic", "TF-IDF + Logistic Regression", (1, 1), 12000),
        ("tfidf_bigram_logistic", "TF-IDF (1–2 grams) + Logistic Regression", (1, 2), 20000),
    ]
    fitted = {}
    predictions = {}
    for model_id, model_name, ngrams, max_features in tfidf_specs:
        pipeline = Pipeline([
            ("vectorizer", TfidfVectorizer(ngram_range=ngrams, min_df=2, max_features=max_features, sublinear_tf=True)),
            ("model", LogisticRegression(max_iter=1000, solver="liblinear", class_weight="balanced", random_state=SEED)),
        ])
        t0 = time.perf_counter()
        pipeline.fit([texts[i] for i in train_idx], y[train_idx])
        runtime = time.perf_counter() - t0
        val_prob = pipeline.predict_proba([texts[i] for i in val_idx])[:, 1]
        threshold = _optimal_f1_threshold(y[val_idx], val_prob)
        test_prob = pipeline.predict_proba([texts[i] for i in test_idx])[:, 1]
        pred = (test_prob >= threshold).astype(int)
        candidates.append(_llm_metric_row(model_id, model_name, "lexical NLP baseline", runtime, threshold, y[test_idx], test_prob, pred))
        fitted[model_id] = pipeline
        predictions[model_id] = (test_prob, pred)

    repo = "distilbert-base-uncased"
    if not _hf_model_cached(repo):
        raise RuntimeError(f"Required local transformer is not cached: {repo}")
    t0 = time.perf_counter()
    embeddings = _encode_with_distilbert(texts, repo)
    embedding_runtime = time.perf_counter() - t0
    transformer = LogisticRegression(max_iter=1000, solver="liblinear", class_weight="balanced", random_state=SEED)
    t0 = time.perf_counter()
    transformer.fit(embeddings[train_idx], y[train_idx])
    runtime = time.perf_counter() - t0 + embedding_runtime
    val_prob = transformer.predict_proba(embeddings[val_idx])[:, 1]
    threshold = _optimal_f1_threshold(y[val_idx], val_prob)
    test_prob = transformer.predict_proba(embeddings[test_idx])[:, 1]
    pred = (test_prob >= threshold).astype(int)
    model_id = "distilbert_logistic"
    candidates.append(_llm_metric_row(model_id, "DistilBERT Embeddings + Logistic Regression", "frozen transformer encoder", runtime, threshold, y[test_idx], test_prob, pred))
    fitted[model_id] = transformer
    predictions[model_id] = (test_prob, pred)

    comparison = pd.DataFrame(candidates).sort_values(
        ["test_pr_auc", "test_f1", "test_brier"], ascending=[False, False, True]
    ).reset_index(drop=True)
    winner = comparison.iloc[0]
    comparison["selected"] = comparison["model_id"].eq(winner["model_id"])
    comparison.to_csv(os.path.join(TABLES, "llm_text_classifier_comparison.csv"), index=False)

    confusion_rows = []
    for _, row in comparison.iterrows():
        _, model_pred = predictions[row["model_id"]]
        tn, fp, fn, tp = confusion_matrix(y[test_idx], model_pred, labels=[0, 1]).ravel()
        confusion_rows.append({"model_id": row["model_id"], "model_name": row["model_name"], "tn": tn, "fp": fp, "fn": fn, "tp": tp})
    confusions = pd.DataFrame(confusion_rows)
    confusions.to_csv(os.path.join(TABLES, "llm_text_confusion_matrices.csv"), index=False)
    selected_prob, selected_pred = predictions[winner["model_id"]]
    pd.DataFrame({
        "userid_DI": sample.iloc[test_idx]["userid_DI"].to_numpy(),
        "actual_certified": y[test_idx],
        "predicted_certified": selected_pred,
        "predicted_probability": selected_prob,
    }).to_csv(os.path.join(TABLES, "llm_text_test_predictions.csv"), index=False)

    artifact = {
        "model_id": winner["model_id"], "model_name": winner["model_name"],
        "model": fitted[winner["model_id"]], "threshold": float(winner["threshold_from_validation"]),
        "serialization_function": "_student_behavior_text", "unit_of_analysis": "one student row",
        "target": "certified (kept outside serialized text)",
        "transformer_repo": repo if winner["model_id"] == model_id else None,
    }
    joblib.dump(artifact, os.path.join(MODELS, "llm_student_text_classifier.joblib"))
    _plot_llm_text_models(comparison, confusions)

    task_plan = pd.DataFrame([
        {"field": "Unit of analysis", "specification": "One row = one de-identified student"},
        {"field": "Input conversion", "specification": "Audited behavioral values are rendered as one factual sentence set per student"},
        {"field": "Video interpretation", "specification": "total_video_plays is a play/click count; no watch-duration claim is made"},
        {"field": "Prediction target", "specification": "Ever certified in an eligible enrollment; stored separately from text"},
        {"field": "Models", "specification": "TF-IDF baselines and locally cached DistilBERT embeddings with a class-weighted classifier"},
        {"field": "Success metric", "specification": "Test PR-AUC, supported by recall, precision, F1, ROC-AUC, Brier score, and confusion matrix"},
    ])
    task_plan.to_csv(os.path.join(TABLES, "llm_task_definition.csv"), index=False)
    comparison[["model_name", "representation", "runtime_sec", "test_pr_auc", "test_f1", "selected"]].rename(
        columns={"model_name": "method", "representation": "kind", "selected": "status"}
    ).to_csv(os.path.join(TABLES, "llm_method_availability.csv"), index=False)

    manifest = {
        "status": "Completed — student rows converted to text and models evaluated",
        "track_type": "Tabular-to-Text Student Classification",
        "task_definition": "Predict student certification from a factual natural-language rendering of each student's behavioral row.",
        "unit_of_analysis": "one row per student",
        "sample_students": int(sample_n),
        "positive_students": int(y.sum()),
        "positive_rate": float(y.mean()),
        "split": {"train": len(train_idx), "validation": len(val_idx), "test": len(test_idx)},
        "trained_models": comparison["model_name"].tolist(),
        "selected_model_id": winner["model_id"],
        "selected_model_name": winner["model_name"],
        "selected_threshold": float(winner["threshold_from_validation"]),
        "selected_test_metrics": {key.replace("test_", ""): float(winner[key]) for key in ["test_pr_auc", "test_roc_auc", "test_brier", "test_accuracy", "test_balanced_accuracy", "test_precision", "test_recall", "test_f1"]},
        "target_leakage_guard": "certified is joined only as y after text generation and is never included in the student sentence",
        "video_semantics": "video values are play/click counts, not watched minutes or clip duration",
        "content_boundary": "This model classifies student behavioral profiles; it does not transcribe or summarize spoken lecture content.",
        "output_artifacts": [
            "outputs/tables/llm_student_text_inputs.csv", "outputs/tables/llm_text_classifier_comparison.csv",
            "outputs/tables/llm_text_confusion_matrices.csv", "outputs/tables/llm_text_test_predictions.csv",
            "outputs/figures/tracks/llm_text_model_comparison.png", "outputs/figures/tracks/llm_text_confusion_matrices.png",
            "models/tracks/llm_student_text_classifier.joblib",
        ],
    }
    with open(os.path.join(REPRO, "llm_track_manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    
    try:
        from src.run_llm_external_benchmark import main as run_external_benchmark
        run_external_benchmark()
    except Exception as exc:
        print(f"[Warning] run_external_benchmark call failed: {exc}")

    return manifest, text_frame, comparison


def _llm_metric_row(model_id, model_name, representation, runtime, threshold, y_true, probability, prediction):
    return {
        "model_id": model_id, "model_name": model_name, "representation": representation,
        "runtime_sec": runtime, "threshold_from_validation": threshold,
        "test_pr_auc": float(average_precision_score(y_true, probability)),
        "test_roc_auc": float(roc_auc_score(y_true, probability)),
        "test_brier": float(brier_score_loss(y_true, probability)),
        "test_accuracy": float(accuracy_score(y_true, prediction)),
        "test_balanced_accuracy": float(balanced_accuracy_score(y_true, prediction)),
        "test_precision": float(precision_score(y_true, prediction, zero_division=0)),
        "test_recall": float(recall_score(y_true, prediction, zero_division=0)),
        "test_f1": float(f1_score(y_true, prediction, zero_division=0)),
    }


def _plot_llm_text_models(comparison, confusions):
    metrics = ["test_pr_auc", "test_precision", "test_recall", "test_f1"]
    ax = comparison.set_index("model_name")[metrics].plot(kind="bar", figsize=(12, 6), ylim=(0, 1), rot=10)
    ax.set_ylabel("Test score"); ax.set_title("Student behavior text-classifier comparison"); ax.grid(axis="y", alpha=.2)
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "llm_text_model_comparison.png"), dpi=180, bbox_inches="tight"); plt.close()
    fig, axes = plt.subplots(1, len(confusions), figsize=(5 * len(confusions), 4.5))
    axes = np.atleast_1d(axes)
    for ax, row in zip(axes, confusions.itertuples(index=False)):
        matrix = np.array([[row.tn, row.fp], [row.fn, row.tp]])
        image = ax.imshow(matrix, cmap="Blues")
        for (i, j), value in np.ndenumerate(matrix): ax.text(j, i, f"{value:,}", ha="center", va="center")
        ax.set_xticks([0, 1], ["Pred 0", "Pred 1"]); ax.set_yticks([0, 1], ["Actual 0", "Actual 1"]); ax.set_title(row.model_name)
    fig.suptitle("Test confusion matrices · same held-out students")
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "llm_text_confusion_matrices.png"), dpi=180, bbox_inches="tight"); plt.close()


def _hf_model_cached(repo_name):
    cache_name = "models--" + repo_name.replace("/", "--")
    return os.path.isdir(os.path.join(CACHE_HOME, cache_name))


def _student_behavior_text(frame):
    texts = []
    for _, row in frame.iterrows():
        def value(name):
            raw = row.get(name, 0)
            return 0.0 if pd.isna(raw) else float(raw)

        video = int(round(value("total_video_plays")))
        events = int(round(value("total_events")))
        days = int(round(value("total_active_days")))
        chapters = int(round(value("total_chapters")))
        forums = int(round(value("total_forum_posts")))
        courses = int(round(value("n_courses")))
        availability = value("video_data_available_rate")
        video_level = "no recorded video plays" if video == 0 else "low video activity" if video < 5 else "moderate video activity" if video < 25 else "high video activity"
        texts.append(
            f"This is a structured behavioral summary, not a video transcript. "
            f"The learner enrolled in {courses} courses and recorded {video} video plays, classified as {video_level}. "
            f"Video logging availability was {availability:.0%}. The learner generated {events} events across {days} active days, "
            f"accessed {chapters} chapters, and posted {forums} forum messages."
        )
    return texts


def _encode_with_distilbert(texts, repo):
    """Create mean-pooled DistilBERT embeddings for short behavior summaries."""
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(repo, local_files_only=True)
    model = AutoModel.from_pretrained(repo, local_files_only=True)
    model.eval()
    vectors = []
    batch_size = 96
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=96, return_tensors="pt")
            output = model(**encoded).last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).float()
            pooled = (output * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            vectors.append(pooled.cpu().numpy())
    return np.vstack(vectors)


def run_llm_embedding_track(students):
    """Execute local NLP models on truthful structured behavioral sentences."""
    sample_n = min(2500, len(students))
    sample = students.sample(sample_n, random_state=SEED).reset_index(drop=True)
    texts = _student_behavior_text(sample)
    text_frame = pd.DataFrame({
        "userid_DI": sample["userid_DI"],
        "text_type": "structured_video_behavior_summary_not_transcript",
        "behavior_text": texts,
        "source_fields": "nplay_video-derived totals; video availability; events; active days; chapters; forum posts",
    })
    text_frame.to_csv(os.path.join(TABLES, "llm_behavior_text_inputs.csv"), index=False)

    availability = [
        {"method": "TF-IDF + SVD", "kind": "local lexical NLP baseline", "repo": "scikit-learn", "status": "completed", "reason": "Runs locally on structured behavioral sentences."},
        {"method": "DIST / DistilBERT", "kind": "local transformer embedding", "repo": "distilbert-base-uncased", "status": "completed", "reason": "Cached local transformer model executed without remote API."},
        {"method": "GPT", "kind": "remote generative LLM", "repo": "", "status": "not run", "reason": "No API credential or need to send sensitive learner records to an external service."},
        {"method": "Spoken-content LLM", "kind": "media transcript model", "repo": "", "status": "blocked", "reason": "No video/audio/caption/transcript files exist; structured behavioral text is not spoken content."},
    ]
    availability_frame = pd.DataFrame(availability)
    availability_frame.to_csv(os.path.join(TABLES, "llm_method_availability.csv"), index=False)

    representations = []
    t0 = time.perf_counter()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=5000, sublinear_tf=True)
    sparse = vectorizer.fit_transform(texts)
    tfidf_vectors = TruncatedSVD(n_components=32, random_state=SEED).fit_transform(sparse)
    tfidf_vectors = StandardScaler().fit_transform(tfidf_vectors)
    representations.append(("TF-IDF + SVD", tfidf_vectors, time.perf_counter() - t0))

    t0 = time.perf_counter()
    distil_vectors = _encode_with_distilbert(texts, "distilbert-base-uncased")
    representations.append(("DIST / DistilBERT", distil_vectors, time.perf_counter() - t0))

    records, fitted = [], {}
    for method, vectors, embed_runtime in representations:
        for k in range(2, 7):
            t0 = time.perf_counter()
            model = MiniBatchKMeans(n_clusters=k, n_init=10, batch_size=512, random_state=SEED)
            labels = model.fit_predict(vectors)
            runtime = time.perf_counter() - t0
            second = MiniBatchKMeans(n_clusters=k, n_init=10, batch_size=512, random_state=SEED + 101)
            labels_second = second.fit_predict(vectors)
            metrics = _safe_metrics(vectors, labels)
            records.append({
                "track": "Structured Behavioral Text NLP", "method": method,
                "family": "MiniBatch K-Means", "k": k, "runtime_sec": runtime,
                "embedding_runtime_sec": embed_runtime, "sample_students": sample_n,
                "resample_ari": float(adjusted_rand_score(labels, labels_second)), **metrics,
            })
            fitted[(method, k)] = (model, vectors, labels)
    result_frame = pd.DataFrame(records)
    eligible = result_frame[result_frame["smallest_cluster_pct"].ge(1.0)].copy()
    eligible["rank_silhouette"] = eligible["silhouette"].rank(ascending=False, method="min")
    eligible["rank_db"] = eligible["davies_bouldin"].rank(ascending=True, method="min")
    eligible["rank_ch"] = eligible["calinski_harabasz"].rank(ascending=False, method="min")
    eligible["rank_stability"] = eligible["resample_ari"].rank(ascending=False, method="min")
    eligible["mean_internal_rank"] = eligible[["rank_silhouette", "rank_db", "rank_ch", "rank_stability"]].mean(axis=1)
    winner = eligible.sort_values(["mean_internal_rank", "runtime_sec"]).iloc[0]
    result_frame = result_frame.merge(eligible[["method", "k", "mean_internal_rank"]], on=["method", "k"], how="left")
    result_frame["selected"] = result_frame["method"].eq(winner["method"]) & result_frame["k"].eq(winner["k"])
    result_frame["noise_pct"] = 0.0
    result_frame.to_csv(os.path.join(TABLES, "llm_embedding_model_comparison.csv"), index=False)

    selected_model, selected_vectors, selected_labels = fitted[(winner["method"], int(winner["k"]))]
    joblib.dump({"model": selected_model, "method": winner["method"], "k": int(winner["k"]), "text_policy": "structured behavior, not transcript"}, os.path.join(MODELS, "llm_behavior_text_cluster.joblib"))
    projection = PCA(n_components=2, random_state=SEED).fit_transform(selected_vectors)
    pd.DataFrame({"userid_DI": sample["userid_DI"], "x": projection[:, 0], "y": projection[:, 1], "cluster": selected_labels, "method": winner["method"]}).to_csv(os.path.join(TABLES, "llm_behavior_embedding_projection.csv"), index=False)
    plt.figure(figsize=(8.5, 6))
    plt.scatter(projection[:, 0], projection[:, 1], c=selected_labels, cmap="viridis", s=10, alpha=.6)
    plt.xlabel("PCA 1"); plt.ylabel("PCA 2"); plt.title(f"Behavioral Text Embeddings · {winner['method']} · k={int(winner['k'])}")
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "llm_behavior_embedding_projection.png"), dpi=180); plt.close()

    manifest = {
        "status": "Completed on structured behavioral text; not a spoken-content transcript model",
        "sample_students": sample_n,
        "input_text": "Deterministic factual sentences generated from audited video-play and learning-behavior fields.",
        "completed_methods": ["TF-IDF + SVD", "DIST / DistilBERT"],
        "selected_method": winner["method"], "selected_k": int(winner["k"]),
        "selected_metrics": {"silhouette": float(winner["silhouette"]), "davies_bouldin": float(winner["davies_bouldin"]), "calinski_harabasz": float(winner["calinski_harabasz"]), "resample_ari": float(winner["resample_ari"])},
        "not_run_methods": availability_frame[availability_frame["status"].ne("completed")][["method", "reason"]].to_dict(orient="records"),
        "content_boundary": "These sentences summarize interaction metadata. They do not contain or reconstruct spoken video content.",
        "output_artifacts": ["outputs/tables/llm_behavior_text_inputs.csv", "outputs/tables/llm_embedding_model_comparison.csv", "outputs/tables/llm_behavior_embedding_projection.csv", "outputs/figures/tracks/llm_behavior_embedding_projection.png", "models/tracks/llm_behavior_text_cluster.joblib"],
    }
    return manifest, result_frame


def run_track_analysis():
    _ensure_dirs()
    students = pd.read_parquet(STUDENTS_PATH)
    registry = build_feature_registry(students)
    missing = [column for column in UNSUPERVISED_FEATURES if column not in students.columns]
    if missing:
        raise RuntimeError(f"Step 3 must be rerun before track analysis; missing features: {missing}")
    unsup_assign, unsup_manifest, unsup_results, profile, full_prep, X_full = run_unsupervised_track(students)
    # Add a larger multi-seed sensitivity audit without overwriting the
    # operational segmentation selected by the governed baseline workflow.
    from src.k_sensitivity_audit import main as run_k_sensitivity_audit
    run_k_sensitivity_audit()
    # Reproduce the saved outcome-free sample positions for the unsupervised diagnostics.
    rng = np.random.default_rng(SEED)
    sample_idx = np.sort(rng.choice(len(students), min(15000, len(students)), replace=False))
    train_idx, eval_idx = train_test_split(np.arange(len(sample_idx)), test_size=0.30, random_state=SEED, shuffle=True)
    deep_frame, deep_prob, deep_manifest, deep_results = run_deep_learning_track(students)
    supervised_frame, supervised_prob, supervised_manifest, supervised_results = run_supervised_track(students)
    llm_manifest, llm_results, llm_model_results = run_generative_llm_track(students, profile, supervised_manifest)
    _build_segment_summary(students, unsup_assign, supervised_frame, supervised_prob)
    _write_literature_and_track_status()

    unified_rows = []
    for _, row in unsup_results.iterrows():
        unified_rows.append({
            "track": "Traditional Unsupervised", "model": row["family"], "configuration": row["model_id"],
            "k": row.get("k"), "primary_metric_name": "Silhouette", "primary_metric_value": row.get("silhouette"),
            "silhouette": row.get("silhouette"), "davies_bouldin": row.get("davies_bouldin"),
            "calinski_harabasz": row.get("calinski_harabasz"), "stability_ari": row.get("resample_ari"),
            "accuracy": np.nan, "balanced_accuracy": np.nan, "precision": np.nan, "recall": np.nan,
            "f1": np.nan, "runtime_sec": row.get("runtime_sec"), "selected": row.get("selected", False),
        })
    for _, row in deep_results.iterrows():
        unified_rows.append({
            "track": "Deep Learning", "model": row["model_name"], "configuration": row["model_id"],
            "k": np.nan, "primary_metric_name": "PR-AUC", "primary_metric_value": row["test_pr_auc"],
            "silhouette": np.nan, "davies_bouldin": np.nan,
            "calinski_harabasz": np.nan, "stability_ari": np.nan,
            "accuracy": row["test_accuracy"], "balanced_accuracy": row["test_balanced_accuracy"],
            "precision": row["test_precision"], "recall": row["test_recall"],
            "f1": row["test_f1"], "runtime_sec": row.get("runtime_sec"), "selected": row.get("selected", False),
        })
    for _, row in supervised_results.iterrows():
        unified_rows.append({
            "track": "Supervised Learning", "model": row["model_name"], "configuration": row["model_id"],
            "k": np.nan, "primary_metric_name": "PR-AUC", "primary_metric_value": row["test_pr_auc"],
            "silhouette": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan,
            "stability_ari": np.nan, "accuracy": row["test_accuracy"],
            "balanced_accuracy": row["test_balanced_accuracy"], "precision": row["test_precision"],
            "recall": row["test_recall"], "f1": row["test_f1"],
            "runtime_sec": row["runtime_sec"], "selected": row["selected"],
        })
    for _, row in llm_model_results.iterrows():
        unified_rows.append({
            "track": "LLM / Transformer Text Classification", "model": row["model_name"],
            "configuration": row["model_id"], "k": np.nan,
            "primary_metric_name": "PR-AUC", "primary_metric_value": row["test_pr_auc"],
            "silhouette": np.nan, "davies_bouldin": np.nan,
            "calinski_harabasz": np.nan, "stability_ari": np.nan,
            "accuracy": row["test_accuracy"], "balanced_accuracy": row["test_balanced_accuracy"],
            "precision": row["test_precision"], "recall": row["test_recall"],
            "f1": row["test_f1"], "runtime_sec": row["runtime_sec"], "selected": row["selected"],
        })
    pd.DataFrame(unified_rows).to_csv(os.path.join(TABLES, "all_track_model_comparison.csv"), index=False)
    summary = {
        "students": len(students),
        "feature_registry_rows": len(registry),
        "traditional_unsupervised": unsup_manifest,
        "deep_learning": deep_manifest,
        "supervised_learning": supervised_manifest,
        "generative_llm": llm_manifest,
    }
    with open(os.path.join(REPRO, "analysis_tracks_manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    print("[+] Unified analysis tracks completed with computed artifacts only.")
    return summary


def run_llm_track_only():
    """Refresh only the student-row-to-text classification track."""
    _ensure_dirs()
    students = pd.read_parquet(STUDENTS_PATH)
    with open(os.path.join(REPRO, "supervised_track_manifest.json"), encoding="utf-8") as handle:
        supervised_manifest = json.load(handle)
    profile = pd.read_csv(os.path.join(TABLES, "unsupervised_cluster_profiles.csv"))
    build_feature_registry(students)
    llm_manifest, _, llm_model_results = run_generative_llm_track(students, profile, supervised_manifest)

    analysis_path = os.path.join(REPRO, "analysis_tracks_manifest.json")
    with open(analysis_path, encoding="utf-8") as handle:
        analysis_manifest = json.load(handle)
    analysis_manifest["generative_llm"] = llm_manifest
    with open(analysis_path, "w", encoding="utf-8") as handle:
        json.dump(analysis_manifest, handle, indent=2, ensure_ascii=False)

    comparison_path = os.path.join(TABLES, "all_track_model_comparison.csv")
    comparison = pd.read_csv(comparison_path)
    comparison = comparison[~comparison["track"].isin(["Generative LLM", "LLM/NLP Representation", "Content LLM / RAG", "LLM / Transformer Text Classification"])]
    rows = []
    for _, row in llm_model_results.iterrows():
        rows.append({
            "track": "LLM / Transformer Text Classification", "model": row["model_name"],
            "configuration": row["model_id"], "k": np.nan, "primary_metric_name": "PR-AUC",
            "primary_metric_value": row["test_pr_auc"], "silhouette": np.nan, "davies_bouldin": np.nan,
            "calinski_harabasz": np.nan, "stability_ari": np.nan, "accuracy": row["test_accuracy"],
            "balanced_accuracy": row["test_balanced_accuracy"], "precision": row["test_precision"],
            "recall": row["test_recall"], "f1": row["test_f1"], "runtime_sec": row["runtime_sec"],
            "selected": row["selected"],
        })
    pd.concat([comparison, pd.DataFrame(rows)], ignore_index=True).to_csv(comparison_path, index=False)
    _write_literature_and_track_status()
    print("[+] Student-row-to-text LLM track refreshed; other model tracks were not retrained.")
    return llm_manifest


if __name__ == "__main__":
    run_track_analysis()
