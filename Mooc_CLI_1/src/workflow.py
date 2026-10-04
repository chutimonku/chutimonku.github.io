"""Reproducible implementation of the authoritative Workflow.md.

The project has two branches:
* grouped, imbalanced binary classification of course certification;
* outcome-free student-level behavioral clustering.

All learned transformations are fitted after deterministic group splits.  Model
selection uses validation evidence; only locked winners see the test split.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import html
import json
import os
import platform
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"))

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import seaborn as sns
import sklearn
from scipy import stats
from sklearn.base import BaseEstimator
from sklearn.cluster import AgglomerativeClustering, Birch, DBSCAN, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    adjusted_rand_score,
    average_precision_score,
    balanced_accuracy_score,
    calinski_harabasz_score,
    classification_report,
    confusion_matrix,
    davies_bouldin_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    silhouette_samples,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import StratifiedGroupKFold, cross_validate
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, RobustScaler, StandardScaler
from sklearn.tree import DecisionTreeClassifier


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/big_student_clear_third_version.csv"
PROCESSED = ROOT / "data/processed"
QUARANTINE = ROOT / "data/quarantine"
TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
EDA_FIGURES = FIGURES / "eda"
CLASS_FIGURES = FIGURES / "classification"
CLUSTER_FIGURES = FIGURES / "clustering"
REPRO = ROOT / "outputs/reproducibility"
LOGS = ROOT / "outputs/logs"
RESEARCH = ROOT / "outputs/research"
MODELS = ROOT / "models"
CANDIDATES = MODELS / "candidates"
FINAL_MODELS = MODELS / "final"
REPORTS = ROOT / "reports"
MONITORING = ROOT / "monitoring"
CONFIG_PATH = ROOT / "config/project_config.json"

OUTCOMES = ["certified", "grade", "explored", "incomplete_flag"]
CLASS_TARGET = "certified"
CLASS_FORBIDDEN = ["grade", "explored", "incomplete_flag", "Unnamed: 0"]
CLASS_NUMERIC = [
    "year", "viewed", "nevents", "ndays_act", "nplay_video_clean",
    "nplay_video_missing", "nchapters", "nforum_posts", "age_clean",
    "age_missing", "engagement_span_days",
]
CLASS_CATEGORICAL = ["institute", "course_id", "semester", "final_cc_cname_DI", "LoE_DI", "gender"]
CLASS_FEATURES = CLASS_NUMERIC + CLASS_CATEGORICAL
CLUSTER_FEATURES = [
    "n_enrollments", "n_unique_courses", "n_institutes", "view_rate",
    "total_events", "mean_events", "total_active_days", "mean_active_days",
    "total_video_plays", "video_observed_rate", "total_chapters",
    "total_forum_posts", "overall_span_days", "event_intensity",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    for path in [PROCESSED, QUARANTINE, TABLES, EDA_FIGURES, CLASS_FIGURES,
                 CLUSTER_FIGURES, REPRO, LOGS, RESEARCH, CANDIDATES,
                 FINAL_MODELS, REPORTS, MONITORING, ROOT / "examples", ROOT / "outputs/data"]:
        path.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if pd.isna(value):
        return None
    raise TypeError(f"Cannot JSON serialize {type(value)!r}")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=_json_default)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def group_split_value(identifier: str, seed: int) -> float:
    raw = hashlib.sha256(f"{seed}|{identifier}".encode("utf-8")).digest()[:8]
    return int.from_bytes(raw, "big") / float(2**64)


def assign_group_split(ids: pd.Series, seed: int) -> pd.Series:
    unique = pd.Series(ids.astype(str).unique())
    values = unique.map(lambda x: group_split_value(x, seed))
    labels = np.where(values < 0.70, "train", np.where(values < 0.85, "validation", "test"))
    mapping = dict(zip(unique, labels))
    return ids.astype(str).map(mapping)


def deterministic_clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Deterministic, non-learned cleaning; never mutates the raw file."""
    df = raw.copy()
    df["nplay_video_missing"] = (df["nplay_video"] == 197757).astype("int8")
    df["nplay_video_clean"] = df["nplay_video"].mask(df["nplay_video"] == 197757, np.nan)
    df["age_missing"] = ((df["age"] <= 0) | (df["age"] > 100)).astype("int8")
    df["age_clean"] = df["age"].mask((df["age"] <= 0) | (df["age"] > 100), np.nan)
    start = pd.to_datetime(df["start_time_DI"], errors="coerce")
    last = pd.to_datetime(df["last_event_DI"], errors="coerce")
    span = (last - start).dt.days
    df["engagement_span_days"] = span.mask(span < 0, np.nan)
    for col in CLASS_CATEGORICAL:
        df[col] = df[col].astype("string").fillna("Unknown").str.strip()
    return df


def aggregate_students(clean: pd.DataFrame) -> pd.DataFrame:
    """Aggregate outcome-free course records to one row per student."""
    forbidden = [c for c in OUTCOMES if c in clean.columns]
    source = clean.drop(columns=forbidden, errors="ignore").copy()
    grouped = source.groupby("userid_DI", sort=False)
    students = grouped.agg(
        n_enrollments=("course_id", "size"),
        n_unique_courses=("course_id", "nunique"),
        n_institutes=("institute", "nunique"),
        view_rate=("viewed", "mean"),
        total_events=("nevents", "sum"),
        mean_events=("nevents", "mean"),
        total_active_days=("ndays_act", "sum"),
        mean_active_days=("ndays_act", "mean"),
        total_chapters=("nchapters", "sum"),
        total_forum_posts=("nforum_posts", "sum"),
        video_observed_rate=("nplay_video_missing", lambda x: 1.0 - x.mean()),
        age=("age_clean", "median"),
        gender=("gender", "first"),
        education=("LoE_DI", "first"),
        country=("final_cc_cname_DI", "first"),
        first_start=("start_time_DI", "min"),
        last_event=("last_event_DI", "max"),
    )
    students["total_video_plays"] = grouped["nplay_video_clean"].sum(min_count=1)
    first_dt = pd.to_datetime(students.pop("first_start"), errors="coerce")
    last_dt = pd.to_datetime(students.pop("last_event"), errors="coerce")
    students["overall_span_days"] = (last_dt - first_dt).dt.days.clip(lower=0)
    students["event_intensity"] = students["total_events"] / students["total_active_days"].clip(lower=1)
    students = students.reset_index()
    for outcome in OUTCOMES:
        if outcome in students.columns:
            raise AssertionError(f"Outcome leakage into clustering table: {outcome}")
    return students


FIELD_DESCRIPTIONS = {
    "Unnamed: 0": ("integer", "identifier", "none", "Source export row index"),
    "institute": ("categorical", "context", "none", "Course-delivering institution"),
    "course_id": ("categorical", "context", "none", "Course identifier"),
    "year": ("integer", "context", "year", "Offering year"),
    "semester": ("categorical", "context", "none", "Offering term"),
    "userid_DI": ("string", "identifier/group", "none", "De-identified learner identifier"),
    "viewed": ("binary", "behavior", "indicator", "Viewed course content"),
    "explored": ("binary", "outcome/leakage", "indicator", "Explored at least half the course chapters"),
    "certified": ("binary", "classification target", "indicator", "Earned course certificate"),
    "final_cc_cname_DI": ("categorical", "demographic", "none", "Generalized country"),
    "LoE_DI": ("categorical", "demographic", "none", "Level of education"),
    "gender": ("categorical", "demographic", "none", "Self-reported generalized gender"),
    "grade": ("continuous", "outcome/leakage", "proportion", "Final grade"),
    "start_time_DI": ("date", "temporal", "date", "De-identified start date"),
    "last_event_DI": ("date", "temporal", "date", "De-identified last-event date"),
    "nevents": ("count", "behavior", "events", "Recorded interaction-event count"),
    "ndays_act": ("count", "behavior", "days", "Number of active days"),
    "nplay_video": ("count", "behavior", "plays", "Video plays; 197757 is treated as missing sentinel in this derivative"),
    "nchapters": ("count", "behavior", "chapters", "Distinct chapters visited"),
    "nforum_posts": ("count", "behavior", "posts", "Forum posts"),
    "incomplete_flag": ("binary", "outcome/leakage", "indicator", "Incomplete-record status flag"),
    "age": ("integer", "demographic", "years", "De-identified learner age"),
}


