#!/usr/bin/env python3
"""
EXP-003b: Linear Regression with Fixed Source Token + Ablation Studies

Fixes:
- Source token extracted from filename (not jid) to correctly identify Conte
- Ablation: models with/without timelimit
- Baselines: median predictor, timelimit-only
- Better metrics: MdAE, MdAPE alongside MAE, MAPE

Usage:
    python exp003b_linear_regression.py train --input-dir <fresco_chunks> --out-dir <output>
"""

from __future__ import annotations

import argparse
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


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


# Feature sets for ablation
FEATURES_FULL = ["ncores", "nhosts", "log_timelimit", "log_wait_sec"]
FEATURES_NO_TIMELIMIT = ["ncores", "nhosts", "log_wait_sec"]
FEATURES_TIMELIMIT_ONLY = ["log_timelimit"]

TARGET = "log_runtime"


def load_fresco_data(input_dir: Path, threads: int = 8) -> pd.DataFrame:
    """Load FRESCO data with source_token extracted from filename."""
    _require_duckdb()
    import duckdb

    glob_pattern = str((input_dir / "**" / "*.parquet").as_posix())
    
    con = duckdb.connect(":memory:")
    con.execute(f"PRAGMA threads={threads}")
    
    # Extract source token from filename using regex
    # Filename pattern: HH.parquet or HH_X.parquet where X is S or C
    sql = f"""
    WITH raw_data AS (
        SELECT
            *,
            filename
        FROM read_parquet('{glob_pattern}', filename=true, union_by_name=true)
        WHERE start_time IS NOT NULL AND end_time IS NOT NULL
    ),
    with_token AS (
        SELECT
            *,
            -- Extract source token from filename
            CASE 
                WHEN filename LIKE '%/_S.parquet' OR filename LIKE '%\\_S.parquet' THEN 'S'
                WHEN filename LIKE '%/_C.parquet' OR filename LIKE '%\\_C.parquet' THEN 'C'
                WHEN regexp_matches(filename, '.*[/\\\\]\\d{{2}}_S\\.parquet$') THEN 'S'
                WHEN regexp_matches(filename, '.*[/\\\\]\\d{{2}}_C\\.parquet$') THEN 'C'
                ELSE 'NONE'
            END AS source_token
        FROM raw_data
    ),
    job_stats AS (
        SELECT
            jid,
            source_token,
            MIN(start_time) AS start_time,
            MIN(end_time) AS end_time,
            MIN(submit_time) AS submit_time,
            MAX(ncores) AS ncores,
            MAX(nhosts) AS nhosts,
            MAX(timelimit) AS timelimit
        FROM with_token
        GROUP BY jid, source_token
    )
    SELECT
        jid,
        source_token,
        EXTRACT(YEAR FROM start_time)::INT AS start_year,
        EXTRACT(MONTH FROM start_time)::INT AS start_month,
        EXTRACT(EPOCH FROM (end_time - start_time)) AS runtime_sec,
        EXTRACT(EPOCH FROM (start_time - submit_time)) AS wait_sec,
        ncores,
        nhosts,
        timelimit
    FROM job_stats
    WHERE EXTRACT(EPOCH FROM (end_time - start_time)) > 0
      AND EXTRACT(EPOCH FROM (end_time - start_time)) < 31536000
    """
    
    print(f"[load] Loading FRESCO data from {input_dir}...")
    print(f"[load] Extracting source_token from filename...")
    df = con.execute(sql).fetchdf()
    con.close()
    
    # Verify we got all clusters
    clusters = df["source_token"].value_counts()
    print(f"[load] Loaded {len(df):,} jobs")
    print(f"[load] Clusters found:")
    for cluster, count in clusters.items():
        print(f"       {cluster}: {count:,} jobs")
    
    return df


