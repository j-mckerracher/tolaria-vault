#!/usr/bin/env python3
"""Local analysis for EXP-010.

Generates a calibration curve (R² vs k) for each condition.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


HERE = Path(__file__).resolve().parent.parent
RESULTS = HERE / "results" / "exp010_results.csv"
OUT_DIR = HERE / "results"


def main() -> None:
    if not RESULTS.exists():
        raise SystemExit(f"Missing: {RESULTS}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RESULTS)

    fig, ax = plt.subplots(figsize=(6, 4))
    for cond, d in df.groupby("condition"):
        d = d.sort_values("k")
        ax.plot(d["k"], d["r2"], marker="o", label=cond)
        ax.fill_between(d["k"], d["r2_ci_low"], d["r2_ci_high"], alpha=0.2)

    ax.set_xscale("symlog", linthresh=100)
    ax.set_xlabel("k target labels added")
    ax.set_ylabel("R² (log-runtime)")
    ax.set_title("EXP-010 few-shot calibration curves (Conte target)")
    ax.grid(alpha=0.25)
    ax.legend()

    out = OUT_DIR / "exp010_calibration_curves.png"
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)

    print("[done] Wrote:", out)


if __name__ == "__main__":
    main()