def make_data_dictionary(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in raw.columns:
        conceptual, role, unit, description = FIELD_DESCRIPTIONS.get(col, ("unknown", "unknown", "unknown", "Undocumented"))
        rows.append({
            "variable": col, "observed_dtype": str(raw[col].dtype), "conceptual_type": conceptual,
            "role": role, "unit": unit, "description": description,
            "missing_count": int(raw[col].isna().sum()),
            "missing_pct": raw[col].isna().mean() * 100,
            "unique_count": int(raw[col].nunique(dropna=True)),
        })
    return pd.DataFrame(rows)


def generate_eda(raw: pd.DataFrame, clean: pd.DataFrame, students: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    numeric = ["nevents", "ndays_act", "nplay_video_clean", "nchapters", "nforum_posts", "age_clean", "engagement_span_days"]
    eda = clean[numeric].describe(percentiles=[.01, .25, .5, .75, .95, .99]).T.reset_index(names="feature")
    eda["missing_count"] = [int(clean[c].isna().sum()) for c in numeric]
    eda["zero_pct"] = [float((clean[c] == 0).mean() * 100) for c in numeric]
    eda["skew"] = [float(clean[c].skew()) for c in numeric]
    eda.to_csv(TABLES / "eda_summary.csv", index=False)

    corr = clean[numeric].corr(method="spearman")
    screening = []
    for i, a in enumerate(numeric):
        for b in numeric[i + 1:]:
            screening.append({"feature_a": a, "feature_b": b, "spearman_rho": corr.loc[a, b], "high_abs_correlation": abs(corr.loc[a, b]) >= .85})
    pd.DataFrame(screening).to_csv(TABLES / "feature_screening.csv", index=False)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, col in zip(axes.flat, ["nevents", "ndays_act", "nplay_video_clean", "nchapters", "nforum_posts", "engagement_span_days"]):
        vals = np.log1p(clean[col].dropna().clip(lower=0))
        sns.histplot(vals.sample(min(80000, len(vals)), random_state=42), bins=45, ax=ax, color="#2878b5")
        ax.set_title(f"{col} (log1p)")
    fig.tight_layout(); fig.savefig(EDA_FIGURES / "numeric_distributions.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    missing = raw.isna().mean().sort_values(ascending=False) * 100
    missing[missing > 0].plot.bar(ax=axes[0], color="#d95f02")
    axes[0].set_title("Explicit missingness in supplied CSV"); axes[0].set_ylabel("Percent")
    pd.Series({"not certified": int((raw.certified == 0).sum()), "certified": int((raw.certified == 1).sum())}).plot.bar(ax=axes[1], color=["#6baed6", "#238b45"])
    axes[1].set_title("Classification target imbalance"); axes[1].set_ylabel("Enrollment records")
    fig.tight_layout(); fig.savefig(EDA_FIGURES / "missingness_and_target.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, cmap="vlag", center=0, annot=True, fmt=".2f", ax=ax)
    ax.set_title("Spearman correlations (descriptive, not causal)")
    fig.tight_layout(); fig.savefig(EDA_FIGURES / "correlation_heatmap.png", dpi=150); plt.close(fig)

    pca_source = students[CLUSTER_FEATURES].replace([np.inf, -np.inf], np.nan)
    pca_pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("log", FunctionTransformer(np.log1p)), ("scale", RobustScaler()), ("pca", PCA(n_components=2, random_state=42))])
    sample = pca_source.sample(min(15000, len(pca_source)), random_state=42)
    coords = pca_pipe.fit_transform(sample)
    fig, ax = plt.subplots(figsize=(8, 6)); ax.scatter(coords[:, 0], coords[:, 1], s=5, alpha=.25, color="#54278f")
    ax.set_title("Outcome-free student behavior: PCA inspection"); ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    fig.tight_layout(); fig.savefig(EDA_FIGURES / "pca_structure.png", dpi=150); plt.close(fig)


def run_data_stage() -> dict[str, Any]:
    ensure_dirs()
    cfg = load_config()
    raw_hash_before = sha256_file(RAW)
    raw = pd.read_csv(RAW)
    dictionary = make_data_dictionary(raw)
    dictionary.to_csv(PROCESSED / "data_dictionary.csv", index=False)
    dictionary.to_csv(TABLES / "data_dictionary.csv", index=False)

    key = ["userid_DI", "course_id", "year", "semester"]
    quality = {
        "generated_at": utc_now(), "rows": len(raw), "columns": len(raw.columns),
        "unique_students": int(raw.userid_DI.nunique()), "exact_duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_offering_keys": int(raw.duplicated(key).sum()),
        "class_counts": raw.certified.value_counts().sort_index().to_dict(),
        "positive_rate": float(raw.certified.mean()),
        "invalid_binary_counts": {c: int((~raw[c].isin([0, 1])).sum()) for c in ["viewed", "explored", "certified", "incomplete_flag"]},
        "negative_count_values": {c: int((raw[c] < 0).sum()) for c in ["nevents", "ndays_act", "nchapters", "nforum_posts"]},
        "video_sentinel_197757_count": int((raw.nplay_video == 197757).sum()),
        "invalid_age_count": int(((raw.age <= 0) | (raw.age > 100)).sum()),
        "date_inversion_count": int((pd.to_datetime(raw.last_event_DI) < pd.to_datetime(raw.start_time_DI)).sum()),
        "demographic_privacy": "De-identified but potentially sensitive; no re-identification or individual punitive use.",
        "representativeness": "Self-selected registrations in 13 early HarvardX/MITx offerings; not representative of all learners or present-day MOOCs.",
    }
    write_json(PROCESSED / "data_quality_assessment.json", quality)

    provenance = {
        "dataset": cfg["source"], "local_path": str(RAW.relative_to(ROOT)),
        "local_file_size_bytes": RAW.stat().st_size, "local_sha256": raw_hash_before,
        "observed_rows": len(raw), "observed_columns": len(raw.columns),
        "unit": "one de-identified learner-course-offering record",
        "collection_method": "Aggregate registration, demographics, and edX activity-log derivative",
        "sampling_method": "Supplied observational census-like extract; learner registration is self-selected",
        "known_limitations": [
            "Local derivative dimensions differ from the canonical current Dataverse release; provenance cannot be proven from filename alone.",
            "Full-course aggregate behavior supports retrospective association, not early prediction.",
            "De-identification and course selection limit external validity and fairness assessment.",
        ],
    }
    write_json(PROCESSED / "data_provenance.json", provenance)

    quarantine = raw[["Unnamed: 0", "userid_DI", "course_id", "year", "semester"] + OUTCOMES].copy()
    quarantine.to_parquet(QUARANTINE / "outcomes.parquet", index=False)
    write_json(QUARANTINE / "manifest.json", {
        "created_at": utc_now(), "columns": OUTCOMES, "rows": len(quarantine),
        "raw_sha256": raw_hash_before,
        "rule": "certified is available only to the supervised branch; all outcomes are excluded from clustering. grade/explored/incomplete_flag are forbidden classification predictors.",
    })

    clean = deterministic_clean(raw)
    classification = clean[["userid_DI", "course_id"] + CLASS_FEATURES + [CLASS_TARGET]].copy()
    classification["split"] = assign_group_split(classification.userid_DI, cfg["random_seed"])
    classification.to_parquet(PROCESSED / "classification_records.parquet", index=False)
    non_outcomes = clean.drop(columns=OUTCOMES, errors="ignore")
    non_outcomes.to_parquet(PROCESSED / "raw_non_outcomes.parquet", index=False)
    students = aggregate_students(clean)
    students["split"] = assign_group_split(students.userid_DI, cfg["random_seed"])
    students.to_parquet(PROCESSED / "students_cleaned.parquet", index=False)

    split_rows = []
    for name in ["train", "validation", "test"]:
        part = classification[classification.split == name]
        sp = students[students.split == name]
        split_rows.append({"split": name, "classification_rows": len(part), "students": part.userid_DI.nunique(), "positive_rate": part.certified.mean(), "clustering_students": len(sp)})
    split_table = pd.DataFrame(split_rows)
    split_table.to_csv(TABLES / "data_splits.csv", index=False)
    overlap = {}
    sets = {n: set(students.loc[students.split == n, "userid_DI"]) for n in ["train", "validation", "test"]}
    for a, b in [("train", "validation"), ("train", "test"), ("validation", "test")]:
        overlap[f"{a}_{b}"] = len(sets[a] & sets[b])
    write_json(PROCESSED / "split_manifest.json", {
        "method": "SHA-256 deterministic group split by userid_DI", "seed": cfg["random_seed"],
        "ratios": cfg["split"], "split_summary": split_rows, "group_overlap_counts": overlap,
        "test_policy": "Test split is not used for preprocessing, tuning, selection, revision, or threshold choice.",
    })

    cleaning_rules = [
        {"field": "nplay_video", "rule": "197757 -> missing, plus missing indicator", "reason": "Repeated impossible sentinel-like maximum in 61% of derivative; uncertainty retained instead of recoding to zero"},
        {"field": "age", "rule": "values <=0 or >100 -> missing, plus missing indicator", "reason": "invalid human age for analysis"},
        {"field": "dates", "rule": "parse; negative duration -> missing", "reason": "do not invent zero-duration activity"},
        {"field": "categoricals", "rule": "trim strings; explicit Unknown", "reason": "consistent encoding"},
        {"field": "duplicates", "rule": "retain all unique offering records", "reason": "zero exact duplicates and zero duplicate learner-course-year-semester keys"},
    ]
    pd.DataFrame(cleaning_rules).to_csv(TABLES / "cleaning_rules.csv", index=False)
    write_json(PROCESSED / "cleaning_audit.json", {"input_rows": len(raw), "classification_rows": len(classification), "student_rows": len(students), "excluded_rows": 0, "rules": cleaning_rules})

    generate_eda(raw, clean, students)
    raw_hash_after = sha256_file(RAW)
    if raw_hash_before != raw_hash_after:
        raise RuntimeError("Raw data checksum changed during data stage")
    return {"raw_hash": raw_hash_before, "classification_rows": len(classification), "students": len(students)}


def class_preprocessor(features: list[str] | None = None) -> ColumnTransformer:
    features = features or CLASS_FEATURES
    numeric = [c for c in CLASS_NUMERIC if c in features]
    categorical = [c for c in CLASS_CATEGORICAL if c in features]
    return ColumnTransformer([
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)), ("scale", StandardScaler())]), numeric),
        ("categorical", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=50))]), categorical),
    ], remainder="drop")


def classifier_for(name: str, params: dict[str, Any], seed: int) -> BaseEstimator:
    if name == "dummy_prevalence":
        return DummyClassifier(strategy="prior")
    if name == "logistic_regression":
        return LogisticRegression(C=params["C"], class_weight="balanced", max_iter=500, solver="liblinear", random_state=seed)
    if name == "sgd_logistic":
        return SGDClassifier(loss="log_loss", alpha=params["alpha"], class_weight="balanced", max_iter=1000, tol=1e-3, random_state=seed)
    if name == "decision_tree":
        return DecisionTreeClassifier(max_depth=params["max_depth"], min_samples_leaf=40, class_weight="balanced", random_state=seed)
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=70, max_depth=params["max_depth"], min_samples_leaf=10, class_weight="balanced_subsample", n_jobs=-1, random_state=seed)
    if name == "extra_trees":
        return ExtraTreesClassifier(n_estimators=70, max_depth=params["max_depth"], min_samples_leaf=10, class_weight="balanced", n_jobs=-1, random_state=seed)
    raise KeyError(name)


CLASS_GRIDS: dict[str, list[dict[str, Any]]] = {
    "dummy_prevalence": [{}],
    "logistic_regression": [{"C": 0.3}, {"C": 1.0}],
    "sgd_logistic": [{"alpha": 0.0001}, {"alpha": 0.001}],
    "decision_tree": [{"max_depth": 6}, {"max_depth": 12}],
    "random_forest": [{"max_depth": 10}, {"max_depth": 16}],
    "extra_trees": [{"max_depth": 10}, {"max_depth": 16}],
}


def score_values(pipe: Pipeline, X: pd.DataFrame) -> np.ndarray:
    if hasattr(pipe, "predict_proba"):
        return pipe.predict_proba(X)[:, 1]
    decision = pipe.decision_function(X)
    return 1.0 / (1.0 + np.exp(-np.clip(decision, -30, 30)))


def binary_metrics(y: pd.Series | np.ndarray, pred: np.ndarray, score: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "precision_positive": float(precision_score(y, pred, zero_division=0)),
        "recall_positive": float(recall_score(y, pred, zero_division=0)),
        "f1_positive": float(f1_score(y, pred, zero_division=0)),
        "f1_macro": float(f1_score(y, pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y, pred, average="weighted", zero_division=0)),
        "roc_auc": float(roc_auc_score(y, score)),
        "pr_auc": float(average_precision_score(y, score)),
    }


def stratified_row_sample(df: pd.DataFrame, max_rows: int, seed: int) -> pd.DataFrame:
    if len(df) <= max_rows:
        return df.copy()
    fractions = df[CLASS_TARGET].value_counts(normalize=True)
    parts = []
    for target, fraction in fractions.items():
        part = df[df[CLASS_TARGET] == target]
        n = min(len(part), max(1, int(round(max_rows * fraction))))
        parts.append(part.sample(n=n, random_state=seed + int(target)))
    return pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)


