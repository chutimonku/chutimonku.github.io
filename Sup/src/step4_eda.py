"""ขั้นตอนที่ 4: การสำรวจข้อมูลเชิงลึก (EDA) และการคัดกรองฟีเจอร์ป้องกันข้อมูลรั่วไหล."""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Thonburi", "Sukhumvit Set", "Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns

STUDENTS_PATH = os.path.join("data", "processed", "students_cleaned.parquet")
LABELS_PATH = os.path.join("data", "labels", "student_labels.parquet")
FIG_DIR = os.path.join("outputs", "figures", "eda")
TABLE_DIR = os.path.join("outputs", "tables")


def run_eda():
    """ดำเนินกระบวนการวิเคราะห์เชิงสำรวจ สถิติเชิงพรรณนา และสร้างกราฟิกสรุปผล."""
    print("=" * 70)
    print("ขั้นตอนที่ 4: การวิเคราะห์ข้อมูลเชิงสำรวจและการคัดกรองฟีเจอร์ (EDA)")
    print("=" * 70)

    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(TABLE_DIR, exist_ok=True)

    df_students = pd.read_parquet(STUDENTS_PATH)
    df_labels = pd.read_parquet(LABELS_PATH)

    merged = pd.merge(df_students, df_labels, on="userid_DI")
    target_col = "certified_student"

    # 1. คำนวณสถิติเชิงพรรณนาของฟีเจอร์ตัวเลข
    numeric_cols = df_students.select_dtypes(include=[np.number]).columns.tolist()

    summary_rows = []
    for col in numeric_cols:
        series = df_students[col].dropna()
        summary_rows.append({
            "feature": col,
            "count": len(series),
            "missing_pct": float(round(df_students[col].isna().mean() * 100, 2)),
            "mean": float(round(series.mean(), 4)),
            "std": float(round(series.std(), 4)),
            "min": float(round(series.min(), 4)),
            "p25": float(round(series.quantile(0.25), 4)),
            "median": float(round(series.median(), 4)),
            "p75": float(round(series.quantile(0.75), 4)),
            "max": float(round(series.max(), 4)),
            "skewness": float(round(series.skew(), 4)),
        })
    df_summary = pd.DataFrame(summary_rows)
    eda_summary_path = os.path.join(TABLE_DIR, "eda_summary.csv")
    df_summary.to_csv(eda_summary_path, index=False)
    print(f"[+] บันทึกสถิติเชิงพรรณนาของฟีเจอร์เรียบร้อยที่: {eda_summary_path}")

    # 2. การคัดกรองฟีเจอร์และความสัมพันธ์สองตัวแปรกับเป้าหมาย (Bivariate Association)
    screening_rows = []
    for col in numeric_cols:
        valid = merged[[col, target_col]].dropna()
        x_vals = valid[col]
        y_vals = valid[target_col]

        # สหสัมพันธ์แบบ Point Biserial Correlation
        corr, p_val = stats.pointbiserialr(x_vals, y_vals)

        mean_non_cert = float(valid.loc[valid[target_col] == 0, col].mean())
        mean_cert = float(valid.loc[valid[target_col] == 1, col].mean())
        median_non_cert = float(valid.loc[valid[target_col] == 0, col].median())
        median_cert = float(valid.loc[valid[target_col] == 1, col].median())

        # การทดสอบ Mann-Whitney U test (สุ่มตัวอย่างเพื่อความรวดเร็วในการประมวลผล)
        sample_size = min(len(valid), 50000)
        sample_valid = valid.sample(n=sample_size, random_state=42)
        u_stat, u_pval = stats.mannwhitneyu(
            sample_valid.loc[sample_valid[target_col] == 1, col],
            sample_valid.loc[sample_valid[target_col] == 0, col],
            alternative="two-sided",
        )

        leakage_warning = abs(corr) > 0.90
        screening_rows.append({
            "feature": col,
            "point_biserial_corr": float(round(corr, 4)),
            "corr_p_value": float(p_val),
            "mean_non_completers": float(round(mean_non_cert, 2)),
            "mean_completers": float(round(mean_cert, 2)),
            "median_non_completers": float(round(median_non_cert, 2)),
            "median_completers": float(round(median_cert, 2)),
            "mann_whitney_u_stat": float(round(u_stat, 1)),
            "mann_whitney_p_val": float(u_pval),
            "leakage_flag": leakage_warning,
            "screening_decision": "Flagged" if leakage_warning else "Approved",
        })

    df_screening = pd.DataFrame(screening_rows).sort_values("point_biserial_corr", ascending=False)
    screening_path = os.path.join(TABLE_DIR, "feature_screening.csv")
    df_screening.to_csv(screening_path, index=False)
    print(f"[+] บันทึกผลการคัดกรองฟีเจอร์เรียบร้อยที่: {screening_path}")

    # 3. การสร้างกราฟิกประกอบรายงาน (Visualizations)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    navy, blue, cyan, violet, mint, coral = "#173B69", "#4F86C6", "#56C2E6", "#7567C8", "#54C6A5", "#EC7063"
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelcolor": "#26364A",
        "text.color": "#26364A",
        "xtick.color": "#44546A",
        "ytick.color": "#44546A",
        "axes.edgecolor": "#D8E2EF",
        "grid.color": "#E7EDF5",
    })

    def style_axis(ax, grid_axis="y"):
        ax.set_facecolor("#FBFDFF")
        ax.grid(True, axis=grid_axis, linewidth=0.8, alpha=0.85)
        ax.grid(False, axis="x" if grid_axis == "y" else "y")
        for spine in ax.spines.values():
            spine.set_color("#D8E2EF")

    # รูปที่ 1: การกระจายตัวของคลาสและความไม่สมดุล (Class Imbalance)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), facecolor="white")

    def draw_distribution(ax, counts, labels, colors, title):
        total = int(counts.sum())
        percentages = counts.values / total * 100
        positions = np.arange(len(labels))
        bars = ax.barh(positions, percentages, color=colors, height=0.56, edgecolor="white")
        ax.set_yticks(positions, labels=labels)
        ax.invert_yaxis()
        for bar, value, pct in zip(bars, counts.values, percentages):
            if pct >= 18:
                x, align, color = pct - 2, "right", "white"
            else:
                x, align, color = pct + 1.2, "left", "#26364A"
            ax.text(x, bar.get_y() + bar.get_height() / 2,
                    f"{int(value):,} คน  ·  {pct:.2f}%", ha=align, va="center",
                    fontsize=10, fontweight="bold", color=color)
        ax.set_xlim(0, 100)
        ax.set_xlabel("สัดส่วนนักศึกษา (%)", fontsize=11, fontweight="bold")
        ax.set_title(title, pad=14, fontsize=12, fontweight="bold", color=navy)
        style_axis(ax, "x")

    cert_counts = df_labels["certified_student"].value_counts().sort_index()
    draw_distribution(
        axes[0], cert_counts, ["ไม่สำเร็จ (Non-completer)", "ได้รับใบจบ (Certified)"], [blue, mint],
        "การกระจายตัวของตัวแปรเป้าหมายหลัก (Primary Target)",
    )

    tier_counts = df_labels["outcome_tier"].value_counts().sort_index()
    draw_distribution(
        axes[1], tier_counts, ["ได้รับใบจบ (Completer)", "เข้าเรียนลึกซึ้ง (Explored)", "ออกกลางคัน (Dropout)"], [mint, violet, coral],
        "การกระจายตัวของกลุ่มผลลัพธ์ 3 ระดับ (Observed Tiers)",
    )
    fig.suptitle("ความไม่สมดุลของคลาสข้อมูลและการกระจายตัวของผลลัพธ์", fontsize=14, fontweight="bold", color=navy)
    plt.tight_layout(rect=[0, 0, 1, 0.90])
    fig1_path = os.path.join(FIG_DIR, "class_imbalance.png")
    fig.savefig(fig1_path, dpi=180)
    plt.close(fig)

    # รูปที่ 2: การกระจายตัวของกิจกรรมแยกตามสถานะการได้รับใบจบ
    activity_metrics = [
        ("total_active_days", "จำนวนวันที่มีกิจกรรม (Active Days)"),
        ("total_events", "จำนวนเหตุการณ์ทั้งหมด (Total Events)"),
        ("total_chapters", "จำนวนบทเรียนที่เข้าถึง (Chapters)"),
        ("total_video_plays", "จำนวนการเล่นวิดีโอ (Video Plays)"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), facecolor="white")
    for ax, (feat, label) in zip(axes.flatten(), activity_metrics):
        temp = merged[[feat, target_col]].dropna().copy()
        temp["log_feat"] = np.log1p(temp[feat])
        sns.boxplot(
            data=temp,
            x=target_col,
            y="log_feat",
            ax=ax,
            hue=target_col,
            palette=["#B9C8D8", mint],
            showfliers=False,
            linewidth=1.2,
            legend=False,
        )
        ax.set_xticks([0, 1], ["ไม่สำเร็จการศึกษา", "ได้รับใบจบ"])
        ax.set_title(label, pad=10, fontsize=12, fontweight="bold", color=navy)
        ax.set_xlabel("")
        ax.set_ylabel("ค่าหลังแปลง log1p", fontsize=10)
        style_axis(ax)
    fig.suptitle("การกระจายตัวของพฤติกรรมการมีส่วนร่วมจำแนกตามผลลัพธ์การสำเร็จการศึกษา", fontsize=14, fontweight="bold", color=navy)
    fig.text(0.5, 0.01, "กล่องแสดงช่วงควอร์ไทล์ (IQR); ซ่อนค่าผิดปกติรุนแรงเพื่อความชัดเจนในการนำเสนอ", ha="center", fontsize=9, color="#66758A")
    plt.tight_layout(rect=[0, 0.04, 1, 0.94])
    fig2_path = os.path.join(FIG_DIR, "activity_distributions.png")
    fig.savefig(fig2_path, dpi=180)
    plt.close(fig)

    # รูปที่ 3: แผนผังความร้อนสหสัมพันธ์ (Correlation Heatmap)
    key_features = [
        "total_active_days",
        "total_events",
        "total_chapters",
        "total_video_plays",
        "total_forum_posts",
        "event_intensity",
        "video_play_ratio",
        "overall_span_days",
        "n_courses",
        "certified_student",
    ]
    corr_df = merged[key_features].corr()
    mask = np.triu(np.ones_like(corr_df, dtype=bool), k=1)
    fig, ax = plt.subplots(figsize=(11, 8.5), facecolor="white")
    sns.heatmap(
        corr_df,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap=sns.diverging_palette(250, 15, s=75, l=55, as_cmap=True),
        center=0,
        vmin=-1,
        vmax=1,
        cbar=True,
        square=True,
        ax=ax,
        linewidths=1,
        linecolor="white",
        cbar_kws={"label": "ค่าสัมประสิทธิ์สหสัมพันธ์เพียร์สัน (r)", "shrink": 0.8},
    )
    ax.set_title("ความสัมพันธ์ระหว่างฟีเจอร์พฤติกรรมและตัวแปรเป้าหมาย", fontsize=14, color=navy, pad=16, fontweight="bold")
    ax.tick_params(axis="x", rotation=55)
    ax.tick_params(axis="y", rotation=0)
    plt.tight_layout()
    fig3_path = os.path.join(FIG_DIR, "correlation_matrix.png")
    fig.savefig(fig3_path, dpi=180)
    plt.close(fig)

    # รูปที่ 4: ความสัมพันธ์ระหว่างประชากรศาสตร์และอัตราการสำเร็จการศึกษา
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6), facecolor="white")
    loe_order = ["Less than Secondary", "Secondary", "Bachelor's", "Master's", "Doctorate", "Unknown"]
    loe_order_th = ["ต่ำกว่ามัธยม", "มัธยมศึกษา", "ปริญญาตรี", "ปริญญาโท", "ปริญญาเอก", "ไม่ระบุ"]
    loe_rate = (
        merged.groupby("LoE_DI")[target_col]
        .mean()
        .reindex(loe_order)
        .fillna(0) * 100
    )
    education_colors = sns.color_palette("Blues", n_colors=len(loe_order) + 2)[2:]
    axes[0].barh(loe_order_th, loe_rate.values, color=education_colors, edgecolor="white")
    for i, v in enumerate(loe_rate.values):
        axes[0].text(v + 0.15, i, f"{v:.2f}%", va="center", fontweight="bold")
    axes[0].axvline(df_labels[target_col].mean() * 100, color=violet, linestyle="--", linewidth=1.8, label="อัตราเฉลี่ยรวม")
    axes[0].set_title("อัตราสำเร็จการศึกษาจำแนกตามระดับการศึกษา", fontsize=12, fontweight="bold", color=navy)
    axes[0].set_xlabel("อัตราการสำเร็จการศึกษา (%)", fontsize=11, fontweight="bold")
    axes[0].legend(frameon=False, loc="lower right")
    axes[0].set_xlim(0, max(loe_rate.max() * 1.18, 6.5))
    style_axis(axes[0], "x")

    # 8 ประเทศที่มีผู้เรียนมากที่สุด
    top_countries = merged["country"].value_counts().head(8).index
    country_rate = (
        merged[merged["country"].isin(top_countries)]
        .groupby("country")[target_col]
        .mean()
        .sort_values(ascending=True) * 100
    )
    country_colors = sns.color_palette("mako", n_colors=len(country_rate) + 2)[2:]
    axes[1].barh(country_rate.index, country_rate.values, color=country_colors, edgecolor="white")
    for i, v in enumerate(country_rate.values):
        axes[1].text(v + 0.15, i, f"{v:.2f}%", va="center", fontweight="bold")
    axes[1].axvline(df_labels[target_col].mean() * 100, color=violet, linestyle="--", linewidth=1.8, label="อัตราเฉลี่ยรวม")
    axes[1].set_title("อัตราสำเร็จการศึกษาในกลุ่มประเทศที่มีผู้เรียนสูงสุด", fontsize=12, fontweight="bold", color=navy)
    axes[1].set_xlabel("อัตราการสำเร็จการศึกษา (%)", fontsize=11, fontweight="bold")
    axes[1].legend(frameon=False, loc="lower right")
    axes[1].set_xlim(0, max(country_rate.max() * 1.18, 6.5))
    style_axis(axes[1], "x")
    fig.suptitle("บริบททางประชากรศาสตร์ (เชิงพรรณนาเท่านั้น ไม่ใช่ความสัมพันธ์เชิงสาเหตุ)", fontsize=14, fontweight="bold", color=navy)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig4_path = os.path.join(FIG_DIR, "demographics_completion.png")
    fig.savefig(fig4_path, dpi=180)
    plt.close(fig)

    print(f"[+] บันทึกภาพประกอบ EDA ทั้งหมดเรียบร้อยที่: {FIG_DIR}")


if __name__ == "__main__":
    run_eda()
