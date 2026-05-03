#!/usr/bin/env python3
"""
EXP-002: Isolation Forest Anomaly Detection on FRESCO Job Rollups

Trains per-cluster Isolation Forest models to detect anomalous jobs.
Evaluates correlation between anomaly scores and job failures.

Usage:
    python exp002_isolation_forest.py train --input-dir <job_rollup_dir> --out-dir <output>
    python exp002_isolation_forest.py analyze --out-dir <output>
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Lazy imports for heavy dependencies
def _require_sklearn():
    try:
        import sklearn
    except ImportError:
        sys.exit("scikit-learn not installed. Run: pip install scikit-learn")

def _require_duckdb():
    try:
        import duckdb
    except ImportError:
        sys.exit("duckdb not installed. Run: pip install duckdb")


# Feature configuration
NUMERIC_FEATURES = [
    "runtime_sec",
    "wait_sec",
    "ncores",
    "nhosts",
    "timelimit",
    "cpuuser_mean_of_mean",
    "memused_mean",
    "memused_max",
]

# Features to log-transform (highly skewed)
LOG_FEATURES = ["runtime_sec", "wait_sec", "memused_mean", "memused_max", "timelimit"]

# Columns needed from job_rollup
REQUIRED_COLS = [
    "jid",
    "source_token",
    "start_year",
    "start_month",
    "exitcode",
    "runtime_sec",
    "wait_sec",
    "ncores",
    "nhosts",
    "timelimit",
    "value_cpuuser_mean",
    "value_memused_mean",
    "value_memused_max",
]


def load_job_rollup(input_dir: Path, threads: int = 8) -> pd.DataFrame:
    """Load job rollup from EXP-001 using DuckDB for speed."""
    _require_duckdb()
    import duckdb

    glob_pattern = str((input_dir / "**" / "*.parquet").as_posix())
    
    con = duckdb.connect(":memory:")
    con.execute(f"PRAGMA threads={threads}")
    
    # Select and rename columns for clarity
    sql = f"""
    SELECT
        jid,
        source_token,
        start_year,
        start_month,
        exitcode,
        runtime_sec,
        wait_sec,
        ncores,
        nhosts,
        timelimit,
        value_cpuuser_mean AS cpuuser_mean_of_mean,
        value_memused_mean AS memused_mean,
        value_memused_max AS memused_max
    FROM read_parquet('{glob_pattern}', hive_partitioning=1, union_by_name=true)
    WHERE runtime_sec IS NOT NULL AND runtime_sec > 0
    """
    
    print(f"[load] Loading job rollup from {input_dir}...")
    df = con.execute(sql).fetchdf()
    con.close()
    
    print(f"[load] Loaded {len(df):,} jobs with valid runtime")
    return df


def preprocess_features(df: pd.DataFrame, cluster: str) -> tuple[np.ndarray, list[str]]:
    """
    Preprocess features for a single cluster:
    1. Select numeric features
    2. Log-transform skewed features
    3. Impute missing with median
    4. Standardize (Z-score)
    
    Returns feature matrix and feature names.
    """
    from sklearn.preprocessing import StandardScaler
    
    features = []
    feature_names = []
    
    for col in NUMERIC_FEATURES:
        if col not in df.columns:
            print(f"[preprocess] Warning: {col} not in data, skipping")
            continue
            
        vals = df[col].values.astype(np.float64)
        
        # Log-transform if specified (add 1 to handle zeros)
        if col in LOG_FEATURES:
            vals = np.log1p(np.maximum(vals, 0))
            feature_names.append(f"log_{col}")
        else:
            feature_names.append(col)
        
        features.append(vals)
    
    X = np.column_stack(features)
    
    # Impute missing with column median
    for i in range(X.shape[1]):
        mask = ~np.isfinite(X[:, i])
        if mask.any():
            median = np.nanmedian(X[:, i])
            X[mask, i] = median if np.isfinite(median) else 0.0
    
    # Standardize
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    print(f"[preprocess] {cluster}: {X.shape[0]:,} jobs, {X.shape[1]} features")
    return X, feature_names


def train_isolation_forest(
    X: np.ndarray,
    n_estimators: int = 100,
    max_samples: int = 10000,
    contamination: float = 0.01,
    random_state: int = 42,
):
    """Train Isolation Forest and return model + anomaly scores."""
    _require_sklearn()
    from sklearn.ensemble import IsolationForest
    
    model = IsolationForest(
        n_estimators=n_estimators,
        max_samples=min(max_samples, len(X)),
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    
    model.fit(X)
    
    # Get anomaly scores (lower = more anomalous in sklearn convention)
    # Convert to positive scores where higher = more anomalous
    scores = -model.decision_function(X)
    predictions = model.predict(X)  # -1 = anomaly, 1 = normal
    
    return model, scores, predictions


def compute_failure_correlation(df: pd.DataFrame) -> dict:
    """Compute correlation between anomaly scores and job failures."""
    from scipy import stats
    
    # Binary failure indicator
    # Exitcode contains strings: COMPLETED = success, everything else = failure
    df = df.copy()
    exitcode_str = df["exitcode"].astype(str).str.upper().str.strip()
    df["failed"] = ~exitcode_str.isin(["COMPLETED", "0", "NONE", "NAN", ""])
    
    # Spearman correlation
    valid = df["anomaly_score"].notna() & df["failed"].notna()
    if valid.sum() < 10:
        return {"spearman_rho": np.nan, "spearman_p": np.nan}
    
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
    
    return results


def train_command(args):
    """Train Isolation Forest models per cluster."""
    _require_sklearn()
    
    input_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "models").mkdir(exist_ok=True)
    (out_dir / "figures").mkdir(exist_ok=True)
    
    # Load data
    df = load_job_rollup(input_dir, threads=args.threads)
    
    # Get unique clusters
    clusters = df["source_token"].unique()
    print(f"[train] Found clusters: {clusters}")
    
    all_results = []
    cluster_stats = []
    
    for cluster in clusters:
        print(f"\n[train] Processing cluster: {cluster}")
        cluster_df = df[df["source_token"] == cluster].copy()
        
        if len(cluster_df) < 100:
            print(f"[train] Skipping {cluster}: only {len(cluster_df)} jobs")
            continue
        
        # Preprocess
        X, feature_names = preprocess_features(cluster_df, cluster)
        
        # Train
        print(f"[train] Training Isolation Forest for {cluster}...")
        model, scores, predictions = train_isolation_forest(
            X,
            n_estimators=args.n_estimators,
            max_samples=args.max_samples,
            contamination=args.contamination,
            random_state=args.seed,
        )
        
        # Add scores to dataframe
        cluster_df["anomaly_score"] = scores
        cluster_df["is_anomaly"] = predictions == -1
        
        # Compute metrics
        metrics = compute_failure_correlation(cluster_df)
        metrics["cluster"] = cluster
        metrics["n_jobs"] = len(cluster_df)
        metrics["n_anomalies"] = (predictions == -1).sum()
        metrics["anomaly_rate"] = metrics["n_anomalies"] / len(cluster_df)
        cluster_stats.append(metrics)
        
        print(f"[train] {cluster}: {metrics['n_anomalies']:,} anomalies ({metrics['anomaly_rate']:.2%})")
        print(f"[train] {cluster}: Spearman ρ = {metrics['spearman_rho']:.3f}, p = {metrics['spearman_p']:.2e}")
        print(f"[train] {cluster}: Precision@1% = {metrics.get('precision_at_1pct', np.nan):.3f}")
        
        # Save model
        model_path = out_dir / "models" / f"iforest_{cluster}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump({"model": model, "feature_names": feature_names}, f)
        print(f"[train] Saved model to {model_path}")
        
        # Collect results
        all_results.append(cluster_df[["jid", "source_token", "start_year", "start_month", 
                                        "exitcode", "anomaly_score", "is_anomaly"]])
    
    # Combine and save results
    if all_results:
        results_df = pd.concat(all_results, ignore_index=True)
        results_path = out_dir / "anomaly_scores.parquet"
        results_df.to_parquet(results_path, index=False)
        print(f"\n[train] Saved {len(results_df):,} anomaly scores to {results_path}")
    
    # Save cluster stats
    stats_df = pd.DataFrame(cluster_stats)
    stats_path = out_dir / "cluster_metrics.csv"
    stats_df.to_csv(stats_path, index=False)
    print(f"[train] Saved cluster metrics to {stats_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(stats_df.to_string(index=False))


def analyze_command(args):
    """Generate analysis figures from trained models."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    out_dir = Path(args.out_dir)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(exist_ok=True)
    
    # Load anomaly scores
    scores_path = out_dir / "anomaly_scores.parquet"
    if not scores_path.exists():
        sys.exit(f"Anomaly scores not found: {scores_path}. Run 'train' first.")
    
    df = pd.read_parquet(scores_path)
    print(f"[analyze] Loaded {len(df):,} anomaly scores")
    
    # 1. Score distribution per cluster
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    clusters = df["source_token"].unique()
    
    for i, cluster in enumerate(clusters[:3]):
        ax = axes[i] if len(clusters) > 1 else axes
        cluster_scores = df[df["source_token"] == cluster]["anomaly_score"]
        ax.hist(cluster_scores, bins=100, alpha=0.7, edgecolor="black")
        ax.set_xlabel("Anomaly Score")
        ax.set_ylabel("Count")
        ax.set_title(f"{cluster} (n={len(cluster_scores):,})")
        ax.axvline(cluster_scores.quantile(0.99), color="red", linestyle="--", label="99th pct")
        ax.legend()
    
    plt.tight_layout()
    plt.savefig(fig_dir / "score_distributions.png", dpi=150)
    plt.close()
    print(f"[analyze] Saved score_distributions.png")
    
    # 2. Anomaly rate by month
    monthly = df.groupby(["source_token", "start_year", "start_month"]).agg(
        n_jobs=("jid", "count"),
        n_anomalies=("is_anomaly", "sum"),
    ).reset_index()
    monthly["anomaly_rate"] = monthly["n_anomalies"] / monthly["n_jobs"]
    monthly["date"] = pd.to_datetime(
        monthly["start_year"].astype(str) + "-" + monthly["start_month"].astype(str).str.zfill(2) + "-01"
    )
    
    fig, ax = plt.subplots(figsize=(12, 5))
    for cluster in clusters:
        cluster_data = monthly[monthly["source_token"] == cluster].sort_values("date")
        ax.plot(cluster_data["date"], cluster_data["anomaly_rate"] * 100, 
                marker="o", markersize=3, label=cluster)
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Anomaly Rate (%)")
    ax.set_title("Monthly Anomaly Rate by Cluster")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(fig_dir / "anomaly_rate_by_month.png", dpi=150)
    plt.close()
    print(f"[analyze] Saved anomaly_rate_by_month.png")
    
    # 3. Top anomalies inspection
    top_anomalies = df.nlargest(100, "anomaly_score")
    top_path = out_dir / "top_100_anomalies.csv"
    top_anomalies.to_csv(top_path, index=False)
    print(f"[analyze] Saved top 100 anomalies to {top_path}")
    
    # Save monthly summary
    monthly.to_csv(out_dir / "monthly_anomaly_summary.csv", index=False)
    print(f"[analyze] Saved monthly_anomaly_summary.csv")
    
    print("\n[analyze] Analysis complete!")


def main():
    parser = argparse.ArgumentParser(description="EXP-002: Isolation Forest Anomaly Detection")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train Isolation Forest models")
    train_parser.add_argument("--input-dir", required=True, help="Path to EXP-001 job_rollup directory")
    train_parser.add_argument("--out-dir", required=True, help="Output directory for results")
    train_parser.add_argument("--threads", type=int, default=8, help="DuckDB threads")
    train_parser.add_argument("--n-estimators", type=int, default=100, help="Number of trees")
    train_parser.add_argument("--max-samples", type=int, default=10000, help="Samples per tree")
    train_parser.add_argument("--contamination", type=float, default=0.01, help="Expected anomaly fraction")
    train_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    train_parser.set_defaults(func=train_command)
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Generate analysis figures")
    analyze_parser.add_argument("--out-dir", required=True, help="Output directory with trained results")
    analyze_parser.set_defaults(func=analyze_command)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