def plot_confusion(y: np.ndarray, pred: np.ndarray, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 4.5))
    ConfusionMatrixDisplay(confusion_matrix(y, pred), display_labels=["not certified", "certified"]).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(title); fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def normalized_utility(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    utility = pd.Series(0.0, index=frame.index)
    for metric, weight in weights.items():
        values = frame[metric].astype(float)
        span = values.max() - values.min()
        scaled = (values - values.min()) / span if span > 1e-12 else pd.Series(1.0, index=frame.index)
        utility += weight * scaled
    return utility


def train_classification() -> dict[str, Any]:
    cfg = load_config(); seed = cfg["random_seed"]
    data = pd.read_parquet(PROCESSED / "classification_records.parquet")
    train = data[data.split == "train"].copy()
    val = data[data.split == "validation"].copy()
    test = data[data.split == "test"].copy()
    train_sample = stratified_row_sample(train, cfg["classification"]["candidate_training_max_rows"], seed)
    cv_sample = stratified_row_sample(train_sample, cfg["classification"]["cross_validation_max_rows"], seed + 5)
    rows: list[dict[str, Any]] = []
    best_by_algorithm: dict[str, tuple[Pipeline, dict[str, Any], dict[str, float], np.ndarray, np.ndarray]] = {}
    log_rows: list[dict[str, Any]] = []

    Xtr, ytr = train_sample[CLASS_FEATURES], train_sample[CLASS_TARGET]
    Xv, yv = val[CLASS_FEATURES], val[CLASS_TARGET]
    for algo, grid in CLASS_GRIDS.items():
        algo_candidates = []
        for index, params in enumerate(grid):
            pipe = Pipeline([("preprocess", class_preprocessor()), ("model", classifier_for(algo, params, seed))])
            started = time.perf_counter(); status = "success"; error = ""
            try:
                pipe.fit(Xtr, ytr)
                fit_seconds = time.perf_counter() - started
                pred_start = time.perf_counter(); score = score_values(pipe, Xv); pred = (score >= .5).astype(int)
                predict_seconds = time.perf_counter() - pred_start
                metrics = binary_metrics(yv, pred, score)
                tuning_score = .60 * metrics["pr_auc"] + .40 * metrics["balanced_accuracy"]
                row = {"algorithm": algo, "config_index": index, "parameters": json.dumps(params, sort_keys=True), **metrics,
                       "tuning_score": tuning_score, "fit_seconds": fit_seconds, "prediction_seconds": predict_seconds,
                       "training_rows": len(train_sample), "validation_rows": len(val), "status": status}
                rows.append(row); algo_candidates.append((tuning_score, pipe, params, metrics, pred, score))
            except Exception as exc:
                fit_seconds = time.perf_counter() - started; status = "failed"; error = repr(exc)
                rows.append({"algorithm": algo, "config_index": index, "parameters": json.dumps(params), "status": status, "error": error, "fit_seconds": fit_seconds})
            log_rows.append({"branch": "classification", "algorithm": algo, "config": json.dumps(params), "status": status, "seconds": fit_seconds, "error": error})
        if not algo_candidates:
            continue
        _, best_pipe, best_params, best_metrics, best_pred, best_score = max(algo_candidates, key=lambda x: x[0])
        best_by_algorithm[algo] = (best_pipe, best_params, best_metrics, best_pred, best_score)
        joblib.dump(best_pipe, CANDIDATES / f"classification_{algo}.joblib")
        plot_confusion(yv.to_numpy(), best_pred, f"Validation confusion matrix: {algo}", CLASS_FIGURES / f"confusion_validation_{algo}.png")

    tuning = pd.DataFrame(rows)
    tuning.to_csv(TABLES / "classification_tuning_results.csv", index=False)
    pd.DataFrame(log_rows).to_csv(LOGS / "model_training_log.csv", index=False)

    # Cross-validation is performed only after each algorithm's validation-tuned setting is fixed.
    cv_rows = []
    cv = StratifiedGroupKFold(n_splits=cfg["classification"]["cv_folds"], shuffle=True, random_state=seed)
    scorers = {"balanced_accuracy": "balanced_accuracy", "f1_macro": "f1_macro", "roc_auc": "roc_auc", "pr_auc": "average_precision"}
    for algo, (_, params, val_metrics, pred, score) in best_by_algorithm.items():
        pipe = Pipeline([("preprocess", class_preprocessor()), ("model", classifier_for(algo, params, seed))])
        cvres = cross_validate(pipe, cv_sample[CLASS_FEATURES], cv_sample[CLASS_TARGET], groups=cv_sample.userid_DI,
                               cv=cv, scoring=scorers, n_jobs=1, error_score="raise")
        row = {"algorithm": algo, "parameters": json.dumps(params, sort_keys=True), **{f"val_{k}": v for k, v in val_metrics.items()}}
        for metric in scorers:
            row[f"cv_{metric}_mean"] = float(np.mean(cvres[f"test_{metric}"]))
            row[f"cv_{metric}_std"] = float(np.std(cvres[f"test_{metric}"], ddof=1))
        row["cv_fit_seconds_mean"] = float(np.mean(cvres["fit_time"]))
        cv_rows.append(row)
    comparison = pd.DataFrame(cv_rows)
    eligible = comparison[comparison.algorithm != "dummy_prevalence"].copy()
    weights = cfg["classification"]["selection_weights"]
    eligible["selection_utility"] = normalized_utility(eligible.rename(columns={f"val_{k}": k for k in weights}), weights)
    comparison = comparison.merge(eligible[["algorithm", "selection_utility"]], on="algorithm", how="left")
    winner = eligible.sort_values(["selection_utility", "val_pr_auc"], ascending=False).iloc[0]
    winner_name = str(winner.algorithm); winner_params = best_by_algorithm[winner_name][1]

    # Plot validation ROC/PR for algorithm-level winners before touching test.
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for algo, (_, _, _, _, score) in best_by_algorithm.items():
        fpr, tpr, _ = roc_curve(yv, score); precision, recall, _ = precision_recall_curve(yv, score)
        axes[0].plot(fpr, tpr, label=f"{algo} ({roc_auc_score(yv, score):.3f})")
        axes[1].plot(recall, precision, label=f"{algo} ({average_precision_score(yv, score):.3f})")
    axes[0].plot([0, 1], [0, 1], "k--", alpha=.4); axes[0].set(title="Validation ROC curves", xlabel="False-positive rate", ylabel="True-positive rate")
    axes[1].axhline(yv.mean(), color="k", ls="--", alpha=.4); axes[1].set(title="Validation precision-recall curves", xlabel="Recall", ylabel="Precision")
    for ax in axes: ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(CLASS_FIGURES / "validation_roc_pr_curves.png", dpi=150); plt.close(fig)

    # Revision/sensitivity experiments use validation only.
    revision_rows = []
    feature_sets = {
        "full_predefined_features": CLASS_FEATURES,
        "behavior_and_context_no_demographics": [c for c in CLASS_FEATURES if c not in ["final_cc_cname_DI", "LoE_DI", "gender", "age_clean", "age_missing"]],
        "context_and_demographics_no_engagement_counts": ["year", "institute", "course_id", "semester", "final_cc_cname_DI", "LoE_DI", "gender", "age_clean", "age_missing"],
    }
    for label, features in feature_sets.items():
        p = Pipeline([("preprocess", class_preprocessor(features)), ("model", classifier_for(winner_name, winner_params, seed))])
        t0 = time.perf_counter(); p.fit(train_sample[features], ytr); s = score_values(p, val[features]); pr = (s >= .5).astype(int)
        revision_rows.append({"branch": "classification", "revision": label, "changed_component": "feature set", **binary_metrics(yv, pr, s), "seconds": time.perf_counter() - t0, "test_used": False})
    revision_df = pd.DataFrame(revision_rows)
    revision_df.to_csv(TABLES / "classification_sensitivity.csv", index=False)

    # Threshold sensitivity, also validation-only; threshold remains 0.5 for unbiased standard deployment.
    selected_val_score = best_by_algorithm[winner_name][4]
    threshold_rows = []
    for threshold in [.20, .30, .40, .50, .60, .70, .80]:
        p = (selected_val_score >= threshold).astype(int)
        m = binary_metrics(yv, p, selected_val_score)
        threshold_rows.append({"threshold": threshold, **m, "test_used": False})
    pd.DataFrame(threshold_rows).to_csv(TABLES / "classification_threshold_sensitivity.csv", index=False)

    # Refit locked winner on train + validation and evaluate untouched test once.
    development = pd.concat([train, val], ignore_index=True)
    final_pipe = Pipeline([("preprocess", class_preprocessor()), ("model", classifier_for(winner_name, winner_params, seed))])
    final_fit_start = time.perf_counter(); final_pipe.fit(development[CLASS_FEATURES], development[CLASS_TARGET]); final_fit_seconds = time.perf_counter() - final_fit_start
    joblib.dump(final_pipe, FINAL_MODELS / "classification_pipeline.joblib")
    model_hash = sha256_file(FINAL_MODELS / "classification_pipeline.joblib")
    test_start = time.perf_counter(); test_score = score_values(final_pipe, test[CLASS_FEATURES]); test_pred = (test_score >= .5).astype(int); test_seconds = time.perf_counter() - test_start
    test_metrics = binary_metrics(test[CLASS_TARGET], test_pred, test_score)
    plot_confusion(test[CLASS_TARGET].to_numpy(), test_pred, f"Untouched test confusion matrix: {winner_name}", CLASS_FIGURES / "confusion_test_final.png")
    predictions = test[["userid_DI", "course_id", CLASS_TARGET]].copy(); predictions["prediction"] = test_pred; predictions["score"] = test_score
    predictions.to_parquet(ROOT / "outputs/data/classification_test_predictions.parquet", index=False)

    report = classification_report(test[CLASS_TARGET], test_pred, labels=[0, 1], target_names=["not_certified", "certified"], output_dict=True, zero_division=0)
    per_class = pd.DataFrame(report).T.reset_index(names="class_or_average")
    per_class.to_csv(TABLES / "classification_per_class_metrics.csv", index=False)
    comparison["test_accuracy"] = np.nan; comparison["test_balanced_accuracy"] = np.nan; comparison["test_pr_auc"] = np.nan; comparison["test_roc_auc"] = np.nan
    mask = comparison.algorithm == winner_name
    comparison.loc[mask, ["test_accuracy", "test_balanced_accuracy", "test_pr_auc", "test_roc_auc"]] = [test_metrics["accuracy"], test_metrics["balanced_accuracy"], test_metrics["pr_auc"], test_metrics["roc_auc"]]
    comparison["test_policy"] = np.where(mask, "evaluated once after lock", "not evaluated to protect test set")
    comparison.to_csv(TABLES / "classification_model_comparison.csv", index=False)

    # Original-feature permutation importance on a fixed test sample, after final evaluation.
    from sklearn.inspection import permutation_importance
    perm_sample = test.sample(min(4000, len(test)), random_state=seed)
    perm = permutation_importance(final_pipe, perm_sample[CLASS_FEATURES], perm_sample[CLASS_TARGET], scoring="average_precision", n_repeats=3, random_state=seed, n_jobs=1)
    importance = pd.DataFrame({"feature": CLASS_FEATURES, "importance_mean_pr_auc_drop": perm.importances_mean, "importance_std": perm.importances_std}).sort_values("importance_mean_pr_auc_drop", ascending=False)
    importance.to_csv(TABLES / "classification_feature_importance.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 6)); top = importance.head(15).sort_values("importance_mean_pr_auc_drop"); ax.barh(top.feature, top.importance_mean_pr_auc_drop, xerr=top.importance_std, color="#3182bd")
    ax.set_title("Final classifier permutation importance"); ax.set_xlabel("Mean decrease in test PR-AUC")
    fig.tight_layout(); fig.savefig(CLASS_FIGURES / "feature_importance.png", dpi=150); plt.close(fig)

    # Error rates by difficult subgroups.
    error_source = test[["gender", "LoE_DI", "course_id", CLASS_TARGET]].copy(); error_source["prediction"] = test_pred
    error_rows = []
    for field in ["gender", "LoE_DI", "course_id"]:
        for value, part in error_source.groupby(field, dropna=False):
            y = part[CLASS_TARGET].to_numpy(); p = part.prediction.to_numpy()
            tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
            error_rows.append({"subgroup_field": field, "subgroup": str(value), "n": len(part), "positives": int(y.sum()), "false_positive_rate": fp / max(fp + tn, 1), "false_negative_rate": fn / max(fn + tp, 1), "balanced_accuracy": balanced_accuracy_score(y, p) if len(np.unique(y)) == 2 else np.nan})
    pd.DataFrame(error_rows).to_csv(TABLES / "classification_error_analysis.csv", index=False)

    lock = {"status": "LOCKED_BEFORE_TEST", "algorithm": winner_name, "parameters": winner_params, "features": CLASS_FEATURES,
            "split_policy": "train+validation refit after validation selection; test evaluated exactly once", "threshold": .5,
            "sha256": model_hash, "final_fit_seconds": final_fit_seconds, "test_prediction_seconds": test_seconds,
            "test_metrics": test_metrics, "locked_at": utc_now()}
    write_json(FINAL_MODELS / "classification_model_lock.json", lock)
    write_json(PROCESSED / "classification_results.json", lock)
    return {"winner": winner_name, "test_metrics": test_metrics, "model_hash": model_hash,
            "validation_score": float(winner.val_pr_auc), "positive_rate": float(test[CLASS_TARGET].mean())}


class StudentClusteringPipeline:
    """Portable inductive clustering pipeline with schema and leakage guards."""

    def __init__(self, preprocessor: Pipeline, model: BaseEstimator, feature_names: list[str], algorithm: str):
        self.preprocessor = preprocessor
        self.model = model
        self.feature_names = feature_names
        self.algorithm = algorithm

    def validate(self, frame: pd.DataFrame) -> None:
        leaked = sorted(set(OUTCOMES) & set(frame.columns))
        if leaked:
            raise ValueError(f"Outcome columns forbidden in clustering input: {leaked}")
        missing = sorted(set(self.feature_names) - set(frame.columns))
        if missing:
            raise ValueError(f"Missing clustering input features: {missing}")

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        self.validate(frame)
        matrix = self.preprocessor.transform(frame[self.feature_names])
        return self.model.predict(matrix)


def cluster_preprocessor() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=False)),
        ("log1p", FunctionTransformer(np.log1p, validate=False)),
        ("scale", RobustScaler()),
    ])


