"""Plot EXP-001 monthly summaries.

Reads monthly_summary.csv and writes a few basic figures to results/figures.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--monthly-csv",
        type=Path,
        default=Path("results") / "monthly_summary.csv",
        help="Path to monthly_summary.csv",
    )
    ap.add_argument(
        "--figdir",
        type=Path,
        default=Path("results") / "figures",
        help="Output directory for figures",
    )
    args = ap.parse_args()

    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except Exception as e:
        raise RuntimeError("matplotlib+seaborn required for plotting") from e

    df = pd.read_csv(args.monthly_csv)
    df["month"] = pd.to_datetime(df["start_year"].astype(str) + "-" + df["start_month"].astype(str).str.zfill(2) + "-01")

    args.figdir.mkdir(parents=True, exist_ok=True)

    sns.set_style("whitegrid")

    # Runtime median over time
    plt.figure(figsize=(12, 5))
    sns.lineplot(data=df, x="month", y="runtime_median_sec", hue="source_token")
    plt.title("FRESCO baseline: median runtime by start month")
    plt.xlabel("Start month")
    plt.ylabel("Median runtime (seconds)")
    plt.tight_layout()
    plt.savefig(args.figdir / "runtime_median_by_month.png", dpi=200)
    plt.close()

    # Peak memused p90 over time
    plt.figure(figsize=(12, 5))
    sns.lineplot(data=df, x="month", y="peak_memused_p90", hue="source_token")
    plt.title("FRESCO baseline: peak memused p90 by start month")
    plt.xlabel("Start month")
    plt.ylabel("Peak memused p90")
    plt.tight_layout()
    plt.savefig(args.figdir / "peak_memused_p90_by_month.png", dpi=200)
    plt.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
