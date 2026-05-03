#!/usr/bin/env python3
"""
EXP-003: Linear Regression Baseline for Runtime Prediction

Trains per-cluster Ridge Regression models to predict log(runtime) from
pre-execution features (ncores, nhosts, timelimit, wait_sec, etc.).

Usage:
    python exp003_linear_regression.py train --input-dir <job_rollup_dir> --out-dir <output>
"""

from __future__ import annotations

import argparse
import pickle
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


# Pre-execution features only (no leakage)
NUMERIC_FEATURES = ["ncores", "nhosts", "timelimit", "wait_sec"]
CATEGORICAL_FEATURES = ["start_month"]  # source_token handled separately

TARGET = "runtime_sec"


def load_job_rollup(input_dir: Path, threads: int = 8, from_raw: bool = False) -> pd.DataFrame:
    """Load job rollup from EXP-001 or compute from raw FRESCO data."""
    _require_duckdb()
    import duckdb

    con = duckdb.connect(":memory:")
    con.execute(f"PRAGMA threads={threads}")
    
    if from_raw:
        # Load directly from raw FRESCO chunks
        glob_pattern = str((input_dir / "**" / "*.parquet").as_posix())
        
        sql = f"""
        WITH job_stats AS (
            SELECT
                jid,
                -- Extract source token from suffix pattern
                CASE 
                    WHEN jid LIKE '%_S' THEN 'S'
                    WHEN jid LIKE '%_C' THEN 'C'
                    ELSE 'NONE'
                END AS source_token,
                MIN(start_time) AS start_time,
                MIN(end_time) AS end_time,
                MIN(submit_time) AS submit_time,
                MAX(ncores) AS ncores,
                MAX(nhosts) AS nhosts,
                MAX(timelimit) AS timelimit
            FROM read_parquet('{glob_pattern}', union_by_name=true)
            WHERE start_time IS NOT NULL AND end_time IS NOT NULL
            GROUP BY jid
        )
        SELECT
            jid,
            source_token,
            EXTRACT(YEAR FROM start_time) AS start_year,
            EXTRACT(MONTH FROM start_time) AS start_month,
            EXTRACT(EPOCH FROM (end_time - start_time)) AS runtime_sec,
            EXTRACT(EPOCH FROM (start_time - submit_time)) AS wait_sec,
            ncores,
            nhosts,
            timelimit
        FROM job_stats
        WHERE EXTRACT(EPOCH FROM (end_time - start_time)) > 0
          AND EXTRACT(EPOCH FROM (end_time - start_time)) < 31536000
        """
        
        print(f"[load] Loading raw FRESCO data from {input_dir}...")
    else:
        # Load from EXP-001 job_rollup
        glob_pattern = str((input_dir / "**" / "*.parquet").as_posix())
        
        sql = f"""
        SELECT
            jid,
            source_token,
            start_year,
            start_month,
            runtime_sec,
            wait_sec,
            ncores,
            nhosts,
            timelimit
        FROM read_parquet('{glob_pattern}', hive_partitioning=1, union_by_name=true)
        WHERE runtime_sec IS NOT NULL 
          AND runtime_sec > 0
          AND runtime_sec < 31536000  -- Filter extreme outliers (>1 year)
        """
        
        print(f"[load] Loading job rollup from {input_dir}...")
    
    df = con.execute(sql).fetchdf()
    con.close()
    
    print(f"[load] Loaded {len(df):,} jobs with valid runtime")
    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Prepare feature matrix with preprocessing."""
    
    df = df.copy()
    
    # Log-transform target
    df["log_runtime"] = np.log1p(df["runtime_sec"])
    
    # Log-transform skewed numeric features
    for col in ["timelimit", "wait_sec"]:
        if col in df.columns:
            df[f"log_{col}"] = np.log1p(df[col].clip(lower=0))
    
    # One-hot encode month (cyclical patterns)
    month_dummies = pd.get_dummies(df["start_month"], prefix="month", dtype=float)
    df = pd.concat([df, month_dummies], axis=1)
    
    # Final feature list
    feature_cols = ["ncores", "nhosts", "log_timelimit", "log_wait_sec"]
    feature_cols += [c for c in month_dummies.columns]
    
    # Handle missing values
    for col in feature_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    return df, feature_cols


def time_split(df: pd.DataFrame, train_frac: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by time (year, month) to avoid temporal leakage."""
    
    # Create time index
    df = df.copy()
    df["time_idx"] = df["start_year"] * 100 + df["start_month"]
    
    # Find cutoff
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