def safe_cluster_metrics(X: np.ndarray, labels: np.ndarray, max_eval: int = 5000, seed: int = 42) -> dict[str, Any]:
    labels = np.asarray(labels)
    valid = labels != -1
    unique = np.unique(labels[valid])
    noise = float(np.mean(~valid))
    if len(unique) < 2 or valid.sum() <= len(unique):
        return {"silhouette": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan,
                "n_clusters": int(len(unique)), "noise_rate": noise, "min_cluster_share": 0.0}
    idx = np.flatnonzero(valid)
    if len(idx) > max_eval:
        idx = np.random.default_rng(seed).choice(idx, max_eval, replace=False)
    lab = labels[idx]; mat = X[idx]
    shares = pd.Series(labels[valid]).value_counts(normalize=True)
    return {
        "silhouette": float(silhouette_score(mat, lab)),
        "davies_bouldin": float(davies_bouldin_score(mat, lab)),
        "calinski_harabasz": float(calinski_harabasz_score(mat, lab)),
        "n_clusters": int(len(unique)), "noise_rate": noise, "min_cluster_share": float(shares.min()),
    }


def nearest_centroid_predict(X_train: np.ndarray, labels: np.ndarray, X_new: np.ndarray) -> np.ndarray:
    valid_labels = sorted(x for x in np.unique(labels) if x != -1)
    centroids = np.vstack([X_train[labels == c].mean(axis=0) for c in valid_labels])
    distances = ((X_new[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    return np.asarray(valid_labels)[distances.argmin(axis=1)]


def dbscan_predict(model: DBSCAN, X_train: np.ndarray, train_labels: np.ndarray, X_new: np.ndarray) -> np.ndarray:
    core_indices = getattr(model, "core_sample_indices_", np.array([], dtype=int))
    if len(core_indices) == 0:
        return np.full(len(X_new), -1)
    nn = NearestNeighbors(n_neighbors=1).fit(X_train[core_indices])
    dist, ix = nn.kneighbors(X_new)
    predicted = train_labels[core_indices[ix[:, 0]]]
    predicted[dist[:, 0] > model.eps] = -1
    return predicted


def evaluate_cluster_candidate(algorithm: str, params: dict[str, Any], Xt: np.ndarray, Xv: np.ndarray, seed: int) -> tuple[BaseEstimator, np.ndarray, np.ndarray, bool]:
    if algorithm == "kmeans":
        model = KMeans(n_clusters=params["k"], n_init=10, random_state=seed).fit(Xt); return model, model.labels_, model.predict(Xv), True
    if algorithm == "gaussian_mixture":
        model = GaussianMixture(n_components=params["k"], covariance_type="diag", reg_covar=1e-5, max_iter=200, random_state=seed).fit(Xt); return model, model.predict(Xt), model.predict(Xv), True
    if algorithm == "birch":
        model = Birch(n_clusters=params["k"], threshold=params.get("threshold", .5)).fit(Xt); return model, model.labels_, model.predict(Xv), True
    if algorithm == "agglomerative_ward":
        model = AgglomerativeClustering(n_clusters=params["k"], linkage="ward").fit(Xt); return model, model.labels_, nearest_centroid_predict(Xt, model.labels_, Xv), False
    if algorithm == "dbscan":
        model = DBSCAN(eps=params["eps"], min_samples=params["min_samples"], n_jobs=-1).fit(Xt); return model, model.labels_, dbscan_predict(model, Xt, model.labels_, Xv), False
    raise KeyError(algorithm)


def cluster_stability(algorithm: str, params: dict[str, Any], Xt: np.ndarray, Xv: np.ndarray, seeds: list[int]) -> float:
    predictions = []
    rng = np.random.default_rng(42)
    for seed in seeds:
        idx = rng.choice(len(Xt), int(len(Xt) * .80), replace=False)
        model, labels, pred, _ = evaluate_cluster_candidate(algorithm, params, Xt[idx], Xv, seed)
        predictions.append(pred)
    aris = []
    for i in range(len(predictions)):
        for j in range(i + 1, len(predictions)):
            mask = (predictions[i] != -1) & (predictions[j] != -1)
            if mask.sum() > 1:
                aris.append(adjusted_rand_score(predictions[i][mask], predictions[j][mask]))
    return float(np.mean(aris)) if aris else np.nan


def train_clustering() -> dict[str, Any]:
    cfg = load_config(); seed = cfg["random_seed"]; ccfg = cfg["clustering"]
    students = pd.read_parquet(PROCESSED / "students_cleaned.parquet")
    train = students[students.split == "train"].copy(); val = students[students.split == "validation"].copy(); test = students[students.split == "test"].copy()
    train_sample = train.sample(min(ccfg["training_max_rows"], len(train)), random_state=seed)
    val_sample = val.sample(min(ccfg["validation_max_rows"], len(val)), random_state=seed)
    test_sample = test.sample(min(ccfg["test_max_rows"], len(test)), random_state=seed)
    prep = cluster_preprocessor(); Xt = prep.fit_transform(train_sample[CLUSTER_FEATURES]); Xv = prep.transform(val_sample[CLUSTER_FEATURES])

    grids: dict[str, list[dict[str, Any]]] = {
        "kmeans": [{"k": k} for k in ccfg["k_values"]],
        "gaussian_mixture": [{"k": k} for k in ccfg["k_values"]],
        "birch": [{"k": k, "threshold": .5} for k in ccfg["k_values"]],
        "agglomerative_ward": [{"k": k} for k in [2, 3, 4, 5]],
        "dbscan": [],
    }
    nn = NearestNeighbors(n_neighbors=12).fit(Xt)
    distances, _ = nn.kneighbors(Xt)
    for q in [.85, .92, .97]:
        grids["dbscan"].append({"eps": float(np.quantile(distances[:, -1], q)), "min_samples": 12, "quantile": q})

    rows = []; best_family: dict[str, tuple[float, BaseEstimator, dict[str, Any], np.ndarray, bool]] = {}
    training_log_path = LOGS / "model_training_log.csv"
    existing_logs = pd.read_csv(training_log_path).to_dict("records") if training_log_path.exists() else []
    for algorithm, grid in grids.items():
        family = []
        algo_Xt = Xt[:6000] if algorithm in {"agglomerative_ward", "dbscan"} else Xt
        for params in grid:
            t0 = time.perf_counter(); status = "success"; error = ""
            try:
                model, labels_train, labels_val, deployable = evaluate_cluster_candidate(algorithm, params, algo_Xt, Xv, seed)
                fit_predict_seconds = time.perf_counter() - t0
                metrics = safe_cluster_metrics(Xv, labels_val, seed=seed)
                stability = cluster_stability(algorithm, params, algo_Xt, Xv[:3000], ccfg["stability_seeds"])
                family_score = (metrics["silhouette"] if np.isfinite(metrics["silhouette"]) else -2) - .20 * (metrics["davies_bouldin"] if np.isfinite(metrics["davies_bouldin"]) else 10) + .30 * (stability if np.isfinite(stability) else 0) - metrics["noise_rate"]
                row = {"algorithm": algorithm, "parameters": json.dumps(params, sort_keys=True), **metrics,
                       "stability_ari": stability, "fit_prediction_seconds": fit_predict_seconds,
                       "training_rows": len(algo_Xt), "validation_rows": len(Xv), "deployable": deployable,
                       "family_tuning_score": family_score, "status": status}
                rows.append(row); family.append((family_score, model, params, labels_val, deployable))
            except Exception as exc:
                fit_predict_seconds = time.perf_counter() - t0; status = "failed"; error = repr(exc)
                rows.append({"algorithm": algorithm, "parameters": json.dumps(params), "status": status, "error": error, "fit_prediction_seconds": fit_predict_seconds})
            existing_logs.append({"branch": "clustering", "algorithm": algorithm, "config": json.dumps(params), "status": status, "seconds": fit_predict_seconds, "error": error})
        if family:
            best_family[algorithm] = max(family, key=lambda x: x[0])
    pd.DataFrame(existing_logs).to_csv(training_log_path, index=False)
    tuning = pd.DataFrame(rows); tuning.to_csv(TABLES / "clustering_tuning_results.csv", index=False)

    family_rows = []
    for algorithm, (score, model, params, labels_val, deployable) in best_family.items():
        row = tuning[(tuning.algorithm == algorithm) & (tuning.parameters == json.dumps(params, sort_keys=True))].iloc[0].to_dict()
        family_rows.append(row)
        joblib.dump({"preprocessor": prep, "model": model, "parameters": params, "deployable": deployable}, CANDIDATES / f"clustering_{algorithm}.joblib")
    comparison = pd.DataFrame(family_rows)
    eligible = comparison[(comparison.deployable == True) & (comparison.n_clusters >= 2) & (comparison.min_cluster_share >= .01)].copy()
    if eligible.empty:
        raise RuntimeError("No deployable clustering candidate passed minimum cluster-share criterion")
    # Rank-based predefined multi-criteria selection; outcome variables are not loaded here.
    eligible["rank_silhouette"] = eligible.silhouette.rank(pct=True)
    eligible["rank_db"] = (-eligible.davies_bouldin).rank(pct=True)
    eligible["rank_ch"] = eligible.calinski_harabasz.rank(pct=True)
    eligible["rank_stability"] = eligible.stability_ari.fillna(0).rank(pct=True)
    eligible["selection_utility"] = .35 * eligible.rank_silhouette + .20 * eligible.rank_db + .15 * eligible.rank_ch + .25 * eligible.rank_stability + .05 * (1 - eligible.noise_rate)
    comparison = comparison.merge(eligible[["algorithm", "selection_utility"]], on="algorithm", how="left")
    winner_row = eligible.sort_values(["selection_utility", "silhouette"], ascending=False).iloc[0]
    winner_name = str(winner_row.algorithm); winner_params = json.loads(winner_row.parameters)

    # Outcome-free sensitivity/error analysis on validation.
    selected_labels = best_family[winner_name][3]
    sil_values = silhouette_samples(Xv, selected_labels)
    ambiguity = pd.DataFrame({"userid_DI": val_sample.userid_DI.to_numpy(), "cluster": selected_labels, "silhouette": sil_values})
    ambiguity["ambiguous"] = ambiguity.silhouette < 0
    ambiguity.to_csv(ROOT / "outputs/data/clustering_validation_diagnostics.csv", index=False)
    diagnostics = ambiguity.groupby("cluster").agg(n=("userid_DI", "size"), mean_silhouette=("silhouette", "mean"), ambiguous_pct=("ambiguous", "mean")).reset_index()
    diagnostics["ambiguous_pct"] *= 100
    diagnostics.to_csv(TABLES / "clustering_error_analysis.csv", index=False)

    # Fit final preprocessing and selected model on development data, then lock.
    development = pd.concat([train, val], ignore_index=True)
    final_prep = cluster_preprocessor(); Xdev = final_prep.fit_transform(development[CLUSTER_FEATURES])
    if winner_name == "kmeans": final_model = KMeans(n_clusters=winner_params["k"], n_init=10, random_state=seed).fit(Xdev)
    elif winner_name == "gaussian_mixture": final_model = GaussianMixture(n_components=winner_params["k"], covariance_type="diag", reg_covar=1e-5, max_iter=200, random_state=seed).fit(Xdev)
    elif winner_name == "birch": final_model = Birch(n_clusters=winner_params["k"], threshold=winner_params.get("threshold", .5)).fit(Xdev)
    else: raise RuntimeError(f"Non-deployable algorithm selected: {winner_name}")
    deployment = StudentClusteringPipeline(final_prep, final_model, CLUSTER_FEATURES, winner_name)
    joblib.dump(deployment, FINAL_MODELS / "clustering_pipeline.joblib")
    model_hash = sha256_file(FINAL_MODELS / "clustering_pipeline.joblib")
    lock = {"status": "LOCKED_BEFORE_TEST_AND_POSTHOC_OUTCOMES", "algorithm": winner_name, "parameters": winner_params,
            "features": CLUSTER_FEATURES, "sha256": model_hash, "locked_at": utc_now(),
            "selection_rule": "Validation-only rank utility: silhouette 35%, Davies-Bouldin 20%, Calinski-Harabasz 15%, stability 25%, noise 5%; deployable and min cluster share >=1%.",
            "outcomes_used_for_selection": []}
    write_json(FINAL_MODELS / "clustering_model_lock.json", lock)

    # Untouched clustering test evaluation exactly once after lock.
    Xtest = final_prep.transform(test_sample[CLUSTER_FEATURES]); test_labels = final_model.predict(Xtest)
    test_metrics = safe_cluster_metrics(Xtest, test_labels, seed=seed)
    comparison["test_silhouette"] = np.nan; comparison["test_davies_bouldin"] = np.nan; comparison["test_policy"] = "not evaluated to protect test set"
    m = comparison.algorithm == winner_name
    comparison.loc[m, "test_silhouette"] = test_metrics["silhouette"]; comparison.loc[m, "test_davies_bouldin"] = test_metrics["davies_bouldin"]; comparison.loc[m, "test_policy"] = "evaluated once after lock"
    comparison.to_csv(TABLES / "clustering_model_comparison.csv", index=False)

    # Assign all students after lock; no outcome is present in this table.
    all_labels = deployment.predict(students)
    assignments = students[["userid_DI", "split"]].copy(); assignments["cluster"] = all_labels
    assignments.to_csv(ROOT / "outputs/data/cluster_assignments.csv", index=False)
    profiles = students.assign(cluster=all_labels).groupby("cluster")[CLUSTER_FEATURES].agg(["count", "median", "mean"])
    profiles.columns = [f"{a}_{b}" for a, b in profiles.columns]; profiles.reset_index().to_csv(TABLES / "cluster_profiles.csv", index=False)

    # Cluster-defining contribution via eta-squared; descriptive, not causal.
    contrib = []
    for feat in CLUSTER_FEATURES:
        frame = students[[feat]].copy(); frame["cluster"] = all_labels; frame = frame.dropna()
        grand = frame[feat].mean(); ss_between = sum(len(g) * (g[feat].mean() - grand) ** 2 for _, g in frame.groupby("cluster")); ss_total = ((frame[feat] - grand) ** 2).sum()
        contrib.append({"feature": feat, "eta_squared": ss_between / ss_total if ss_total else 0.0})
    contribution = pd.DataFrame(contrib).sort_values("eta_squared", ascending=False); contribution.to_csv(TABLES / "cluster_feature_contributions.csv", index=False)

    # PCA projection is fitted for visualization only, after final selection.
    vis_idx = students.sample(min(20000, len(students)), random_state=seed).index
    Xvis = final_prep.transform(students.loc[vis_idx, CLUSTER_FEATURES]); pca = PCA(n_components=2, random_state=seed); coords = pca.fit_transform(Xvis)
    fig, ax = plt.subplots(figsize=(9, 7)); scatter = ax.scatter(coords[:, 0], coords[:, 1], c=all_labels[vis_idx], cmap="tab10", s=6, alpha=.35)
    ax.set(title="Locked clustering assignments (PCA display only)", xlabel="PC1", ylabel="PC2"); fig.colorbar(scatter, ax=ax, label="Cluster")
    fig.tight_layout(); fig.savefig(CLUSTER_FIGURES / "cluster_projection.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5)); plot = tuning[tuning.status == "success"].copy()
    for algorithm, part in plot.groupby("algorithm"):
        x = range(len(part)); axes[0].plot(list(x), part.silhouette, marker="o", label=algorithm); axes[1].plot(list(x), part.stability_ari, marker="o", label=algorithm)
    axes[0].set(title="Validation silhouette across tuned configurations", xlabel="Configuration index", ylabel="Silhouette")
    axes[1].set(title="Resampling stability", xlabel="Configuration index", ylabel="ARI")
    for ax in axes: ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(CLUSTER_FIGURES / "model_diagnostics.png", dpi=150); plt.close(fig)

    write_json(PROCESSED / "clustering_results.json", {**lock, "test_metrics": test_metrics, "validation_ambiguous_pct": float(ambiguity.ambiguous.mean() * 100)})
    return {"winner": winner_name, "parameters": winner_params, "test_metrics": test_metrics, "model_hash": model_hash,
            "clusters": int(test_metrics["n_clusters"]), "assignments": assignments}


def posthoc_cluster_validation() -> dict[str, Any]:
    """Access quarantined outcomes only after the clustering lock exists."""
    lock_path = FINAL_MODELS / "clustering_model_lock.json"
    if not lock_path.exists():
        raise RuntimeError("Clustering outcomes cannot be accessed before model lock")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("status") != "LOCKED_BEFORE_TEST_AND_POSTHOC_OUTCOMES":
        raise RuntimeError("Invalid clustering lock status")
    assignments = pd.read_csv(ROOT / "outputs/data/cluster_assignments.csv")
    outcomes = pd.read_parquet(QUARANTINE / "outcomes.parquet")
    agg = outcomes.groupby("userid_DI").agg(
        any_certified=("certified", "max"), certification_rate=("certified", "mean"),
        mean_grade=("grade", "mean"), any_explored=("explored", "max"),
        any_incomplete=("incomplete_flag", "max"),
    ).reset_index()
    merged = assignments.merge(agg, on="userid_DI", validate="one_to_one")
    rows = []
    for cluster, part in merged.groupby("cluster"):
        rows.append({"cluster": int(cluster), "n_students": len(part), "share_pct": len(part) / len(merged) * 100,
                     "any_certified_pct": part.any_certified.mean() * 100, "mean_certification_rate_pct": part.certification_rate.mean() * 100,
                     "mean_grade": part.mean_grade.mean(), "any_explored_pct": part.any_explored.mean() * 100,
                     "any_incomplete_pct": part.any_incomplete.mean() * 100})
    profile = pd.DataFrame(rows); profile.to_csv(TABLES / "posthoc_validation.csv", index=False)
    contingency = pd.crosstab(merged.cluster, merged.any_certified)
    chi2, pvalue, dof, _ = stats.chi2_contingency(contingency)
    cramers_v = np.sqrt(chi2 / (len(merged) * max(1, min(contingency.shape) - 1)))
    groups = [part.mean_grade.to_numpy() for _, part in merged.groupby("cluster")]
    kw_h, kw_p = stats.kruskal(*groups)
    tests = {"certification_chi_square": {"statistic": chi2, "p_value": pvalue, "dof": dof, "cramers_v": cramers_v},
             "grade_kruskal_wallis": {"statistic": kw_h, "p_value": kw_p},
             "interpretation": "Post-hoc associations describe differences; they did not influence cluster selection and are not causal."}
    write_json(PROCESSED / "posthoc_validation.json", tests)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(profile.cluster.astype(str), profile.any_certified_pct, color="#31a354"); axes[0].set(title="Post-hoc certification by locked cluster", xlabel="Cluster", ylabel="Students with any certification (%)")
    axes[1].bar(profile.cluster.astype(str), profile.any_explored_pct, color="#3182bd"); axes[1].set(title="Post-hoc exploration by locked cluster", xlabel="Cluster", ylabel="Students with any explored course (%)")
    fig.tight_layout(); fig.savefig(CLUSTER_FIGURES / "posthoc_outcomes.png", dpi=150); plt.close(fig)
    return {"profile_rows": len(profile), "tests": tests}


def create_documentation(class_result: dict[str, Any], cluster_result: dict[str, Any]) -> None:
    candidates = [
        ["classification", "Dummy prevalence", "Empirical class prior", "Transparent baseline", "No discrimination"],
        ["classification", "Logistic regression", "Linear log-odds after preprocessing", "Interpretable and scalable", "Misses complex interactions"],
        ["classification", "SGD logistic", "Linear separability; stochastic optimization", "Fast and scalable", "Sensitive to regularization/scaling"],
        ["classification", "Decision tree", "Axis-aligned recursive partitions", "Readable nonlinear rules", "High variance without depth control"],
        ["classification", "Random forest", "Bootstrap ensemble of trees", "Flexible and robust", "Less transparent and heavier"],
        ["classification", "Extra Trees", "Randomized tree ensemble", "Flexible and efficient", "Probabilities may require calibration"],
        ["clustering", "K-means", "Roughly compact centroid clusters", "Scalable; native prediction", "Sensitive to scale and non-spherical structure"],
        ["clustering", "Gaussian mixture", "Mixture of diagonal Gaussians", "Soft probabilistic geometry", "Distributional assumption; local optima"],
        ["clustering", "BIRCH", "CF-tree compression", "Scales to large data; native prediction", "Threshold/order sensitivity"],
        ["clustering", "Ward agglomerative", "Hierarchical variance minimization", "Different structural view", "Quadratic cost; transductive"],
        ["clustering", "DBSCAN", "Dense regions separated by sparse noise", "Finds noise/nonconvex groups", "Distance concentration; no native prediction"],
    ]
    pd.DataFrame(candidates, columns=["branch", "technique", "assumptions", "advantages", "limitations"]).to_csv(TABLES / "candidate_models.csv", index=False)
    training_cfg = load_config()
    training_cfg["software_versions"] = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__, "scipy": scipy.__version__, "joblib": joblib.__version__}
    training_cfg["selected_models"] = {"classification": class_result["winner"], "clustering": cluster_result["winner"]}
    write_json(REPRO / "training_config.json", training_cfg)
    history = pd.concat([pd.read_csv(TABLES / "classification_sensitivity.csv").assign(iteration="classification_feature_revision"),
                         pd.read_csv(TABLES / "clustering_tuning_results.csv").assign(iteration="clustering_hyperparameter_revision")], ignore_index=True, sort=False)
    history.to_csv(TABLES / "optimization_history.csv", index=False)
    experiment_text = f"""# Experiment log

Generated: {utc_now()}

- Split first by `userid_DI` using seed 42 and SHA-256 group hashing.
- Classification tuning compared two regularization/depth settings per non-baseline method on validation data. The locked winner was `{class_result['winner']}`. Feature-set and threshold sensitivity used validation only.
- Clustering compared five distinct families and multiple configurations using outcome-free validation evidence. The locked deployable winner was `{cluster_result['winner']}`.
- Final development refits combined train and validation only. Each locked winner was evaluated once on its untouched test subset.
- Unsuccessful or non-deployable configurations remain in the tuning and training log tables with their status and limitations.
"""
    (REPRO / "experiment_log.md").write_text(experiment_text, encoding="utf-8")

    class_card = f"""# Classification model card

- Purpose: retrospective classification of course certification in this supplied historical dataset.
- Target/unit: `certified`; one learner-course-offering record.
- Winner: `{class_result['winner']}`; locked artifact SHA-256 `{class_result['model_hash']}`.
- Inputs: {', '.join(CLASS_FEATURES)}.
- Excluded leakage: grade, explored, incomplete_flag, raw row identifier.
- Evaluation: grouped learner split; validation selection; one untouched test evaluation.
- Limitations: full-course behavior means this is not an early-warning model; class imbalance, historical course context, fairness, and calibration require review before any real use. Do not use for punitive or automated high-stakes decisions.
"""
    (FINAL_MODELS / "classification_model_card.md").write_text(class_card, encoding="utf-8")
    cluster_card = f"""# Clustering model card

- Purpose: descriptive behavioral segmentation for aggregate support planning.
- Unit: one de-identified learner aggregated across supplied course offerings.
- Winner: `{cluster_result['winner']}` with {cluster_result['parameters']}; SHA-256 `{cluster_result['model_hash']}`.
- Outcomes used for model selection: none.
- Inputs: {', '.join(CLUSTER_FEATURES)}.
- Limitations: clusters are not natural identities, diagnoses, or causal categories. Labels can drift and should not determine access, grading, or discipline.
"""
    (FINAL_MODELS / "clustering_model_card.md").write_text(cluster_card, encoding="utf-8")
    write_json(FINAL_MODELS / "classification_input_schema.json", {"required_features": CLASS_FEATURES, "forbidden": CLASS_FORBIDDEN})
    write_json(FINAL_MODELS / "clustering_input_schema.json", {"required_features": CLUSTER_FEATURES, "forbidden": OUTCOMES})

    sample = pd.read_parquet(PROCESSED / "students_cleaned.parquet").head(10)
    sample[["userid_DI"] + CLUSTER_FEATURES].to_csv(ROOT / "examples/clustering_input.csv", index=False)
    deployment: StudentClusteringPipeline = joblib.load(FINAL_MODELS / "clustering_pipeline.joblib")
    output = sample[["userid_DI"]].copy(); output["cluster"] = deployment.predict(sample)
    output.to_csv(ROOT / "examples/clustering_output.csv", index=False)


def image_data(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def table_html(path: Path, max_rows: int = 20) -> str:
    frame = pd.read_csv(path).head(max_rows)
    numeric = frame.select_dtypes(include=np.number).columns
    frame[numeric] = frame[numeric].round(4)
    return frame.to_html(index=False, classes="data-table", border=0, na_rep="—", escape=True)


def report_figure(path: Path, caption: str) -> str:
    return f'<figure><img src="{image_data(path)}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}</figcaption></figure>'


def generate_report() -> Path:
    quality = json.loads((PROCESSED / "data_quality_assessment.json").read_text())
    provenance = json.loads((PROCESSED / "data_provenance.json").read_text())
    class_res = json.loads((PROCESSED / "classification_results.json").read_text())
    cluster_res = json.loads((PROCESSED / "clustering_results.json").read_text())
    posthoc = json.loads((PROCESSED / "posthoc_validation.json").read_text())
    split = json.loads((PROCESSED / "split_manifest.json").read_text())
    tm = class_res["test_metrics"]; cm = cluster_res["test_metrics"]
    sections = []
    sections.append(f"""<section id="executive-summary"><h2>Executive summary</h2><div class="kpis">
      <div><b>{quality['rows']:,}</b><span>enrollments</span></div><div><b>{quality['unique_students']:,}</b><span>students</span></div>
      <div><b>{tm['pr_auc']:.3f}</b><span>final test PR-AUC</span></div><div><b>{cm['silhouette']:.3f}</b><span>cluster test silhouette</span></div></div>
      <p>The workflow completed two complementary tasks. The locked <b>{html.escape(class_res['algorithm'])}</b> classifier retrospectively distinguishes certification using grouped learner splits. The outcome-free <b>{html.escape(cluster_res['algorithm'])}</b> pipeline produces {cm['n_clusters']} behavioral groups. Neither result is causal or suitable for punitive individual decisions.</p></section>""")
    sections.append(f"""<section id="problem"><h2>Problem statement and research questions</h2>
      <p><b>Problem:</b> Determine how well supplied course context, demographics, and full-course engagement distinguish certification, while separately discovering reproducible outcome-free student behavior groups for aggregate support planning.</p>
      <ol><li>Can a grouped, leakage-controlled classifier improve materially over prevalence while recovering the minority certified class?</li><li>Which of five distinct clustering families yields stable, separated, deployable student groups?</li><li>Which measured features define predictions and clusters, and where do errors or ambiguous assignments concentrate?</li></ol>
      <p><b>Stakeholders:</b> learning researchers, course teams, and data stewards. <b>Constraints:</b> de-identification, historical/self-selected sample, severe target imbalance, no causal inference, raw-data immutability, and no claimed early warning because engagement covers the full course.</p>
      <p><b>Predefined success:</b> classification selection uses validation PR-AUC (40%), balanced accuracy (25%), macro-F1 (20%), and positive recall (15%); clustering uses multiple internal metrics, stability, minimum 1% cluster share, and deployability.</p></section>""")
    sections.append("""<section id="literature"><h2>Literature review and references</h2>
      <p>The canonical <a href="https://doi.org/10.7910/DVN/26147">Harvard Dataverse record</a> defines person-course records and custom privacy terms. The <a href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2381263">first-year HarvardX/MITx report</a> provides context. Reviews of <a href="https://doi.org/10.1109/TLT.2018.2856808">MOOC prediction</a>, <a href="https://doi.org/10.1109/EDUCON.2018.8363340">dropout-prediction challenges</a>, and <a href="https://arxiv.org/abs/1711.06349">student-success prediction</a> motivate explicit outcome definitions, behavior/context features, imbalance-aware metrics, and cautious generalization.</p>
      <p>The local CSV differs in dimensions from the canonical current release, so this report calls it a <i>local derivative</i> and identifies it by checksum rather than asserting file identity.</p></section>""")
    sections.append(f"""<section id="data"><h2>Dataset source, data dictionary, quality, privacy, and splitting</h2>
      <p><b>Source:</b> {html.escape(provenance['dataset']['dataset_name'])}. Canonical URL: <a href="{provenance['dataset']['canonical_url']}">{provenance['dataset']['canonical_url']}</a>. License: {html.escape(provenance['dataset']['license'])}. Access date: {provenance['dataset']['access_date']}. Local SHA-256: <code>{provenance['local_sha256']}</code>.</p>
      <p>Observed structure: {quality['rows']:,} rows, {quality['columns']} fields, {quality['unique_students']:,} unique learners; {quality['exact_duplicate_rows']} exact duplicates and {quality['duplicate_offering_keys']} duplicate learner-course-year-term keys. Certified prevalence is {quality['positive_rate']:.2%}. The repeated video value 197757 ({quality['video_sentinel_197757_count']:,} rows) is retained as explicit missingness plus an indicator, not silently converted to zero.</p>
      <p>The SHA-256 group split assigns every learner to exactly one of train/validation/test; pairwise learner overlaps are {split['group_overlap_counts']}. The test split is untouched during tuning and revision.</p>
      <h3>Split table</h3>{table_html(TABLES/'data_splits.csv')}<h3>Complete data dictionary</h3>{table_html(TABLES/'data_dictionary.csv', 30)}</section>""")
    sections.append(f"""<section id="eda"><h2>Exploratory data analysis</h2><p>Engagement counts are zero-inflated and strongly right-skewed; log views reveal their structure without deleting valid rare high-activity observations. Correlations are descriptive, not causal.</p>
      {report_figure(EDA_FIGURES/'missingness_and_target.png','Explicit missingness and certification class imbalance.')}
      {report_figure(EDA_FIGURES/'numeric_distributions.png','Enrollment-level feature distributions after deterministic cleaning.')}
      {report_figure(EDA_FIGURES/'correlation_heatmap.png','Spearman relationships; high association motivates regularization and tree comparisons.')}
      {report_figure(EDA_FIGURES/'pca_structure.png','Outcome-free student-level PCA inspection; PCA is visualization only.')}
      <h3>Descriptive statistics</h3>{table_html(TABLES/'eda_summary.csv')}</section>""")
    sections.append(f"""<section id="preprocessing"><h2>Preprocessing and feature engineering</h2>
      <p>All deterministic validity rules run before splitting. Learned numeric median imputation, missingness indicators, standard scaling, categorical imputation, and one-hot encoding are fitted only within training pipelines. Clustering aggregates course records per learner, log1p-transforms nonnegative behavior, median-imputes, and robust-scales using training learners only. No outcomes enter clustering.</p>
      <h3>Cleaning rules</h3>{table_html(TABLES/'cleaning_rules.csv')}<h3>Candidate assumptions and limitations</h3>{table_html(TABLES/'candidate_models.csv', 20)}</section>""")
    sections.append(f"""<section id="classification"><h2>Classification results and comparison</h2>
      <p>The final locked {html.escape(class_res['algorithm'])} pipeline was selected on validation evidence, refitted on train+validation, and evaluated once on the untouched test set: accuracy {tm['accuracy']:.3f}, balanced accuracy {tm['balanced_accuracy']:.3f}, positive-class precision {tm['precision_positive']:.3f}, recall {tm['recall_positive']:.3f}, macro-F1 {tm['f1_macro']:.3f}, ROC-AUC {tm['roc_auc']:.3f}, and PR-AUC {tm['pr_auc']:.3f} versus test prevalence {quality['positive_rate']:.3f}.</p>
      {report_figure(CLASS_FIGURES/'validation_roc_pr_curves.png','Validation ROC and precision-recall curves for all classifier families.')}
      {report_figure(CLASS_FIGURES/'confusion_test_final.png','Final untouched-test confusion matrix for the locked classifier.')}
      <h3>Comparative model table</h3>{table_html(TABLES/'classification_model_comparison.csv')}<h3>Per-class metrics</h3>{table_html(TABLES/'classification_per_class_metrics.csv')}</section>""")
    sections.append(f"""<section id="clustering"><h2>Clustering results and comparison</h2>
      <p>The locked {html.escape(cluster_res['algorithm'])} configuration {html.escape(str(cluster_res['parameters']))} was chosen without outcomes. On its untouched test sample, silhouette was {cm['silhouette']:.3f}, Davies-Bouldin {cm['davies_bouldin']:.3f}, Calinski-Harabasz {cm['calinski_harabasz']:.1f}, and the smallest cluster held {cm['min_cluster_share']:.2%}. Confusion matrices are not used for clustering.</p>
      {report_figure(CLUSTER_FIGURES/'model_diagnostics.png','Validation separation and resampling stability across clustering configurations.')}
      {report_figure(CLUSTER_FIGURES/'cluster_projection.png','PCA display of locked cluster assignments; axes are not causal constructs.')}
      <h3>Separate clustering comparison</h3>{table_html(TABLES/'clustering_model_comparison.csv')}<h3>Measured cluster profiles</h3>{table_html(TABLES/'cluster_profiles.csv')}</section>""")
    sections.append(f"""<section id="interpretation"><h2>Feature importance, interpretation, and error analysis</h2>
      <p>Permutation importance reports the decrease in test PR-AUC when an original feature is shuffled after final evaluation. It is predictive importance, not a causal effect. Cluster contributions are eta-squared associations with locked assignments.</p>
      {report_figure(CLASS_FIGURES/'feature_importance.png','Original-feature permutation importance for the final classifier.')}
      <h3>Classification subgroup errors</h3>{table_html(TABLES/'classification_error_analysis.csv', 25)}
      <h3>Cluster-defining contributions</h3>{table_html(TABLES/'cluster_feature_contributions.csv')}<h3>Ambiguous cluster assignments</h3>{table_html(TABLES/'clustering_error_analysis.csv')}</section>""")
    sections.append(f"""<section id="sensitivity"><h2>Revision, sensitivity, and robustness</h2>
      <p>Feature-set ablations and threshold changes were evaluated only on validation data, one major component at a time. Cluster k, density radius, model family, and resampling seed sensitivity are retained in the tuning tables. No revision used test results.</p>
      <h3>Classification feature ablation</h3>{table_html(TABLES/'classification_sensitivity.csv')}<h3>Threshold sensitivity</h3>{table_html(TABLES/'classification_threshold_sensitivity.csv')}<h3>Optimization history excerpt</h3>{table_html(TABLES/'optimization_history.csv', 20)}</section>""")
    sections.append(f"""<section id="posthoc"><h2>Post-hoc cluster outcome validation</h2>
      <p>Only after the clustering model was locked were quarantined outcomes merged for description. Certification differed across clusters (χ²={posthoc['certification_chi_square']['statistic']:.1f}, Cramér's V={posthoc['certification_chi_square']['cramers_v']:.3f}); this association did not guide model choice and is not causal.</p>
      {report_figure(CLUSTER_FIGURES/'posthoc_outcomes.png','Outcomes revealed only after clustering lock.')}{table_html(TABLES/'posthoc_validation.csv')}</section>""")
    sections.append("""<section id="conclusions"><h2>Conclusions, limitations, risks, and recommendations</h2>
      <p><b>Observation:</b> full-course engagement contains substantial retrospective signal for certification, and outcome-free behavior admits measurable but imperfect group structure. <b>Interpretation:</b> activity breadth and intensity distinguish historical participation patterns. <b>Conclusion:</b> these artifacts support research and aggregate course-design review, not causal claims or automated intervention.</p>
      <ul><li>Do not describe the classifier as early warning without time-windowed event data.</li><li>Do not treat clusters as fixed learner identities or use them for grading, access, discipline, or surveillance.</li><li>Before operational use, validate prospectively across newer courses, audit calibration and subgroup errors, define consent/governance, and test whether interventions help.</li><li>The local derivative's chain of custody cannot be proven from its filename; preserve its recorded checksum.</li></ul></section>""")
    sections.append(f"""<section id="reproducibility"><h2>Reproducibility information</h2><p>Run <code>python run_project.py</code> from the repository root. Random seed: 42. Python {platform.python_version()}, pandas {pd.__version__}, NumPy {np.__version__}, scikit-learn {sklearn.__version__}, SciPy {scipy.__version__}. Configuration, dependency pins, model locks/checksums, logs, tests, artifact checks, and the raw-file before/after hash are saved with the run.</p></section>""")

    style = """body{margin:0;background:#f4f7fb;color:#172033;font-family:Inter,system-ui,sans-serif;line-height:1.58}header{background:linear-gradient(125deg,#102a43,#0b7285);color:white;padding:48px max(24px,calc((100% - 1120px)/2))}header h1{margin:0 0 8px;font-size:2.25rem}.wrap{max-width:1120px;margin:26px auto;padding:0 18px}section{background:white;margin:20px 0;padding:28px;border:1px solid #dbe4ee;border-radius:13px;box-shadow:0 2px 10px #102a4310}h2{color:#0b7285;border-bottom:2px solid #d8f3f0;padding-bottom:8px}h3{color:#243b53;margin-top:24px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}.kpis div{padding:16px;background:#e8f6f3;border-radius:10px}.kpis b{display:block;font-size:1.5rem;color:#087f5b}.kpis span{font-size:.85rem;color:#486581}figure{text-align:center;margin:24px 0}figure img{max-width:100%;height:auto;border:1px solid #dbe4ee;border-radius:8px}figcaption{color:#627d98;font-size:.88rem}.data-table{display:block;overflow:auto;border-collapse:collapse;width:100%;font-size:.82rem}.data-table th,.data-table td{border:1px solid #dbe4ee;padding:7px 9px;text-align:left;white-space:nowrap}.data-table th{background:#eaf4f4;position:sticky;top:0}code{background:#edf2f7;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}a{color:#0b7285}footer{text-align:center;color:#627d98;padding:30px}@media(max-width:700px){header{padding:30px 18px}section{padding:18px}.data-table{font-size:.74rem}}"""
    document = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>MOOC end-to-end data science report</title><style>{style}</style></head><body><header><h1>MOOC Certification & Learner Segmentation</h1><p>Leakage-controlled classification, outcome-free clustering, interpretation, robustness, and reproducibility</p></header><main class='wrap'>{''.join(sections)}</main><footer>Generated from saved pipeline artifacts at {utc_now()}</footer></body></html>"
    path = REPORTS / "mooc_data_science_report.html"; path.write_text(document, encoding="utf-8")
    # Keep the historical expected report path current rather than leaving a stale report.
    (REPORTS / "student_segmentation_report.html").write_text(document, encoding="utf-8")
    return path


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    ref = reference.replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    cur = current.replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    if len(ref) == 0 or len(cur) == 0:
        return np.nan
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    rp = np.histogram(ref, bins=edges)[0] / len(ref); cp = np.histogram(cur, bins=edges)[0] / len(cur)
    rp = np.clip(rp, 1e-6, None); cp = np.clip(cp, 1e-6, None)
    return float(np.sum((cp - rp) * np.log(cp / rp)))


def run_monitoring_dry_run() -> dict[str, Any]:
    """Build and execute a reproducible monitoring dry-run using held-out data."""
    students = pd.read_parquet(PROCESSED / "students_cleaned.parquet")
    ref = students[students.split == "train"]; cur = students[students.split == "test"]
    pipeline: StudentClusteringPipeline = joblib.load(FINAL_MODELS / "clustering_pipeline.joblib")
    ref_labels = pipeline.predict(ref); cur_labels = pipeline.predict(cur)
    rows = [{"feature": feat, "psi": population_stability_index(ref[feat], cur[feat])} for feat in CLUSTER_FEATURES]
    drift = pd.DataFrame(rows); drift.to_csv(MONITORING / "feature_drift.csv", index=False)
    ref_dist = pd.Series(ref_labels).value_counts(normalize=True); cur_dist = pd.Series(cur_labels).value_counts(normalize=True)
    assignment_l1 = float((ref_dist.subtract(cur_dist, fill_value=0)).abs().sum())
    max_psi = float(drift.psi.max())
    # Empirical dry-run thresholds are governance defaults, not proof of future degradation.
    status = "review" if max_psi >= .20 or assignment_l1 >= .20 else "within_dry_run_bounds"
    config = {"frequency": "per production batch and monthly review", "schema_rule": "exact required feature presence; outcomes rejected",
              "warning_rules": {"feature_psi": .20, "cluster_assignment_l1": .20, "pipeline_failure_rate": .01},
              "response": "Investigate data collection/course mix first; retrain only after confirmed persistent drift and repeat complete workflow."}
    write_json(MONITORING / "monitoring_config.json", config)
    summary = {"generated_at": utc_now(), "mode": "dry-run using historical held-out test cohort, not a future production cohort",
               "reference_n": len(ref), "current_n": len(cur), "max_feature_psi": max_psi, "cluster_assignment_l1": assignment_l1,
               "status": status, "limitations": "A historical random held-out group split cannot demonstrate temporal drift; this validates monitoring code only."}
    write_json(MONITORING / "retraining_decision.json", {**summary, "decision": "do_not_retrain_from_dry_run"})
    history = pd.DataFrame([{**summary, "model_sha256": sha256_file(FINAL_MODELS / "clustering_pipeline.joblib")}])
    history.to_csv(MONITORING / "monitoring_history.csv", index=False)
    table = drift.round(4).to_html(index=False, border=0)
    monitor_html = f"<!doctype html><html><head><meta charset='utf-8'><title>Monitoring dry-run</title><style>body{{font-family:system-ui;max-width:900px;margin:35px auto;line-height:1.5}}table{{border-collapse:collapse}}td,th{{padding:7px;border:1px solid #ccc}}</style></head><body><h1>MOOC model monitoring dry-run</h1><p>Status: <b>{status}</b>. This is a code-path validation using the held-out historical cohort, not evidence of temporal drift.</p><p>Maximum feature PSI: {max_psi:.4f}; assignment-distribution L1 distance: {assignment_l1:.4f}.</p>{table}<h2>Governance action</h2><p>Investigate schema, collection, and course-mix changes before retraining. A replacement must repeat the full split, validation, lock, test, documentation, and responsible-use review.</p></body></html>"
    (MONITORING / "monitoring_report.html").write_text(monitor_html, encoding="utf-8")
    return summary


REQUIRED_ARTIFACTS = [
    "config/project_config.json", "requirements.txt", "README.md",
    "data/processed/data_provenance.json", "data/processed/data_dictionary.csv",
    "data/processed/data_quality_assessment.json", "data/processed/split_manifest.json",
    "data/processed/classification_records.parquet", "data/processed/students_cleaned.parquet",
    "outputs/tables/eda_summary.csv", "outputs/tables/feature_screening.csv",
    "outputs/tables/candidate_models.csv", "outputs/tables/classification_tuning_results.csv",
    "outputs/tables/classification_model_comparison.csv", "outputs/tables/classification_per_class_metrics.csv",
    "outputs/tables/clustering_tuning_results.csv", "outputs/tables/clustering_model_comparison.csv",
    "outputs/tables/cluster_profiles.csv", "outputs/tables/posthoc_validation.csv",
    "outputs/tables/classification_error_analysis.csv", "outputs/tables/clustering_error_analysis.csv",
    "outputs/tables/classification_sensitivity.csv", "outputs/tables/optimization_history.csv",
    "outputs/research/literature_review.md", "outputs/research/model_selection_rationale.md",
    "outputs/reproducibility/training_config.json", "outputs/reproducibility/experiment_log.md",
    "models/final/classification_pipeline.joblib", "models/final/clustering_pipeline.joblib",
    "models/final/classification_model_lock.json", "models/final/clustering_model_lock.json",
    "models/final/classification_model_card.md", "models/final/clustering_model_card.md",
    "outputs/data/classification_test_predictions.parquet", "outputs/data/cluster_assignments.csv",
    "reports/mooc_data_science_report.html", "reports/student_segmentation_report.html",
    "monitoring/monitoring_config.json", "monitoring/monitoring_report.html",
    "monitoring/monitoring_history.csv", "monitoring/retraining_decision.json",
]


REPORT_SECTION_IDS = ["executive-summary", "problem", "literature", "data", "eda", "preprocessing", "classification", "clustering", "interpretation", "sensitivity", "posthoc", "conclusions", "reproducibility"]


def verify_artifacts(raw_hash_before: str) -> dict[str, Any]:
    from html.parser import HTMLParser

    class ReportParser(HTMLParser):
        def __init__(self):
            super().__init__(); self.ids = set(); self.images = []; self.links = []; self.title = False
        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if "id" in values: self.ids.add(values["id"])
            if tag == "img": self.images.append(values.get("src", ""))
            if tag == "a": self.links.append(values.get("href", ""))
            if tag == "title": self.title = True

    checks = []
    for rel in REQUIRED_ARTIFACTS:
        path = ROOT / rel; checks.append({"artifact": rel, "exists": path.exists(), "nonempty": path.exists() and path.stat().st_size > 0, "size_bytes": path.stat().st_size if path.exists() else 0})
    report_path = REPORTS / "mooc_data_science_report.html"; parser = ReportParser(); parser.feed(report_path.read_text(encoding="utf-8"))
    html_checks = {"parse_completed": True, "title_present": parser.title, "section_ids_present": sorted(parser.ids),
                   "all_required_sections": all(section in parser.ids for section in REPORT_SECTION_IDS),
                   "image_count": len(parser.images), "all_images_embedded_and_nonempty": all(src.startswith("data:image/png;base64,") and len(src) > 100 for src in parser.images),
                   "links": parser.links, "all_links_http_or_anchor": all(link.startswith(("https://", "http://", "#")) for link in parser.links)}
    raw_hash_after = sha256_file(RAW)
    summary = {"checked_at": utc_now(), "artifacts": checks, "html": html_checks,
               "raw_sha256_before": raw_hash_before, "raw_sha256_after": raw_hash_after, "raw_unchanged": raw_hash_before == raw_hash_after,
               "all_required_artifacts_ok": all(x["exists"] and x["nonempty"] for x in checks),
               "overall_pass": all(x["exists"] and x["nonempty"] for x in checks) and html_checks["all_required_sections"] and html_checks["all_images_embedded_and_nonempty"] and html_checks["all_links_http_or_anchor"] and raw_hash_before == raw_hash_after}
    write_json(REPORTS / "report_manifest.json", {"report": str(report_path.relative_to(ROOT)), "sha256": sha256_file(report_path), **html_checks})
    write_json(REPRO / "artifact_check.json", summary)
    if not summary["overall_pass"]:
        raise RuntimeError("Required artifact or HTML validation failed; inspect artifact_check.json")
    return summary


def run_all() -> dict[str, Any]:
    ensure_dirs(); started = time.perf_counter(); start_time = utc_now(); raw_hash = sha256_file(RAW)
    stages = []; status = "success"; failure = None
    try:
        for name, function in [
            ("data_acquisition_quality_splitting_eda", run_data_stage),
            ("classification_training_selection_test", train_classification),
            ("clustering_training_selection_test", train_clustering),
            ("clustering_posthoc_validation", posthoc_cluster_validation),
        ]:
            t0 = time.perf_counter(); result = function(); stages.append({"stage": name, "status": "success", "seconds": time.perf_counter() - t0, "summary": result if name != "clustering_training_selection_test" else {k: v for k, v in result.items() if k != "assignments"}})
        class_result = stages[1]["summary"]; cluster_result = {k: v for k, v in stages[2]["summary"].items() if k != "assignments"}
        t0 = time.perf_counter(); create_documentation(class_result, cluster_result); stages.append({"stage": "documentation_and_reproducibility", "status": "success", "seconds": time.perf_counter() - t0})
        t0 = time.perf_counter(); monitor = run_monitoring_dry_run(); stages.append({"stage": "monitoring_dry_run", "status": "success", "seconds": time.perf_counter() - t0, "summary": monitor})
        t0 = time.perf_counter(); report = generate_report(); stages.append({"stage": "html_report", "status": "success", "seconds": time.perf_counter() - t0, "path": str(report.relative_to(ROOT))})
        t0 = time.perf_counter(); verification = verify_artifacts(raw_hash); stages.append({"stage": "artifact_verification", "status": "success", "seconds": time.perf_counter() - t0, "overall_pass": verification["overall_pass"]})
    except Exception as exc:
        status = "failed"; failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        stages.append({"stage": "failure", "status": "failed", "evidence": failure})
        raise
    finally:
        manifest = {"started_at": start_time, "completed_at": utc_now(), "status": status, "elapsed_seconds": time.perf_counter() - started,
                    "command": f"{sys.executable} run_project.py", "raw_sha256_before": raw_hash,
                    "raw_sha256_after": sha256_file(RAW), "raw_unchanged": raw_hash == sha256_file(RAW), "stages": stages, "failure": failure}
        write_json(REPRO / "run_manifest.json", manifest)
    return {"status": status, "stages": stages, "elapsed_seconds": time.perf_counter() - started}
