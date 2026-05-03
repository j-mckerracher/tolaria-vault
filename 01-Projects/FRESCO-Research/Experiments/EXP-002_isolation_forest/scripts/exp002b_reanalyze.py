#!/usr/bin/env python3
"""
EXP-002b: Re-run failure correlation analysis with corrected exitcode parsing.

Uses existing anomaly_scores.parquet from EXP-002 - no re-training needed.

Usage:
    python exp002b_reanalyze.py --results-dir <path_to_exp002_results>
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def compute_failure_correlation(df: pd.DataFrame) -> dict:
    """Compute correlation between anomaly scores and job failures."""
    
    # Binary failure indicator
    # Exitcode contains strings: COMPLETED = success, everything else = failure
    df = df.copy()
    exitcode_str = df["exitcode"].astype(str).str.upper().str.strip()
    df["failed"] = ~exitcode_str.isin(["COMPLETED", "0", "NONE", "NAN", ""])
    
    # Spearman correlation
    valid = df["anomaly_score"].notna() & df["failed"].notna()
    if valid.sum() < 10:
        return {"spearman_rho": np.nan, "spearman_p": np.nan}, df
    
    rho, p = stats.spearmanr(
        df.loc[valid, "anomaly_score"],
        df.loc[valid, "failed"].astype(float)
    )
    
    # Precision at K
    n_jobs = len(df)
    results = {"spearman_rho": rho, "spearman_p": p}
    
    for pct in [0.01, 0.05, 0.10]:
        k = max(1, int(n_jobs * pct))
        top_k = df.nlargest(k, "anomaly_score")
        precision = top_k["failed"].mean() if len(top_k) > 0 else np.nan
        results[f"precision_at_{int(pct*100)}pct"] = precision
    
    # Baseline failure rate
    results["baseline_failure_rate"] = df["failed"].mean()
    
    # Lift (precision@1% / baseline)
    if results["baseline_failure_rate"] > 0:
        results["lift_at_1pct"] = results["precision_at_1pct"] / results["baseline_failure_rate"]
    else:
        results["lift_at_1pct"] = np.nan
    
    return results, df


def main():
    parser = argparse.ArgumentParser(description="EXP-002b: Re-analyze with corrected exitcode")
    parser.add_argument("--results-dir", required=True, help="Path to EXP-002 results directory")
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    scores_path = results_dir / "anomaly_scores.parquet"
    
    if not scores_path.exists():
        print(f"ERROR: {scores_path} not found")
        return 1
    
    # Load anomaly scores
    print(f"[load] Loading {scores_path}...")
    df = pd.read_parquet(scores_path)
    print(f"[load] Loaded {len(df):,} jobs")
    
    # Check exitcode distribution
    print("\n[info] Exitcode value distribution:")
    exitcode_counts = df["exitcode"].astype(str).str.upper().value_counts().head(10)
    print(exitcode_counts)
    
    # Compute per-cluster metrics
    clusters = df["source_token"].unique()
    all_stats = []
    
    print("\n" + "=" * 70)
    print("CORRECTED ANOMALY-FAILURE CORRELATION")
    print("=" * 70)
    
    for cluster in clusters:
        cluster_df = df[df["source_token"] == cluster].copy()
        metrics, cluster_df = compute_failure_correlation(cluster_df)
        metrics["cluster"] = cluster
        metrics["n_jobs"] = len(cluster_df)
        metrics["n_anomalies"] = cluster_df["is_anomaly"].sum()
        metrics["n_failures"] = cluster_df["failed"].sum()
        all_stats.append(metrics)
        
        print(f"\n{cluster}:")
        print(f"  Jobs: {metrics['n_jobs']:,}")
        print(f"  Failures: {metrics['n_failures']:,} ({metrics['baseline_failure_rate']:.2%})")
        print(f"  Anomalies: {metrics['n_anomalies']:,}")
        print(f"  Spearman ρ: {metrics['spearman_rho']:.4f} (p={metrics['spearman_p']:.2e})")
        print(f"  Precision@1%: {metrics['precision_at_1pct']:.3f}")
        print(f"  Precision@5%: {metrics['precision_at_5pct']:.3f}")
        print(f"  Lift@1%: {metrics['lift_at_1pct']:.2f}x")
    
    # Save updated metrics
    stats_df = pd.DataFrame(all_stats)
    out_path = results_dir / "cluster_metrics_corrected.csv"
    stats_df.to_csv(out_path, index=False)
    print(f"\n[save] Saved corrected metrics to {out_path}")
    
    # Analyze top anomalies by failure status
    print("\n" + "=" * 70)
    print("TOP ANOMALIES BY FAILURE STATUS")
    print("=" * 70)
    
    # Recompute failed column for full df
    exitcode_str = df["exitcode"].astype(str).str.upper().str.strip()
    df["failed"] = ~exitcode_str.isin(["COMPLETED", "0", "NONE", "NAN", ""])
    
    top_100 = df.nlargest(100, "anomaly_score")
    failure_breakdown = top_100["exitcode"].value_counts()
    print("\nTop 100 anomalies by exitcode:")
    print(failure_breakdown)
    
    n_failed = top_100["failed"].sum()
    print(f"\nOf top 100 anomalies: {n_failed} failed ({n_failed}%), {100-n_failed} completed")
    
    # Save updated top anomalies with failed column
    top_100.to_csv(results_dir / "top_100_anomalies_corrected.csv", index=False)
    print(f"[save] Saved top_100_anomalies_corrected.csv")
    
    print("\n[done] Analysis complete!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
