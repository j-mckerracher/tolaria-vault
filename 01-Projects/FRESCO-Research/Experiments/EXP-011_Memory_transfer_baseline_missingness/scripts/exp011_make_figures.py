#!/usr/bin/env python3
"""Local analysis for EXP-011.

Creates:
- summary tables (CSV)
- figures (PNG)

Input: results/exp011_results.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent.parent
RESULTS = HERE / "results" / "exp011_results.csv"
OUT_DIR = HERE / "results"


def _spec_label(row: pd.Series) -> str:
    if row["train_spec"] == "single":
        return f"train={row['train_clusters']}"
    if row["train_spec"] == "pooled_all_no_cluster":
        return "pooled(all)"
    if row["train_spec"] == "pooled_all_with_cluster":
        return "pooled(all)+clusterID"
    return f"{row['train_spec']}:{row['train_clusters']}"


def _plot_r2_bars(df: pd.DataFrame, title: str, out_png: Path) -> None:
    # df: all data for memory prediction
    order = [
        ("single", "S", False),
        ("single", "C", False),
        ("single", "NONE", False),
        ("pooled_all_no_cluster", "S+C+NONE", False),
        ("pooled_all_with_cluster", "S+C+NONE", True),
    ]

    test_clusters = sorted(df["test_cluster"].unique())

    fig, axes = plt.subplots(1, len(test_clusters), figsize=(5 * len(test_clusters), 4), sharey=True)
    if len(test_clusters) == 1:
        axes = [axes]

    for ax, tc in zip(axes, test_clusters):
        d = df[df["test_cluster"] == tc].copy()

        xs = []
        ys = []
        yerr = []
        labels = []

        for (train_spec, train_clusters, cc) in order:
            r = d[(d["train_spec"] == train_spec) & (d["train_clusters"] == train_clusters) & (d["cluster_conditioning"] == cc)]
            if len(r) != 1:
                continue
            r = r.iloc[0]
            xs.append(len(xs))
            ys.append(r["r2"])
            yerr.append([r["r2"] - r["r2_ci_low"], r["r2_ci_high"] - r["r2"]])
            labels.append(_spec_label(r))

        yerr = np.array(yerr).T if yerr else None
        ax.bar(xs, ys, yerr=yerr, capsize=3)
        ax.set_title(f"Test={tc}")
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.axhline(0.0, color="black", linewidth=0.8)
        ax.grid(axis="y", alpha=0.25)

    axes[0].set_ylabel("R² (log-peak-memory)")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def _plot_shift_scatter(df: pd.DataFrame, title: str, out_png: Path) -> None:
    # Transfer-only, single-cluster training
    d = df[(df["train_spec"] == "single") & (df["train_clusters"].isin(["S", "C", "NONE"]))].copy()
    d["is_transfer"] = d["train_clusters"] != d["test_cluster"]
    d = d[d["is_transfer"]].copy()

    if len(d) == 0:
        print("[warn] No transfer data for shift scatter plot")
        return

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(d["shift_smd_mean"], d["r2"], alpha=0.7)

    for _, r in d.iterrows():
        ax.annotate(f"{r['train_clusters']}→{r['test_cluster']}", (r["shift_smd_mean"], r["r2"]), fontsize=8, xytext=(4, 2), textcoords="offset points")

    ax.set_xlabel("Shift (mean SMD; feature space)")
    ax.set_ylabel("R²")
    ax.set_title(title)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def _plot_missingness_bars(df: pd.DataFrame, out_png: Path) -> None:
    # Show test_mem_coverage for each test cluster
    d = df[df["train_spec"] == "single"].copy()
    d = d[d["train_clusters"] == d["test_cluster"]].copy()  # Within-site only
    
    if len(d) == 0:
        print("[warn] No data for missingness bar plot")
        return

    clusters = sorted(d["test_cluster"].unique())
    coverages = [d[d["test_cluster"] == c]["test_mem_coverage"].iloc[0] * 100 for c in clusters]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(range(len(clusters)), coverages)
    ax.set_xticks(range(len(clusters)))
    ax.set_xticklabels(clusters)
    ax.set_ylabel("Memory Coverage (%)")
    ax.set_xlabel("Cluster")
    ax.set_title("EXP-011: Memory metric coverage (test set)")
    ax.axhline(100, color="gray", linestyle="--", alpha=0.5)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def main() -> None:
    if not RESULTS.exists():
        raise SystemExit(f"Missing: {RESULTS}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RESULTS)

    # Save a compact pivot for paper tables.
    paper = df.copy()
    paper["train_label"] = paper.apply(_spec_label, axis=1)
    paper["r2_ci"] = paper.apply(lambda r: f"{r['r2']:.3f} [{r['r2_ci_low']:.3f},{r['r2_ci_high']:.3f}]", axis=1)

    pivot = paper.pivot_table(index="train_label", columns="test_cluster", values="r2_ci", aggfunc="first")
    pivot.to_csv(OUT_DIR / "exp011_r2_ci_table.csv")

    # Missingness summary table
    missingness = df[["test_cluster", "test_mem_coverage", "n_test"]].drop_duplicates().sort_values("test_cluster")
    missingness["test_mem_coverage_pct"] = missingness["test_mem_coverage"] * 100
    missingness.to_csv(OUT_DIR / "exp011_missingness_summary.csv", index=False)

    # Transfer detail table (single-cluster training only)
    transfer = df[(df["train_spec"] == "single") & (df["train_clusters"] != df["test_cluster"])].copy()
    if len(transfer) > 0:
        transfer = transfer[["train_clusters", "test_cluster", "r2", "r2_ci_low", "r2_ci_high", "smape", "shift_smd_mean", "shift_jsd_mean"]].sort_values("r2", ascending=False)
        transfer.to_csv(OUT_DIR / "exp011_transfer_detail.csv", index=False)

    # Figures
    _plot_r2_bars(df, "EXP-011 Memory Prediction R² (95% bootstrap CI)", OUT_DIR / "exp011_r2_bars.png")
    _plot_shift_scatter(df, "EXP-011 transfer: shift vs R²", OUT_DIR / "exp011_shift_vs_r2.png")
    _plot_missingness_bars(df, OUT_DIR / "exp011_missingness_bars.png")

    print("[done] Wrote tables/figures to:", OUT_DIR)


if __name__ == "__main__":
    main()