def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray, 
                   y_test_original: np.ndarray) -> dict:
    """Compute evaluation metrics."""
    _require_sklearn()
    from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
    
    y_pred = model.predict(X_test)
    
    # Metrics on log scale
    r2 = r2_score(y_test, y_pred)
    mae_log = mean_absolute_error(y_test, y_pred)
    rmse_log = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # Metrics on original scale
    y_pred_original = np.expm1(y_pred)
    y_pred_original = np.clip(y_pred_original, 0, None)
    
    mae_original = mean_absolute_error(y_test_original, y_pred_original)
    
    # MAPE (avoiding division by zero)
    mask = y_test_original > 0
    if mask.sum() > 0:
        mape = np.mean(np.abs(y_test_original[mask] - y_pred_original[mask]) / y_test_original[mask]) * 100
    else:
        mape = np.nan
    
    return {
        "r2": r2,
        "mae_log": mae_log,
        "rmse_log": rmse_log,
        "mae_sec": mae_original,
        "mape": mape,
    }


def train_command(args):
    """Train linear regression models per cluster."""
    _require_sklearn()
    
    input_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "models").mkdir(exist_ok=True)
    (out_dir / "figures").mkdir(exist_ok=True)
    
    # Load data
    df = load_job_rollup(input_dir, threads=args.threads, from_raw=args.from_raw)
    
    # Prepare features
    df, feature_cols = prepare_features(df)
    
    clusters = df["source_token"].unique()
    print(f"[train] Found clusters: {clusters}")
    print(f"[train] Features: {feature_cols}")
    
    all_metrics = []
    all_coefficients = []
    all_predictions = []
    
    for cluster in clusters:
        print(f"\n{'='*60}")
        print(f"CLUSTER: {cluster}")
        print("="*60)
        
        cluster_df = df[df["source_token"] == cluster].copy()
        
        if len(cluster_df) < 1000:
            print(f"[train] Skipping {cluster}: only {len(cluster_df)} jobs")
            continue
        
        # Time-based split
        train_df, test_df = time_split(cluster_df, train_frac=0.8)
        
        if len(test_df) < 100:
            print(f"[train] Skipping {cluster}: insufficient test data")
            continue
        
        # Prepare arrays
        available_features = [c for c in feature_cols if c in train_df.columns]
        X_train = train_df[available_features].values
        y_train = train_df["log_runtime"].values
        X_test = test_df[available_features].values
        y_test = test_df["log_runtime"].values
        y_test_original = test_df["runtime_sec"].values
        
        # Train model
        print(f"[train] Training Ridge Regression...")
        model = train_model(X_train, y_train, alpha=args.alpha)
        
        # Evaluate
        metrics = evaluate_model(model, X_test, y_test, y_test_original)
        metrics["cluster"] = cluster
        metrics["n_train"] = len(train_df)
        metrics["n_test"] = len(test_df)
        all_metrics.append(metrics)
        
        print(f"[eval] R² = {metrics['r2']:.4f}")
        print(f"[eval] MAE (log) = {metrics['mae_log']:.4f}")
        print(f"[eval] MAE (sec) = {metrics['mae_sec']:.1f}")
        print(f"[eval] MAPE = {metrics['mape']:.1f}%")
        
        # Save coefficients
        coef_df = pd.DataFrame({
            "feature": available_features,
            "coefficient": model.coef_,
            "abs_coefficient": np.abs(model.coef_),
        }).sort_values("abs_coefficient", ascending=False)
        coef_df["cluster"] = cluster
        coef_df["intercept"] = model.intercept_
        all_coefficients.append(coef_df)
        
        print(f"\n[coef] Top 5 features:")
        print(coef_df.head(5).to_string(index=False))
        
        # Save model
        model_path = out_dir / "models" / f"ridge_{cluster}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump({"model": model, "features": available_features}, f)
        
        # Collect predictions for analysis
        test_df = test_df.copy()
        test_df["predicted_log_runtime"] = model.predict(X_test)
        test_df["predicted_runtime_sec"] = np.expm1(test_df["predicted_log_runtime"])
        test_df["residual"] = test_df["log_runtime"] - test_df["predicted_log_runtime"]
        all_predictions.append(test_df[["jid", "source_token", "start_year", "start_month",
                                         "runtime_sec", "predicted_runtime_sec", "residual"]])
    
    # Save all results
    if all_metrics:
        metrics_df = pd.DataFrame(all_metrics)
        metrics_df.to_csv(out_dir / "metrics.csv", index=False)
        print(f"\n[save] Saved metrics to {out_dir / 'metrics.csv'}")
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(metrics_df.to_string(index=False))
    
    if all_coefficients:
        coef_df = pd.concat(all_coefficients, ignore_index=True)
        coef_df.to_csv(out_dir / "coefficients.csv", index=False)
        print(f"[save] Saved coefficients to {out_dir / 'coefficients.csv'}")
    
    if all_predictions:
        pred_df = pd.concat(all_predictions, ignore_index=True)
        pred_df.to_parquet(out_dir / "predictions.parquet", index=False)
        print(f"[save] Saved predictions to {out_dir / 'predictions.parquet'}")
    
    # Generate plots
    generate_plots(out_dir, all_predictions)
    
    print("\n[done] Training complete!")


