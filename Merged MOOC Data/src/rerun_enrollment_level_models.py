"""Rerun MOOC analytics at enrollment-record level (575,060 rows).

This script intentionally does not reuse the previous student-level modelling
outputs.  It reads the cleaned enrollment table, joins the enrollment-level
target table, trains/evaluates fresh unsupervised, supervised, deep-learning,
and text/LLM-style baselines, writes real tables/figures, and injects a concise
audit block into the existing dashboard.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, Birch, KMeans, MiniBatchKMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    adjusted_rand_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    calinski_harabasz_score,
    confusion_matrix,
    davies_bouldin_score,
    f1_score,
    normalized_mutual_info_score,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures" / "enrollment_level"
REPRO = ROOT / "outputs" / "reproducibility"
REPORT = ROOT / "reports" / "student_segmentation_report.html"
SEED = 42


def ensure_dirs() -> None:
    for path in (TABLES, FIGURES, REPRO):
        path.mkdir(parents=True, exist_ok=True)


def read_data() -> pd.DataFrame:
    enrollments = pd.read_parquet(ROOT / "data" / "processed" / "enrollments_cleaned.parquet")
    outcomes = pd.read_parquet(ROOT / "data" / "quarantine" / "supervised_outcomes_cleaned.parquet")
    keys = ["userid_DI", "course_id", "institute", "year", "semester"]
    target_cols = keys + ["certified", "grade", "viewed", "explored", "eligible_for_supervised_target"]
    frame = enrollments.merge(outcomes[target_cols], on=keys, how="left", validate="one_to_one")
    frame["certified"] = frame["certified"].fillna(0).astype(int)
    frame["eligible_for_supervised_target"] = frame["eligible_for_supervised_target"].fillna(False).astype(bool)
    return frame


def feature_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    numeric = [
        "nevents_filled",
        "ndays_act_filled",
        "nplay_video_filled",
        "nchapters_filled",
        "nforum_posts_filled",
        "events_percentile_within_course",
        "active_days_percentile_within_course",
        "video_plays_percentile_within_course",
        "chapters_percentile_within_course",
        "forum_posts_percentile_within_course",
        "age_clean",
        "age_missing",
        "nevents_missing",
        "ndays_act_missing",
        "nplay_video_missing",
        "nchapters_missing",
        "nforum_posts_missing",
        "date_inversion_flag",
        "date_missing_flag",
        "source_count",
    ]
    categorical = ["course_id", "institute", "year", "semester", "gender_clean", "LoE_clean", "country_clean", "source_dataset"]
    numeric = [c for c in numeric if c in df.columns]
    categorical = [c for c in categorical if c in df.columns]
    X = df[numeric + categorical].copy()
    for col in numeric:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    for col in categorical:
        X[col] = X[col].astype("string").fillna("Unknown")
    return X, numeric, categorical


def preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", RobustScaler())]), numeric),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=50))]), categorical),
        ],
        sparse_threshold=0.3,
    )


def safe_cluster_metrics(X: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    labels = np.asarray(labels)
    unique = np.unique(labels)
    if len(unique) < 2 or len(unique) >= len(labels):
        return {"silhouette": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan, "smallest_cluster_pct": np.nan, "largest_cluster_pct": np.nan}
    shares = pd.Series(labels).value_counts(normalize=True)
    return {
        "silhouette": float(silhouette_score(X, labels)),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
        "smallest_cluster_pct": float(shares.min() * 100),
        "largest_cluster_pct": float(shares.max() * 100),
    }


def run_unsupervised(df: pd.DataFrame, X: pd.DataFrame, numeric: list[str], categorical: list[str]) -> dict:
    rng = np.random.default_rng(SEED)
    sample_n = min(20000, len(df))
    idx = rng.choice(len(df), sample_n, replace=False)
    X_sample_raw = X.iloc[idx].reset_index(drop=True)
    prep = preprocessor(numeric, categorical)
    X_sample = prep.fit_transform(X_sample_raw)
    if hasattr(X_sample, "toarray"):
        X_sample = X_sample.toarray()
    if X_sample.shape[1] > 25:
        X_metric = TruncatedSVD(n_components=25, random_state=SEED).fit_transform(X_sample)
    else:
        X_metric = np.asarray(X_sample)

    k_rows = []
    for k in range(2, 11):
        t0 = time.perf_counter()
        model = KMeans(n_clusters=k, n_init=10, random_state=SEED)
        labels = model.fit_predict(X_metric)
        metrics = safe_cluster_metrics(X_metric, labels)
        half = sample_n // 2
        a = KMeans(n_clusters=k, n_init=5, random_state=SEED + 1).fit_predict(X_metric[:half])
        b = KMeans(n_clusters=k, n_init=5, random_state=SEED + 2).fit_predict(X_metric[:half])
        metrics.update(
            {
                "k": k,
                "inertia": float(model.inertia_),
                "resample_ari": float(adjusted_rand_score(a, b)),
                "resample_nmi": float(normalized_mutual_info_score(a, b)),
                "runtime_sec": time.perf_counter() - t0,
            }
        )
        k_rows.append(metrics)
    k_df = pd.DataFrame(k_rows)
    for col, asc in [("silhouette", False), ("davies_bouldin", True), ("calinski_harabasz", False), ("resample_ari", False), ("resample_nmi", False)]:
        k_df[f"rank_{col}"] = k_df[col].rank(ascending=asc, method="min")
    k_df["rank_inertia"] = np.log(k_df["inertia"]).rank(ascending=True, method="min")
    k_df["mean_metric_rank"] = k_df[[c for c in k_df.columns if c.startswith("rank_")]].mean(axis=1)
    selected_k = int(k_df.sort_values(["mean_metric_rank", "k"]).iloc[0]["k"])
    k_df["selected_k"] = k_df["k"].eq(selected_k)
    k_df.to_csv(TABLES / "enrollment_k_selection_metrics.csv", index=False)

    families = {
        "K-Means": KMeans(n_clusters=selected_k, n_init=20, random_state=SEED),
        "MiniBatch K-Means": MiniBatchKMeans(n_clusters=selected_k, n_init=10, random_state=SEED, batch_size=2048),
        "Gaussian Mixture": GaussianMixture(n_components=selected_k, covariance_type="diag", random_state=SEED),
        "BIRCH": Birch(n_clusters=selected_k),
        "Agglomerative": AgglomerativeClustering(n_clusters=selected_k),
    }
    comp_rows = []
    best_labels = None
    best_family = None
    for name, model in families.items():
        t0 = time.perf_counter()
        labels = model.fit_predict(X_metric) if hasattr(model, "fit_predict") else model.fit(X_metric).predict(X_metric)
        row = {"family": name, "k": selected_k, "sample_size": sample_n, "runtime_sec": time.perf_counter() - t0}
        row.update(safe_cluster_metrics(X_metric, labels))
        comp_rows.append(row)
    comp = pd.DataFrame(comp_rows)
    comp["rank_silhouette"] = comp["silhouette"].rank(ascending=False, method="min")
    comp["rank_davies_bouldin"] = comp["davies_bouldin"].rank(ascending=True, method="min")
    comp["rank_calinski_harabasz"] = comp["calinski_harabasz"].rank(ascending=False, method="min")
    comp["mean_rank"] = comp[["rank_silhouette", "rank_davies_bouldin", "rank_calinski_harabasz"]].mean(axis=1)
    selected_row = comp.sort_values(["mean_rank", "runtime_sec"]).iloc[0]
    comp["selected"] = comp["family"].eq(selected_row["family"])
    comp.to_csv(TABLES / "enrollment_unsupervised_model_comparison.csv", index=False)
    best_family = str(selected_row["family"])
    best_model = families[best_family]
    best_labels = best_model.fit_predict(X_metric) if hasattr(best_model, "fit_predict") else best_model.fit(X_metric).predict(X_metric)
    profile = pd.DataFrame({"cluster": best_labels}).value_counts().reset_index(name="count")
    profile["share_pct"] = profile["count"] / sample_n * 100
    profile.to_csv(TABLES / "enrollment_cluster_profile_sample.csv", index=False)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    metrics = [("inertia", "lower"), ("silhouette", "higher"), ("davies_bouldin", "lower"), ("calinski_harabasz", "higher"), ("resample_ari", "higher"), ("resample_nmi", "higher")]
    for ax, (m, direction) in zip(axes.ravel(), metrics):
        ax.plot(k_df["k"], k_df[m], marker="o")
        ax.axvline(selected_k, color="crimson", linestyle="--", label=f"K={selected_k}")
        ax.set_title(f"{m} ({direction} is better)")
        ax.set_xlabel("K")
        ax.grid(alpha=0.25)
    axes.ravel()[0].legend()
    fig.suptitle("Enrollment-level multi-metric K selection (575,060 base; 20,000 sample)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "enrollment_k_selection_6_metrics.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(profile["cluster"].astype(str), profile["share_pct"], color="#3b82f6")
    ax.set_title(f"Enrollment Persona Shares · {best_family}, K={selected_k}", fontweight="bold")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Share of sampled enrollment rows (%)")
    fig.tight_layout()
    fig.savefig(FIGURES / "enrollment_persona_shares.png", dpi=180)
    plt.close(fig)
    return {"sample_size": sample_n, "selected_k": selected_k, "selected_family": best_family, "selected_metrics": selected_row.to_dict()}


def best_threshold(y_val: np.ndarray, prob: np.ndarray) -> float:
    grid = np.linspace(0.05, 0.95, 91)
    scores = []
    for t in grid:
        pred = (prob >= t).astype(int)
        scores.append(f1_score(y_val, pred, zero_division=0))
    return float(grid[int(np.argmax(scores))])


def evaluate_models(df: pd.DataFrame, X: pd.DataFrame, numeric: list[str], categorical: list[str], prefix: str, deep: bool = False) -> dict:
    frame = df[df["eligible_for_supervised_target"]].copy()
    y = frame["certified"].astype(int).to_numpy()
    X_frame = X.loc[frame.index]
    X_train, X_tmp, y_train, y_tmp = train_test_split(X_frame, y, test_size=0.30, random_state=SEED, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=0.50, random_state=SEED, stratify=y_tmp)
    prep = preprocessor(numeric, categorical)
    if deep:
        models = {
            "mlp_64": MLPClassifier(hidden_layer_sizes=(64,), max_iter=35, random_state=SEED, early_stopping=True),
            "mlp_128_64": MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=35, random_state=SEED, early_stopping=True),
            "mlp_64_32": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=35, random_state=SEED, early_stopping=True),
        }
    else:
        models = {
            "logistic_regression": LogisticRegression(max_iter=500, class_weight="balanced", n_jobs=1),
            "random_forest": RandomForestClassifier(n_estimators=120, max_depth=14, class_weight="balanced_subsample", n_jobs=1, random_state=SEED),
            "extra_trees": ExtraTreesClassifier(n_estimators=120, max_depth=14, class_weight="balanced", n_jobs=1, random_state=SEED),
            "hist_gradient_boosting": HistGradientBoostingClassifier(max_iter=120, random_state=SEED),
            "decision_tree": DecisionTreeClassifier(max_depth=12, class_weight="balanced", random_state=SEED),
            "naive_bayes": GaussianNB(),
            "linear_svm": LinearSVC(class_weight="balanced", random_state=SEED),
        }
    rows = []
    cms = []
    for model_id, model in models.items():
        t0 = time.perf_counter()
        if model_id == "naive_bayes":
            pipe = Pipeline([("prep", prep), ("dense", _DenseTransformer()), ("model", model)])
        else:
            pipe = Pipeline([("prep", prep), ("model", model)])
        pipe.fit(X_train, y_train)
        if hasattr(pipe.named_steps["model"], "predict_proba"):
            val_prob = pipe.predict_proba(X_val)[:, 1]
            test_prob = pipe.predict_proba(X_test)[:, 1]
        elif hasattr(pipe.named_steps["model"], "decision_function"):
            val_score = pipe.decision_function(X_val)
            test_score = pipe.decision_function(X_test)
            val_prob = 1 / (1 + np.exp(-val_score))
            test_prob = 1 / (1 + np.exp(-test_score))
        else:
            val_prob = pipe.predict(X_val)
            test_prob = pipe.predict(X_test)
        threshold = best_threshold(y_val, val_prob)
        pred = (test_prob >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
        row = {
            "model_id": model_id,
            "model_name": model_id.replace("_", " ").title(),
            "runtime_sec": time.perf_counter() - t0,
            "threshold_from_validation": threshold,
            "test_pr_auc": average_precision_score(y_test, test_prob),
            "test_roc_auc": roc_auc_score(y_test, test_prob),
            "test_brier": brier_score_loss(y_test, np.clip(test_prob, 0, 1)),
            "test_balanced_accuracy": balanced_accuracy_score(y_test, pred),
            "test_precision": precision_score(y_test, pred, zero_division=0),
            "test_recall": recall_score(y_test, pred, zero_division=0),
            "test_f1": f1_score(y_test, pred, zero_division=0),
            "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        }
        rows.append(row)
        cms.append({"model_id": model_id, "tn": tn, "fp": fp, "fn": fn, "tp": tp})
    out = pd.DataFrame(rows).sort_values(["test_pr_auc", "test_f1"], ascending=False)
    out["selected"] = False
    out.loc[out.index[0], "selected"] = True
    out.to_csv(TABLES / f"enrollment_{prefix}_model_comparison.csv", index=False)
    pd.DataFrame(cms).to_csv(TABLES / f"enrollment_{prefix}_confusion_matrices.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(out["model_name"], out["test_pr_auc"], color="#2563eb")
    ax.set_ylabel("Test PR-AUC")
    ax.set_title(f"Enrollment-level {prefix.replace('_', ' ').title()} Model Comparison", fontweight="bold")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(FIGURES / f"enrollment_{prefix}_model_comparison.png", dpi=180)
    plt.close(fig)
    return {"eligible_rows": int(len(frame)), "positive_rows": int(y.sum()), "split": {"train": len(X_train), "validation": len(X_val), "test": len(X_test)}, "selected": out.iloc[0].to_dict()}


class _DenseTransformer:
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.toarray() if hasattr(X, "toarray") else X


def row_to_text(row: pd.Series) -> str:
    return (
        f"Enrollment in course {row.get('course_id')} from {row.get('institute')} during {row.get('year')} {row.get('semester')}. "
        f"Events {row.get('nevents_filled')}, active days {row.get('ndays_act_filled')}, video plays {row.get('nplay_video_filled')}, "
        f"chapters {row.get('nchapters_filled')}, forum posts {row.get('nforum_posts_filled')}. "
        f"Course percentiles: events {row.get('events_percentile_within_course')}, active days {row.get('active_days_percentile_within_course')}, "
        f"video {row.get('video_plays_percentile_within_course')}, chapters {row.get('chapters_percentile_within_course')}, forum {row.get('forum_posts_percentile_within_course')}. "
        f"Demographics: gender {row.get('gender_clean')}, education {row.get('LoE_clean')}, country {row.get('country_clean')}."
    )


def run_llm_text(df: pd.DataFrame) -> dict:
    frame = df[df["eligible_for_supervised_target"]].sample(min(20000, int(df["eligible_for_supervised_target"].sum())), random_state=SEED).copy()
    frame["text"] = frame.apply(row_to_text, axis=1)
    y = frame["certified"].astype(int).to_numpy()
    X_train, X_tmp, y_train, y_tmp = train_test_split(frame["text"], y, test_size=0.30, random_state=SEED, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=0.50, random_state=SEED, stratify=y_tmp)
    configs = {
        "tfidf_unigram_logistic": TfidfVectorizer(ngram_range=(1, 1), min_df=2, max_features=20000),
        "tfidf_bigram_logistic": TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=30000),
        "tfidf_svd_logistic": Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=30000)), ("svd", TruncatedSVD(n_components=128, random_state=SEED)), ("scale", StandardScaler())]),
    }
    rows = []
    for model_id, vectorizer in configs.items():
        t0 = time.perf_counter()
        pipe = Pipeline([("vec", vectorizer), ("clf", LogisticRegression(max_iter=500, class_weight="balanced"))])
        pipe.fit(X_train, y_train)
        val_prob = pipe.predict_proba(X_val)[:, 1]
        test_prob = pipe.predict_proba(X_test)[:, 1]
        threshold = best_threshold(y_val, val_prob)
        pred = (test_prob >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
        rows.append({
            "model_id": model_id,
            "model_name": model_id.replace("_", " ").title(),
            "runtime_sec": time.perf_counter() - t0,
            "threshold_from_validation": threshold,
            "test_pr_auc": average_precision_score(y_test, test_prob),
            "test_roc_auc": roc_auc_score(y_test, test_prob),
            "test_balanced_accuracy": balanced_accuracy_score(y_test, pred),
            "test_precision": precision_score(y_test, pred, zero_division=0),
            "test_recall": recall_score(y_test, pred, zero_division=0),
            "test_f1": f1_score(y_test, pred, zero_division=0),
            "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        })
    out = pd.DataFrame(rows).sort_values(["test_pr_auc", "test_f1"], ascending=False)
    out["selected"] = False
    out.loc[out.index[0], "selected"] = True
    out.to_csv(TABLES / "enrollment_llm_text_model_comparison.csv", index=False)
    return {"sample_rows": len(frame), "split": {"train": len(X_train), "validation": len(X_val), "test": len(X_test)}, "selected": out.iloc[0].to_dict()}


def update_dashboard(manifest: dict) -> None:
    html = REPORT.read_text()
    block = f"""
      <div class="card accent" id="enrollment-rerun-results">
        <h3 data-th="ผลรันโมเดลใหม่จากข้อมูล 575,060 รายการลงทะเบียน" data-en="Fresh model rerun on 575,060 enrollment records">ผลรันโมเดลใหม่จากข้อมูล 575,060 รายการลงทะเบียน</h3>
        <p>รันใหม่จาก <b>enrollments_cleaned.parquet</b> โดยใช้ข้อมูลรายการลงทะเบียนหลังทำความสะอาดจำนวน <b>{manifest['records']:,}</b> แถว และ join target ระดับรายการลงทะเบียนจาก <b>supervised_outcomes_cleaned.parquet</b> ได้ {manifest['supervised']['eligible_rows']:,} แถวที่ใช้กับงาน supervised/deep.</p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>งาน</th><th>ข้อมูลที่ใช้</th><th>โมเดล/ผลที่เลือก</th><th>Metric หลัก</th><th>ไฟล์ผลลัพธ์</th></tr></thead>
            <tbody>
              <tr><td>Unsupervised</td><td>sample {manifest['unsupervised']['sample_size']:,} จาก 575,060</td><td>{manifest['unsupervised']['selected_family']} · K={manifest['unsupervised']['selected_k']}</td><td>Silhouette {manifest['unsupervised']['selected_metrics'].get('silhouette', float('nan')):.4f}</td><td>enrollment_k_selection_metrics.csv</td></tr>
              <tr><td>Supervised ML</td><td>{manifest['supervised']['eligible_rows']:,} eligible rows</td><td>{manifest['supervised']['selected']['model_name']}</td><td>PR-AUC {manifest['supervised']['selected']['test_pr_auc']:.4f} · F1 {manifest['supervised']['selected']['test_f1']:.4f}</td><td>enrollment_supervised_model_comparison.csv</td></tr>
              <tr><td>Deep Learning</td><td>{manifest['deep']['eligible_rows']:,} eligible rows</td><td>{manifest['deep']['selected']['model_name']}</td><td>PR-AUC {manifest['deep']['selected']['test_pr_auc']:.4f} · F1 {manifest['deep']['selected']['test_f1']:.4f}</td><td>enrollment_deep_model_comparison.csv</td></tr>
              <tr><td>LLM/Text</td><td>sample {manifest['llm_text']['sample_rows']:,} จาก 575,060</td><td>{manifest['llm_text']['selected']['model_name']}</td><td>PR-AUC {manifest['llm_text']['selected']['test_pr_auc']:.4f} · F1 {manifest['llm_text']['selected']['test_f1']:.4f}</td><td>enrollment_llm_text_model_comparison.csv</td></tr>
            </tbody>
          </table>
        </div>
        <figure class="chart-card">
          <img src="../outputs/figures/enrollment_level/enrollment_k_selection_6_metrics.png" alt="Enrollment-level K selection">
          <figcaption>กราฟเลือก K ใหม่จากข้อมูลระดับรายการลงทะเบียน โดยดู Inertia, Silhouette, Davies-Bouldin, Calinski-Harabasz, ARI และ NMI พร้อมเส้น K ที่เลือกจาก mean metric rank.</figcaption>
        </figure>
        <figure class="chart-card">
          <img src="../outputs/figures/enrollment_level/enrollment_supervised_model_comparison.png" alt="Enrollment-level supervised model comparison">
          <figcaption>กราฟเปรียบเทียบโมเดล supervised จากข้อมูล 575,060 รายการลงทะเบียน โดยใช้ PR-AUC เป็น metric หลักเพราะ class ผ่าน/ไม่ผ่านไม่สมดุล.</figcaption>
        </figure>
      </div>
