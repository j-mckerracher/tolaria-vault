#!/usr/bin/env python3
"""Local analysis for EXP-008.

Creates:
- summary tables (CSV)
- figures (PNG)

Input: results/exp008_results.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent.parent
RESULTS = HERE / "results" / "exp008_results.csv"
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
    # df: filtered to one variant
    order = [
        ("single", "S", False),
        ("single", "C", False),
        ("single", "NONE", False),
        ("pooled_all_no_cluster", "S+C+NONE", False),
        ("pooled_all_with_cluster", "S+C+NONE", True),
    ]

    test_clusters = ["S", "C", "NONE"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
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

    axes[0].set_ylabel("R² (log-runtime)")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def _plot_shift_scatter(df: pd.DataFrame, title: str, out_png: Path) -> None:
    # Transfer-only, single-cluster training, with timelimit.
    d = df[(df["variant"] == "with_timelimit") & (df["train_spec"] == "single") & (df["train_clusters"].isin(["S", "C", "NONE"]))].copy()
    d["is_transfer"] = d["train_clusters"] != d["test_cluster"]
    d = d[d["is_transfer"]].copy()

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


def main() -> None:
    if not RESULTS.exists():
        raise SystemExit(f"Missing: {RESULTS}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RESULTS)

    # Save a compact pivot for paper tables.
    paper = df[df["variant"] == "with_timelimit"].copy()
    paper["train_label"] = paper.apply(_spec_label, axis=1)
    paper["r2_ci"] = paper.apply(lambda r: f"{r['r2']:.3f} [{r['r2_ci_low']:.3f},{r['r2_ci_high']:.3f}]", axis=1)

    pivot = paper.pivot_table(index="train_label", columns="test_cluster", values="r2_ci", aggfunc="first")
    pivot.to_csv(OUT_DIR / "exp008_r2_ci_table.csv")

    # Conte anomaly explicit table.
    conte = paper[(paper["test_cluster"] == "C") & (paper["train_spec"] == "single")].copy()
    conte = conte[["train_clusters", "r2", "r2_ci_low", "r2_ci_high", "smape", "shift_smd_mean", "shift_jsd_mean"]].sort_values("r2", ascending=False)
    conte.to_csv(OUT_DIR / "exp008_conte_test_detail.csv", index=False)

    _plot_r2_bars(
        df[df["variant"] == "with_timelimit"].copy(),
        "EXP-008 R² with timelimit (95% bootstrap CI)",
        OUT_DIR / "exp008_r2_with_timelimit.png",
    )
    _plot_r2_bars(
        df[df["variant"] == "no_timelimit"].copy(),
        "EXP-008 R² without timelimit (95% bootstrap CI)",
        OUT_DIR / "exp008_r2_no_timelimit.png",
    )
    _plot_shift_scatter(df, "EXP-008 transfer: shift vs R² (with timelimit)", OUT_DIR / "exp008_shift_vs_r2.png")

    print("[done] Wrote tables/figures to:", OUT_DIR)


if __name__ == "__main__":
    main()