def generate_plots(out_dir: Path, all_predictions: list):
    """Generate diagnostic plots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    if not all_predictions:
        return
    
    pred_df = pd.concat(all_predictions, ignore_index=True)
    fig_dir = out_dir / "figures"
    
    # 1. Actual vs Predicted (log scale)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    clusters = pred_df["source_token"].unique()
    
    for i, cluster in enumerate(clusters[:3]):
        ax = axes[i]
        cluster_data = pred_df[pred_df["source_token"] == cluster].sample(
            min(5000, len(pred_df[pred_df["source_token"] == cluster]))
        )
        
        ax.scatter(np.log1p(cluster_data["runtime_sec"]), 
                   np.log1p(cluster_data["predicted_runtime_sec"]),
                   alpha=0.1, s=1)
        
        # Diagonal line
        lims = [ax.get_xlim()[0], ax.get_xlim()[1]]
        ax.plot(lims, lims, 'r--', alpha=0.8, label="Perfect")
        
        ax.set_xlabel("Actual log(runtime)")
        ax.set_ylabel("Predicted log(runtime)")
        ax.set_title(f"{cluster}")
        ax.legend()
    
    plt.tight_layout()
    plt.savefig(fig_dir / "actual_vs_predicted.png", dpi=150)
    plt.close()
    
    # 2. Residual distribution
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for i, cluster in enumerate(clusters[:3]):
        ax = axes[i]
        cluster_data = pred_df[pred_df["source_token"] == cluster]
        
        ax.hist(cluster_data["residual"], bins=100, alpha=0.7, edgecolor="black")
        ax.axvline(0, color="red", linestyle="--")
        ax.set_xlabel("Residual (log scale)")
        ax.set_ylabel("Count")
        ax.set_title(f"{cluster} (μ={cluster_data['residual'].mean():.2f})")
    
    plt.tight_layout()
    plt.savefig(fig_dir / "residual_distribution.png", dpi=150)
    plt.close()
    
    print(f"[plot] Saved diagnostic plots to {fig_dir}")


def main():
    parser = argparse.ArgumentParser(description="EXP-003: Linear Regression for Runtime Prediction")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train regression models")
    train_parser.add_argument("--input-dir", required=True, help="Path to data directory (job_rollup or raw FRESCO)")
    train_parser.add_argument("--out-dir", required=True, help="Output directory")
    train_parser.add_argument("--threads", type=int, default=8, help="DuckDB threads")
    train_parser.add_argument("--alpha", type=float, default=1.0, help="Ridge regularization")
    train_parser.add_argument("--from-raw", action="store_true", help="Load from raw FRESCO chunks instead of job_rollup")
    train_parser.set_defaults(func=train_command)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