"""
    start = html.find('<div class="card accent" id="enrollment-rerun-results">')
    if start != -1:
        end = html.find("</div>\n", start) + len("</div>\n")
        html = html[:start] + block + html[end:]
    else:
        anchor = '<div class="card accent" id="data-split-fairness-audit">'
        idx = html.find(anchor)
        html = html[:idx] + block + "\n" + html[idx:] if idx != -1 else html.replace("</body>", block + "\n</body>")
    REPORT.write_text(html)


def main() -> None:
    ensure_dirs()
    t0 = time.perf_counter()
    df = read_data()
    X, numeric, categorical = feature_frame(df)
    unsup = run_unsupervised(df, X, numeric, categorical)
    sup = evaluate_models(df, X, numeric, categorical, "supervised", deep=False)
    deep = evaluate_models(df, X, numeric, categorical, "deep", deep=True)
    llm = run_llm_text(df)
    manifest = {
        "status": "completed",
        "run_timestamp": pd.Timestamp.now(tz="Asia/Bangkok").isoformat(),
        "records": int(len(df)),
        "source": "data/processed/enrollments_cleaned.parquet",
        "target_source": "data/quarantine/supervised_outcomes_cleaned.parquet",
        "features": {"numeric": numeric, "categorical": categorical},
        "unsupervised": unsup,
        "supervised": sup,
        "deep": deep,
        "llm_text": llm,
        "runtime_sec": time.perf_counter() - t0,
    }
    (REPRO / "enrollment_level_rerun_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str))
    update_dashboard(manifest)
    print(json.dumps({"status": "completed", "records": len(df), "runtime_sec": round(manifest["runtime_sec"], 2)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