def prepare_features(df: pd.DataFrame, include_month: bool = True) -> tuple[pd.DataFrame, list[str]]:
    """Prepare feature matrix with preprocessing."""
    
    df = df.copy()
    
    # Log-transform target
    df["log_runtime"] = np.log1p(df["runtime_sec"])
    
    # Log-transform skewed numeric features
    df["log_timelimit"] = np.log1p(df["timelimit"].clip(lower=0))
    df["log_wait_sec"] = np.log1p(df["wait_sec"].clip(lower=0))
    
    # Month dummies (optional)
    month_cols = []
    if include_month:
        month_dummies = pd.get_dummies(df["start_month"], prefix="month", dtype=float)
        df = pd.concat([df, month_dummies], axis=1)
        month_cols = list(month_dummies.columns)
    
    # Handle missing values
    for col in FEATURES_FULL + month_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    return df, month_cols


def time_split(df: pd.DataFrame, train_frac: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by time (year, month) to avoid temporal leakage."""
    
    df = df.copy()
    df["time_idx"] = df["start_year"] * 100 + df["start_month"]
    
    sorted_times = df["time_idx"].sort_values().unique()
    n_train = int(len(sorted_times) * train_frac)
    cutoff = sorted_times[n_train]
    
    train = df[df["time_idx"] < cutoff].copy()
    test = df[df["time_idx"] >= cutoff].copy()
    
    print(f"[split] Train: {len(train):,} jobs, Test: {len(test):,} jobs")
    print(f"[split] Cutoff time_idx: {cutoff}")
    
    return train, test


def train_model(X_train: np.ndarray, y_train: np.ndarray, alpha: float = 1.0):
    """Train Ridge Regression model."""
    _require_sklearn()
    from sklearn.linear_model import Ridge
    
    model = Ridge(alpha=alpha, random_state=42)
    model.fit(X_train, y_train)
    
    return model


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray, 
                   y_true_original: np.ndarray) -> dict:
    """Compute evaluation metrics including median-based metrics."""
    _require_sklearn()
    from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
    
    # Metrics on log scale
    r2 = r2_score(y_true, y_pred)
    mae_log = mean_absolute_error(y_true, y_pred)
    mdae_log = np.median(np.abs(y_true - y_pred))  # Median absolute error
    rmse_log = np.sqrt(mean_squared_error(y_true, y_pred))
    
    # Metrics on original scale
    y_pred_original = np.expm1(y_pred)
    y_pred_original = np.clip(y_pred_original, 0, None)
    
    mae_sec = mean_absolute_error(y_true_original, y_pred_original)
    mdae_sec = np.median(np.abs(y_true_original - y_pred_original))
    
    # Percentage errors (avoiding division by zero)
    mask = y_true_original > 60  # Only jobs > 1 minute for MAPE
    if mask.sum() > 0:
        pct_errors = np.abs(y_true_original[mask] - y_pred_original[mask]) / y_true_original[mask] * 100
        mape = np.mean(pct_errors)
        mdape = np.median(pct_errors)
    else:
        mape = np.nan
        mdape = np.nan
    
    return {
        "r2": r2,
        "mae_log": mae_log,
        "mdae_log": mdae_log,
        "rmse_log": rmse_log,
        "mae_sec": mae_sec,
        "mdae_sec": mdae_sec,
        "mape": mape,
        "mdape": mdape,
    }


def train_and_evaluate_variant(train_df: pd.DataFrame, test_df: pd.DataFrame,
                                feature_cols: list[str], variant_name: str,
                                alpha: float = 1.0) -> tuple[dict, pd.DataFrame, object]:
    """Train and evaluate a single model variant."""
    
    # Filter to available features
    available_features = [c for c in feature_cols if c in train_df.columns]
    
    if len(available_features) == 0:
        print(f"[{variant_name}] No features available, skipping")
        return None, None, None
    
    X_train = train_df[available_features].values
    y_train = train_df["log_runtime"].values
    X_test = test_df[available_features].values
    y_test = test_df["log_runtime"].values
    y_test_original = test_df["runtime_sec"].values
    
    # Train
    model = train_model(X_train, y_train, alpha=alpha)
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Evaluate
    metrics = evaluate_model(y_test, y_pred, y_test_original)
    metrics["variant"] = variant_name
    metrics["n_features"] = len(available_features)
    metrics["features"] = ", ".join(available_features[:5]) + ("..." if len(available_features) > 5 else "")
    
    # Coefficients
    coef_df = pd.DataFrame({
        "feature": available_features,
        "coefficient": model.coef_,
        "abs_coefficient": np.abs(model.coef_),
    }).sort_values("abs_coefficient", ascending=False)
    coef_df["variant"] = variant_name
    coef_df["intercept"] = model.intercept_
    
    return metrics, coef_df, model


def evaluate_baseline(test_df: pd.DataFrame, baseline_type: str) -> dict:
    """Evaluate trivial baseline predictors."""
    
    y_test = test_df["log_runtime"].values
    y_test_original = test_df["runtime_sec"].values
    
    if baseline_type == "median":
        y_pred = np.full_like(y_test, np.median(y_test))
    elif baseline_type == "mean":
        y_pred = np.full_like(y_test, np.mean(y_test))
    else:
        raise ValueError(f"Unknown baseline: {baseline_type}")
    
    metrics = evaluate_model(y_test, y_pred, y_test_original)
    metrics["variant"] = f"baseline_{baseline_type}"
    metrics["n_features"] = 0
    metrics["features"] = "none"
    
    return metrics


def train_command(args):
    """Train linear regression models with ablation studies."""
    _require_sklearn()
    
    input_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "models").mkdir(exist_ok=True)
    (out_dir / "figures").mkdir(exist_ok=True)
    
    # Load data
    df = load_fresco_data(input_dir, threads=args.threads)
    
    # Prepare features
    df, month_cols = prepare_features(df, include_month=True)
    
    clusters = df["source_token"].unique()
    print(f"\n[train] Training models for clusters: {list(clusters)}")
    
    all_metrics = []
    all_coefficients = []
    
    for cluster in sorted(clusters):
        print(f"\n{'='*70}")
        print(f"CLUSTER: {cluster}")
        print("="*70)
        
        cluster_df = df[df["source_token"] == cluster].copy()
        
        if len(cluster_df) < 1000:
            print(f"[train] Skipping {cluster}: only {len(cluster_df)} jobs")
            continue
        
        # Time-based split
        train_df, test_df = time_split(cluster_df, train_frac=0.8)
        
        if len(test_df) < 100:
            print(f"[train] Skipping {cluster}: insufficient test data")
            continue
        
        # Define feature sets for ablation
        variants = {
            "full": FEATURES_FULL + month_cols,
            "no_timelimit": FEATURES_NO_TIMELIMIT + month_cols,
            "timelimit_only": FEATURES_TIMELIMIT_ONLY,
            "no_month": FEATURES_FULL,  # Full features without month dummies
        }
        
        # Train each variant
        for variant_name, feature_cols in variants.items():
            print(f"\n--- Variant: {variant_name} ---")
            
            metrics, coef_df, model = train_and_evaluate_variant(
                train_df, test_df, feature_cols, variant_name, alpha=args.alpha
            )
            
            if metrics is None:
                continue
            
            metrics["cluster"] = cluster
            metrics["n_train"] = len(train_df)
            metrics["n_test"] = len(test_df)
            all_metrics.append(metrics)
            
            if coef_df is not None:
                coef_df["cluster"] = cluster
                all_coefficients.append(coef_df)
            
            print(f"[eval] R² = {metrics['r2']:.4f}")
            print(f"[eval] MAE (log) = {metrics['mae_log']:.4f}, MdAE (log) = {metrics['mdae_log']:.4f}")
            print(f"[eval] MAPE = {metrics['mape']:.1f}%, MdAPE = {metrics['mdape']:.1f}%")
            
            # Save model
            if model is not None:
                model_path = out_dir / "models" / f"ridge_{cluster}_{variant_name}.pkl"
                with open(model_path, "wb") as f:
                    pickle.dump({"model": model, "features": feature_cols}, f)
        
        # Evaluate baselines
        for baseline_type in ["median", "mean"]:
            metrics = evaluate_baseline(test_df, baseline_type)
            metrics["cluster"] = cluster
            metrics["n_train"] = len(train_df)
            metrics["n_test"] = len(test_df)
            all_metrics.append(metrics)
            print(f"\n--- Baseline: {baseline_type} ---")
            print(f"[eval] R² = {metrics['r2']:.4f}, MdAPE = {metrics['mdape']:.1f}%")
    
    # Save results
    if all_metrics:
        metrics_df = pd.DataFrame(all_metrics)
        metrics_df.to_csv(out_dir / "metrics_comparison.csv", index=False)
        print(f"\n[save] Saved metrics to {out_dir / 'metrics_comparison.csv'}")
        
        # Create ablation summary
        ablation_summary = create_ablation_summary(metrics_df)
        ablation_summary.to_csv(out_dir / "ablation_summary.csv", index=False)
        print(f"[save] Saved ablation summary to {out_dir / 'ablation_summary.csv'}")
        
        # Print summary
        print("\n" + "="*70)
        print("ABLATION SUMMARY")
        print("="*70)
        print(ablation_summary.to_string(index=False))
    
    if all_coefficients:
        coef_df = pd.concat(all_coefficients, ignore_index=True)
        coef_df.to_csv(out_dir / "coefficients.csv", index=False)
        print(f"[save] Saved coefficients to {out_dir / 'coefficients.csv'}")
    
    # Generate plots
    if all_metrics:
        generate_ablation_plots(out_dir, pd.DataFrame(all_metrics))
    
    print("\n[done] Training complete!")


def create_ablation_summary(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Create summary comparing model variants."""
    
    summary_rows = []
    
    for cluster in metrics_df["cluster"].unique():
        cluster_metrics = metrics_df[metrics_df["cluster"] == cluster]
        
        for _, row in cluster_metrics.iterrows():
            summary_rows.append({
                "cluster": cluster,
                "variant": row["variant"],
                "r2": row["r2"],
                "mdae_log": row["mdae_log"],
                "mdape": row["mdape"],
                "n_features": row["n_features"],
            })
    
    summary_df = pd.DataFrame(summary_rows)
    
    # Pivot for easier comparison
    return summary_df.sort_values(["cluster", "r2"], ascending=[True, False])


def generate_ablation_plots(out_dir: Path, metrics_df: pd.DataFrame):
    """Generate ablation comparison plots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    fig_dir = out_dir / "figures"
    
    # Filter to main variants (not baselines)
    model_variants = ["full", "no_timelimit", "timelimit_only"]
    plot_df = metrics_df[metrics_df["variant"].isin(model_variants + ["baseline_median"])]
    
    if plot_df.empty:
        return
    
    clusters = plot_df["cluster"].unique()
    
    # R² comparison bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(clusters))
    width = 0.2
    
    for i, variant in enumerate(model_variants + ["baseline_median"]):
        variant_data = plot_df[plot_df["variant"] == variant]
        r2_values = [variant_data[variant_data["cluster"] == c]["r2"].values[0] 
                     if len(variant_data[variant_data["cluster"] == c]) > 0 else 0 
                     for c in clusters]
        ax.bar(x + i * width, r2_values, width, label=variant)
    
    ax.set_xlabel("Cluster")
    ax.set_ylabel("R²")
    ax.set_title("Ablation Study: R² by Model Variant")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(clusters)
    ax.legend()
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(fig_dir / "ablation_r2_comparison.png", dpi=150)
    plt.close()
    
    print(f"[plot] Saved ablation plots to {fig_dir}")


def main():
    parser = argparse.ArgumentParser(description="EXP-003b: Linear Regression with Ablation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train regression models with ablation")
    train_parser.add_argument("--input-dir", required=True, help="Path to FRESCO chunks directory")
    train_parser.add_argument("--out-dir", required=True, help="Output directory")
    train_parser.add_argument("--threads", type=int, default=8, help="DuckDB threads")
    train_parser.add_argument("--alpha", type=float, default=1.0, help="Ridge regularization")
    train_parser.set_defaults(func=train_command)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
