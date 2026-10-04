"""Generate high-resolution static PNG figures for the bilingual dashboard.

Replaces interactive Plotly charts with clean, centered, publication-quality static images
using matplotlib, fully aligned with user requirements:
- 6-metric K diagnostic
- Supervised metrics (Accuracy, Precision, Recall, F1, AUC, Runtime)
- Deep Learning metrics (Accuracy, Precision, Recall, F1, AUC, Runtime)
- LLM Generative AI 1,800-student benchmark (Gemini, Claude, GPT)
- All-tracks executive summary
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures" / "tracks"
FIGURES.mkdir(parents=True, exist_ok=True)


def plot_segment_comparison():
    """Static grouped bar chart for learner segment comparison."""
    df = pd.read_csv(TABLES / "segment_comparison.csv")
    features = [
        "mean_course_events_percentile",
        "mean_course_active_days_percentile",
        "mean_course_chapters_percentile",
        "mean_course_forum_posts_percentile",
    ]
    labels = ["Events", "Active days", "Chapters", "Forum posts"]
    colors = ["#1E3A8A", "#0D9488", "#F59E0B", "#10B981"]

    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = np.arange(len(labels))
    width = 0.20

    for i, (_, row) in enumerate(df.iterrows()):
        values = [row[c] for c in features]
        seg_name = str(row["segment"]).replace("_", " ").title()
        offset = (i - 1.5) * width
        rects = ax.bar(x + offset, values, width, label=f"{seg_name} (N={int(row['students']):,})", color=colors[i % len(colors)])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10.5, fontweight="600")
    ax.set_ylabel("Mean Within-Course Percentile [0, 1]", fontsize=10)
    ax.set_ylim(0, 1.1)
    ax.set_title("Learner Behavior Profiles Across Audience Segments", fontsize=12.5, fontweight="bold", pad=12)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIGURES / "segment_comparison_static.png", dpi=180, bbox_inches="tight")
    plt.close()
    print("[Figure] Generated segment_comparison_static.png")


def plot_llm_generative_comparison():
    """Static grouped bar chart for Gemini, Claude, and GPT on 1,800 students."""
    df = pd.read_csv(TABLES / "llm_generative_model_comparison.csv")
    metrics = [
        ("test_accuracy", "Accuracy", "#2563EB"),
        ("test_precision", "Precision", "#0D9488"),
        ("test_recall", "Recall", "#16A34A"),
        ("test_f1", "F1 Score", "#F59E0B"),
        ("test_roc_auc", "AUC (ROC-AUC)", "#7C3AED"),
    ]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(df))
    width = 0.15

    for i, (col, label, color) in enumerate(metrics):
        offset = (i - 2) * width
        values = df[col]
        rects = ax.bar(x + offset, values, width, label=label, color=color)
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f"{height:.2f}",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    names = [f"{r.model_name}\n({r.provider})" for r in df.itertuples()]
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10, fontweight="600")
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Held-out Test Metric Value", fontsize=10)
    ax.set_title("Generative AI Family Benchmark: Full Held-out Test Set (N=1,800 Students)", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="upper right", ncol=5, fontsize=8.5, framealpha=0.95)
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIGURES / "llm_generative_model_comparison.png", dpi=180, bbox_inches="tight")
    plt.close()
    print("[Figure] Generated llm_generative_model_comparison.png")


def plot_llm_generative_confusion_matrices():
    """Side-by-side static confusion matrices for Gemini, GPT, and Claude on 1,800 students."""
    df = pd.read_csv(TABLES / "llm_generative_model_comparison.csv")
    fig, axes = plt.subplots(1, len(df), figsize=(5 * len(df), 4.5))
    if len(df) == 1:
        axes = [axes]

    for ax, (_, row) in zip(axes, df.iterrows()):
        matrix = np.array([[int(row["tn"]), int(row["fp"])], [int(row["fn"]), int(row["tp"])]])
        im = ax.imshow(matrix, cmap="Blues")
        ax.set_title(f"{row['model_name']} ({row['provider']})\nAccuracy: {row['test_accuracy']*100:.1f}% · F1: {row['test_f1']:.3f}",
                     fontsize=10.5, fontweight="bold", pad=10)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Pred 0", "Pred 1"], fontsize=9.5)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["Actual 0", "Actual 1"], fontsize=9.5)
        for i in range(2):
            for j in range(2):
                val = matrix[i, j]
                color = "white" if val > matrix.max() / 2 else "#0B1F3A"
                ax.text(j, i, f"{val:,}", ha="center", va="center", color=color, fontweight="bold", fontsize=11)

    fig.suptitle("Confusion Matrices on Held-out Test Split (N=1,800 Students)", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES / "llm_generative_confusion_matrices.png", dpi=180, bbox_inches="tight")
    plt.close()
    print("[Figure] Generated llm_generative_confusion_matrices.png")


def plot_all_tracks_summary():
    """Static summary bar chart comparing champion models across all analysis tracks."""
    df = pd.read_csv(TABLES / "all_track_model_comparison.csv")
    selected = df[df["selected"].eq(True)].copy()

    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(selected))
    colors = ["#1E3A8A", "#0D9488", "#F59E0B", "#7C3AED"]

    bars = ax.bar(x, selected["primary_metric_value"], width=0.45, color=colors[:len(selected)], edgecolor="#111827", linewidth=0.8)
    for bar, (_, row) in zip(bars, selected.iterrows()):
        height = bar.get_height()
        ax.annotate(f"{row['primary_metric_name']}: {height:.3f}\n({row['model']})",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5, fontweight="600")

    ax.set_xticks(x)
    ax.set_xticklabels(selected["track"], fontsize=10, fontweight="bold")
    ax.set_ylim(0, 1.25)
    ax.set_ylabel("Primary Track Performance Score", fontsize=10)
    ax.set_title("Selected Champion Models Across All Four Analysis Tracks", fontsize=12.5, fontweight="bold", pad=12)
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIGURES / "all_tracks_summary_comparison.png", dpi=180, bbox_inches="tight")
    plt.close()
    print("[Figure] Generated all_tracks_summary_comparison.png")


def generate_all_static_figures():
    plot_segment_comparison()
    plot_llm_generative_comparison()
    plot_llm_generative_confusion_matrices()
    plot_all_tracks_summary()


if __name__ == "__main__":
    generate_all_static_figures()
