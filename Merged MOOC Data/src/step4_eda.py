"""Step 4: Exploratory Data Analysis & Manifold Projections (PCA & UMAP)."""

import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler, StandardScaler
try:
    import umap
except ModuleNotFoundError:
    umap = None

STUDENTS_PATH = os.path.join("data", "processed", "students_cleaned.parquet")
OUTPUT_TABLES = os.path.join("outputs", "tables")
OUTPUT_FIGS = os.path.join("outputs", "figures", "eda")
SAMPLING_PATH = os.path.join("data", "processed", "sampling_report.json")
CONFIG_PATH = os.path.join("config", "project_config.json")

def run_eda():
    print("=" * 70)
    print("STEP 4: EXPLORATORY DATA ANALYSIS & MANIFOLD INSPECTION")
    print("=" * 70)
    
    os.makedirs(OUTPUT_TABLES, exist_ok=True)
    os.makedirs(OUTPUT_FIGS, exist_ok=True)
    
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)
    sample_size = config.get("metric_sample_size", 25000)
    seed = config.get("random_seed", 42)
    
    df = pd.read_parquet(STUDENTS_PATH)
    total_students = len(df)
    print(f"[+] Loaded cleaned student cohort: {total_students:,} students")
    
    # 1. Descriptive Summary Table
    num_cols = [
        "n_courses", "n_institutes", "total_events", "mean_events_per_course",
        "total_active_days", "mean_active_days_per_course", "total_video_plays",
        "total_chapters", "mean_chapters_per_course", "total_forum_posts",
        "demog_age", "demog_loe_rank", "overall_span_days", "event_intensity",
        "video_intensity", "chapters_per_day"
    ]
    
    eda_summary = df[num_cols].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T
    eda_summary["null_count"] = df[num_cols].isnull().sum()
    eda_summary["null_pct"] = (eda_summary["null_count"] / total_students) * 100.0
    eda_summary["skewness"] = df[num_cols].skew(numeric_only=True)
    eda_summary["kurtosis"] = df[num_cols].kurtosis(numeric_only=True)
    eda_summary["zero_count"] = (df[num_cols] == 0).sum()
    eda_summary["zero_pct"] = eda_summary["zero_count"] / total_students * 100.0
    q1 = df[num_cols].quantile(0.25)
    q3 = df[num_cols].quantile(0.75)
    iqr = q3 - q1
    outlier_mask = (df[num_cols].lt(q1 - 1.5 * iqr)) | (df[num_cols].gt(q3 + 1.5 * iqr))
    eda_summary["iqr_outlier_count"] = outlier_mask.sum()
    eda_summary["iqr_outlier_pct"] = eda_summary["iqr_outlier_count"] / total_students * 100.0
    eda_summary_path = os.path.join(OUTPUT_TABLES, "eda_summary.csv")
    eda_summary.to_csv(eda_summary_path)
    print(f"[+] EDA descriptive summary saved to: {eda_summary_path}")

    diagnostics = eda_summary.reset_index().rename(columns={"index": "feature"})
    diagnostics.to_csv(os.path.join(OUTPUT_TABLES, "distribution_diagnostics.csv"), index=False)
    
    # 2. Correlation & Screening
    corr = df[num_cols].corr(method="spearman")
    corr_path = os.path.join(OUTPUT_TABLES, "feature_screening.csv")
    corr.to_csv(corr_path)
    print(f"[+] Feature correlation matrix saved to: {corr_path}")
    
    # Visual 1: Distribution of Core Behavioral Features
    print("[+] Plotting feature distributions...")
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    plot_feats = [
        ("total_events", "Total Events (Log1p)", True),
        ("total_active_days", "Total Active Days (Log1p)", True),
        ("total_video_plays", "Total Video Plays (Log1p)", True),
        ("total_chapters", "Total Chapters Accessed", False),
        ("demog_age", "Student Age", False),
        ("overall_span_days", "Activity Span (Days)", False)
    ]
    for idx, (col, label, is_log) in enumerate(plot_feats):
        ax = axes[idx // 3, idx % 3]
        vals = df[col].dropna()
        if is_log:
            vals = np.log1p(vals)
        sns.histplot(vals, bins=40, kde=True, ax=ax, color="#1f77b4", edgecolor="none")
        ax.set_title(label, fontsize=12, fontweight="bold")
        ax.set_ylabel("Student Count")
        ax.grid(alpha=0.3)
    plt.tight_layout()
    dist_fig_path = os.path.join(OUTPUT_FIGS, "distributions.png")
    plt.savefig(dist_fig_path, dpi=200)
    plt.close()
    print(f"    Saved: {dist_fig_path}")

    # Visual 1B: Full numerical distribution gallery. Count-like variables are
    # shown after log1p only for visibility; the source data remains unchanged.
    print("[+] Plotting full numerical distribution gallery...")
    count_like = {
        "n_courses", "n_institutes", "total_events", "mean_events_per_course",
        "total_active_days", "mean_active_days_per_course", "total_video_plays",
        "total_chapters", "mean_chapters_per_course", "total_forum_posts",
        "overall_span_days",
    }
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    for ax, col in zip(axes.flat, num_cols):
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        shown = np.log1p(values.clip(lower=0)) if col in count_like else values
        sns.histplot(shown, bins=45, kde=True, ax=ax, color="#163A6B", edgecolor="none")
        suffix = " · log1p display" if col in count_like else ""
        ax.set_title(col.replace("_", " ").title() + suffix, fontsize=10, fontweight="bold")
        ax.set_ylabel("Students")
        ax.grid(alpha=0.2)
    plt.suptitle("Full Student-Level Numerical Distributions", fontsize=17, fontweight="bold", y=1.01)
    plt.tight_layout()
    full_dist_path = os.path.join(OUTPUT_FIGS, "full_distributions.png")
    plt.savefig(full_dist_path, dpi=180, bbox_inches="tight")
    plt.close()

    # Visual 1C: robust boxplots make different units comparable without
    # changing the data used downstream.
    print("[+] Plotting robust-scaled boxplots...")
    display_sample = df[num_cols].sample(min(25000, total_students), random_state=seed).copy()
    display_sample = display_sample.fillna(display_sample.median(numeric_only=True))
    robust_values = RobustScaler().fit_transform(display_sample)
    robust_frame = pd.DataFrame(robust_values, columns=num_cols).clip(-6, 6)
    long_robust = robust_frame.melt(var_name="feature", value_name="robust_z")
    plt.figure(figsize=(16, 8))
    sns.boxplot(data=long_robust, x="robust_z", y="feature", color="#F4B400", fliersize=0)
    plt.axvline(0, color="#163A6B", linewidth=1)
    plt.xlabel("Robust-scaled value, clipped to ±6 for display only")
    plt.ylabel("")
    plt.title("Robust Boxplots: Shape and Outlier Comparison Across Features", fontweight="bold")
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    robust_path = os.path.join(OUTPUT_FIGS, "robust_boxplots.png")
    plt.savefig(robust_path, dpi=180, bbox_inches="tight")
    plt.close()

    # Visual 1D: zero concentration, missingness, and IQR outlier rates.
    print("[+] Plotting data-quality distribution diagnostics...")
    plot_diag = diagnostics.set_index("feature")[["zero_pct", "null_pct", "iqr_outlier_pct"]]
    ax = plot_diag.plot(kind="barh", figsize=(13, 9), color=["#163A6B", "#B63232", "#F4B400"])
    ax.set_xlabel("Percent of students")
    ax.set_ylabel("")
    ax.set_title("Zero, Missing, and IQR-Outlier Profile", fontweight="bold")
    ax.legend(["Zero", "Missing", "IQR outlier"])
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    quality_dist_path = os.path.join(OUTPUT_FIGS, "zero_missing_outlier_profile.png")
    plt.savefig(quality_dist_path, dpi=180, bbox_inches="tight")
    plt.close()

    # Visual 1E: relationships among core behavior volumes. Hexbin density is
    # more legible than plotting hundreds of thousands of overlapping points.
    print("[+] Plotting behavioral relationship diagnostics...")
    rel = df[["total_events", "total_active_days", "total_video_plays", "total_chapters", "total_forum_posts"]].sample(
        min(50000, total_students), random_state=seed
    ).fillna(0)
    pairs = [
        ("total_active_days", "total_events"),
        ("total_video_plays", "total_chapters"),
        ("total_forum_posts", "total_events"),
        ("total_active_days", "total_video_plays"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    for ax, (xcol, ycol) in zip(axes.flat, pairs):
        x = np.log1p(rel[xcol].clip(lower=0))
        y = np.log1p(rel[ycol].clip(lower=0))
        hb = ax.hexbin(x, y, gridsize=45, mincnt=1, bins="log", cmap="viridis")
        ax.set_xlabel(f"log1p({xcol})")
        ax.set_ylabel(f"log1p({ycol})")
        ax.set_title(f"{xcol.replace('_', ' ')} vs {ycol.replace('_', ' ')}", fontweight="bold")
        fig.colorbar(hb, ax=ax, label="log10(bin count)")
    plt.suptitle("Behavioral Relationship and Density Diagnostics", fontsize=16, fontweight="bold")
    plt.tight_layout()
    relationships_path = os.path.join(OUTPUT_FIGS, "behavior_relationships.png")
    plt.savefig(relationships_path, dpi=180, bbox_inches="tight")
    plt.close()

    # Visual 1F: activity outlier diagnostics preserve legitimate heavy users
    # while making their influence and audit thresholds explicit.
    activity_cols = ["total_events", "total_active_days", "total_video_plays", "total_forum_posts"]
    outlier_rows = []
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for ax, column in zip(axes.flat, activity_cols):
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        q1_col, q3_col = values.quantile([.25, .75])
        threshold = q3_col + 1.5 * (q3_col - q1_col)
        outlier_rows.append({
            "feature": column, "q1": q1_col, "q3": q3_col,
            "upper_iqr_threshold": threshold,
            "outlier_students": int(values.gt(threshold).sum()),
            "outlier_pct": float(values.gt(threshold).mean() * 100),
            "p99": float(values.quantile(.99)), "maximum": float(values.max()),
        })
        shown = np.log1p(values.clip(lower=0))
        ax.hist(shown[values.le(threshold)], bins=55, color="#163A6B", alpha=.8, label="Within IQR fence")
        ax.hist(shown[values.gt(threshold)], bins=35, color="#B63232", alpha=.8, label="Above upper fence")
        ax.axvline(np.log1p(max(threshold, 0)), color="#F4B400", linestyle="--", linewidth=2)
        ax.set_title(column.replace("_", " ").title()); ax.set_xlabel("log1p(value)"); ax.set_ylabel("Students")
        ax.legend(fontsize=8); ax.grid(alpha=.2)
    pd.DataFrame(outlier_rows).to_csv(os.path.join(OUTPUT_TABLES, "activity_outlier_audit.csv"), index=False)
    fig.suptitle("Activity Outliers: Explicit IQR Audit, Not Automatic Deletion", fontsize=16, fontweight="bold")
    plt.tight_layout(rect=(0, 0, 1, .96)); plt.savefig(os.path.join(OUTPUT_FIGS, "activity_outlier_diagnostics.png"), dpi=180, bbox_inches="tight"); plt.close()

    # Visual 1G: video quality distinguishes true zeros from missing video data.
    video_fields = [c for c in ["total_video_plays", "video_intensity", "video_missing_records", "video_data_available_rate"] if c in df.columns]
    video_rows = []
    for column in video_fields:
        series = pd.to_numeric(df[column], errors="coerce")
        video_rows.append({"feature": column, "available": True, "missing_pct": float(series.isna().mean()*100), "zero_pct": float(series.eq(0).mean()*100), "median": float(series.median()), "p95": float(series.quantile(.95)), "maximum": float(series.max())})
    video_audit = pd.DataFrame(video_rows)
    video_audit.to_csv(os.path.join(OUTPUT_TABLES, "video_quality_audit.csv"), index=False)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    video_values = df["total_video_plays"].fillna(0)
    axes[0,0].hist(np.log1p(video_values.clip(lower=0)), bins=55, color="#163A6B"); axes[0,0].set_title("Video plays (log1p)")
    axes[0,1].bar(["Zero plays", "At least one play"], [video_values.eq(0).mean()*100, video_values.gt(0).mean()*100], color=["#B63232", "#19734B"]); axes[0,1].set_ylabel("Students (%)"); axes[0,1].set_title("Observed video activity")
    if "video_data_available_rate" in df:
        axes[1,0].hist(df["video_data_available_rate"].dropna(), bins=40, color="#F4B400"); axes[1,0].set_title("Video-data availability rate")
    if "video_missing_records" in df:
        missing = df["video_missing_records"].fillna(0)
        axes[1,1].bar(["No missing record", "≥1 missing record"], [missing.eq(0).mean()*100, missing.gt(0).mean()*100], color=["#19734B", "#B63232"]); axes[1,1].set_ylabel("Students (%)"); axes[1,1].set_title("Missing video fields by student")
    for ax in axes.flat: ax.grid(alpha=.2)
    fig.suptitle("Video Quality Audit: Availability, Missingness, and Structural Zeros", fontsize=16, fontweight="bold")
    plt.tight_layout(rect=(0, 0, 1, .96)); plt.savefig(os.path.join(OUTPUT_FIGS, "video_quality_diagnostics.png"), dpi=180, bbox_inches="tight"); plt.close()
    
    # Visual 2: Correlation Heatmap
    print("[+] Plotting correlation matrix heatmap...")
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr, cmap="coolwarm", vmin=-1, vmax=1, annot=True, fmt=".2f", annot_kws={"size": 8}, cbar=True)
    plt.title("Spearman Rank Correlation of Student Engagement Features", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    corr_fig_path = os.path.join(OUTPUT_FIGS, "correlation_matrix.png")
    plt.savefig(corr_fig_path, dpi=200)
    plt.close()
    print(f"    Saved: {corr_fig_path}")
    
    # Visual 3: Institution Breakdown & Demographics
    print("[+] Plotting demographics and institutional distribution...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    inst_counts = df["institutes_enrolled"].value_counts()
    ax1.pie(inst_counts, labels=inst_counts.index, autopct="%1.1f%%", colors=["#4285F4", "#EA4335", "#FBBC05"], startangle=140)
    ax1.set_title("Institutional Distribution (HarvardX vs MITx vs Cross-Institution)", fontweight="bold")
    
    loe_counts = df["demog_loe"].value_counts()
    sns.barplot(x=loe_counts.values, y=loe_counts.index, hue=loe_counts.index, ax=ax2, palette="Blues_r", legend=False)
    ax2.set_title("Highest Level of Education (LoE)", fontweight="bold")
    ax2.set_xlabel("Student Count")
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    inst_fig_path = os.path.join(OUTPUT_FIGS, "institutes_breakdown.png")
    plt.savefig(inst_fig_path, dpi=200)
    plt.close()
    print(f"    Saved: {inst_fig_path}")
    
    # 3. Dimensionality Reduction: PCA & UMAP on representative sample
    manifold_name = "UMAP" if umap is not None else "PCA fallback"
    print(f"[+] Performing PCA & {manifold_name} manifold inspection on sample of {sample_size:,} students...")
    rng = np.random.default_rng(seed)
    sample_indices = rng.choice(total_students, size=min(sample_size, total_students), replace=False)
    sample_df = df.iloc[sample_indices].copy()

    # Document whether the computational sample resembles the available
    # cohort without consulting any quarantined outcome.
    smd_checks = {}
    for col in num_cols:
        full_values = pd.to_numeric(df[col], errors="coerce")
        sample_values = pd.to_numeric(sample_df[col], errors="coerce")
        full_std = float(full_values.std(ddof=0))
        smd_checks[col] = 0.0 if not np.isfinite(full_std) or full_std == 0 else float(
            abs(sample_values.mean() - full_values.mean()) / full_std
        )
    categorical_checks = {}
    for col in ["institutes_enrolled", "demog_gender", "demog_loe"]:
        full_prop = df[col].fillna("Missing").value_counts(normalize=True)
        sample_prop = sample_df[col].fillna("Missing").value_counts(normalize=True)
        levels = full_prop.index.union(sample_prop.index)
        categorical_checks[col] = float(
            max(abs(float(full_prop.get(level, 0.0)) - float(sample_prop.get(level, 0.0))) for level in levels)
        )
    
    # Numerical feature scaling for manifold projections
    X_raw = sample_df[num_cols].fillna(sample_df[num_cols].median()).values
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_raw)
    
    # Fit PCA
    pca = PCA(n_components=min(10, len(num_cols)), random_state=seed)
    X_pca = pca.fit_transform(X_scaled)
    var_ratio = pca.explained_variance_ratio_
    cum_var = np.cumsum(var_ratio)
    
    # Visual 4: PCA Scree Plot
    plt.figure(figsize=(8, 4.5))
    plt.bar(range(1, len(var_ratio) + 1), var_ratio * 100, alpha=0.7, label="Individual Component Variance (%)", color="#34A853")
    plt.plot(range(1, len(var_ratio) + 1), cum_var * 100, marker="o", color="#1A73E8", linewidth=2, label="Cumulative Variance (%)")
    plt.xlabel("Principal Component", fontweight="bold")
    plt.ylabel("Variance Explained (%)", fontweight="bold")
    plt.title("PCA Scree Plot: Student Feature Space", fontweight="bold")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    pca_fig_path = os.path.join(OUTPUT_FIGS, "pca_variance.png")
    plt.savefig(pca_fig_path, dpi=200)
    plt.close()
    print(f"    Saved: {pca_fig_path}")
    
    # Fit UMAP when available. Otherwise keep the pipeline reproducible with
    # a deterministic PCA fallback instead of blocking the whole EDA refresh.
    if umap is not None:
        print("    Computing UMAP 2D manifold projection...")
        reducer = umap.UMAP(n_neighbors=25, min_dist=0.3, metric="cosine", random_state=seed, n_jobs=1)
        X_manifold = reducer.fit_transform(X_scaled)
        manifold_title = "Non-Linear Manifold: UMAP 2D Projection"
        manifold_x, manifold_y = "UMAP-1", "UMAP-2"
    else:
        print("    UMAP is not installed; using PCA component fallback for the second panel.")
        X_manifold = X_pca[:, [1, 2]] if X_pca.shape[1] >= 3 else X_pca[:, :2]
        manifold_title = "PCA Fallback Projection (UMAP unavailable)"
        manifold_x, manifold_y = "PC2", "PC3" if X_pca.shape[1] >= 3 else "PC2"
    
    # Visual 5: 2D Manifold Visualizations (PCA vs UMAP)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    scatter1 = ax1.scatter(X_pca[:, 0], X_pca[:, 1], c=np.log1p(sample_df["total_events"]), cmap="viridis", alpha=0.4, s=10)
    ax1.set_title(f"Linear Manifold: PCA (PC1 vs PC2)\nExplains {cum_var[1]*100:.1f}% Variance", fontweight="bold")
    ax1.set_xlabel(f"PC1 ({var_ratio[0]*100:.1f}%)")
    ax1.set_ylabel(f"PC2 ({var_ratio[1]*100:.1f}%)")
    fig.colorbar(scatter1, ax=ax1, label="Log(Total Events + 1)")
    ax1.grid(alpha=0.2)
    
    scatter2 = ax2.scatter(X_manifold[:, 0], X_manifold[:, 1], c=np.log1p(sample_df["total_events"]), cmap="viridis", alpha=0.4, s=10)
    ax2.set_title(f"{manifold_title}\n(Color = Interaction Volume)", fontweight="bold")
    ax2.set_xlabel(manifold_x)
    ax2.set_ylabel(manifold_y)
    fig.colorbar(scatter2, ax=ax2, label="Log(Total Events + 1)")
    ax2.grid(alpha=0.2)
    
    plt.tight_layout()
    manifold_fig_path = os.path.join(OUTPUT_FIGS, "manifold_projection.png")
    plt.savefig(manifold_fig_path, dpi=200)
    plt.close()
    print(f"    Saved: {manifold_fig_path}")
    
    # Save Sampling Report
    sampling_report = {
        "full_cohort_size": total_students,
        "sample_size": len(sample_df),
        "purpose": "Reduce memory and runtime for PCA, UMAP, and candidate-model comparison on the large student cohort.",
        "sampling_method": "Simple random sampling without replacement from the student-level table; outcomes were not used.",
        "random_seed": seed,
        "outcomes_used_for_sampling": False,
        "representativeness_checks": {
            "standardized_mean_difference_by_numeric_feature": smd_checks,
            "maximum_absolute_standardized_mean_difference": float(max(smd_checks.values())),
            "maximum_category_proportion_difference": categorical_checks
        },
        "limitations": [
            "Rare behavioral or demographic subgroups can be underrepresented in a finite random sample.",
            "Model conclusions should be checked again on a real future cohort before operational use."
        ],
        "pca_explained_variance_pc1": float(var_ratio[0]),
        "pca_explained_variance_pc2": float(var_ratio[1]),
        "pca_cumulative_variance_top5": float(cum_var[4]),
        "umap_parameters": {"n_neighbors": 25, "min_dist": 0.3, "metric": "cosine"}
    }
    with open(SAMPLING_PATH, "w", encoding="utf-8") as f:
        json.dump(sampling_report, f, indent=2)
    print(f"[+] Sampling report saved to: {SAMPLING_PATH}")

    # Export observed EDA findings and their downstream implications.
    skew_series = df[num_cols].skew(numeric_only=True).sort_values(ascending=False)
    corr_pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    strongest_pair = corr_pairs.abs().idxmax()
    strongest_corr = float(corr.loc[strongest_pair[0], strongest_pair[1]])
    minimal_activity_pct = float((df["total_active_days"] < 5).mean() * 100.0)
    sustained_activity_pct = float((df["total_active_days"] >= 14).mean() * 100.0)
    eda_findings_md = f"""# Exploratory Data Analysis: Key Findings & Downstream Impacts

## 1. Distributional Skewness & Outliers
- **Finding:** The most right-skewed inspected variable is `{skew_series.index[0]}` with observed skewness {skew_series.iloc[0]:.2f}; activity variables have long upper tails.
- **Impact on Step 5 (Feature Engineering):** Standard Euclidean algorithms would be distorted by high-magnitude outliers. Therefore, we mandate a `log1p(x) = log(x + 1)` transformation on count metrics combined with `RobustScaler` (median and IQR) to ensure stable scaling.

## 2. Multicollinearity & Redundancy
- **Finding:** The strongest absolute Spearman relationship among inspected numerical variables is `{strongest_pair[0]}` versus `{strongest_pair[1]}` (rho={strongest_corr:.3f}).
- **Impact on Steps 6-7 (Model Training):** High-dimensional collinearity creates artificial distance stretching in standard Euclidean space. This justifies non-linear latent compression via Deep Autoencoders and manifold projection (PCA/UMAP) to decorrelate features before clustering.

## 3. Class Imbalance & Student Posture
- **Finding:** {minimal_activity_pct:.1f}% of students have fewer than 5 recorded active days, while {sustained_activity_pct:.1f}% have at least 14 active days.
- **Impact on Steps 6-8 (Clustering & Evaluation):** Prevents the use of algorithms that enforce equal cluster sizes. We establish a minimum cluster size threshold of >= 2.0% to guard against trivial singleton clusters while allowing organic population proportions.

## 4. Cross-Institutional Heterogeneity
- **Finding:** Course duration and chapter structures differ between HarvardX humanities/social science courses and MITx engineering/computer science offerings.
- **Impact on Feature Engineering:** We construct normalized intensity ratios (`chapters_per_day`, `video_intensity`, `event_intensity`) that benchmark activity relative to individual learner enrollment span rather than raw course chapter counts.
"""
    os.makedirs("outputs/research", exist_ok=True)
    with open(os.path.join("outputs", "research", "eda_findings.md"), "w", encoding="utf-8") as f:
        f.write(eda_findings_md)
    print(f"[+] EDA findings & downstream impact report saved to: outputs/research/eda_findings.md")
    print("=" * 70)
    print("STEP 4: EXPLORATORY DATA ANALYSIS COMPLETED SUCCESSFULLY.")
    print("=" * 70)

if __name__ == "__main__":
    run_eda()
