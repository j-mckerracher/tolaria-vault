#!/usr/bin/env python3
"""
EXP-004: XGBoost Ablation for Runtime Prediction

Tests whether nonlinear models can recover signal from non-timelimit features.

Usage:
    python exp004_xgboost.py train --input-dir <fresco_chunks> --out-dir <output>
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _require_xgboost():
    try:
        import xgboost
    except ImportError:
        sys.exit("xgboost not installed. Run: pip install xgboost")


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


# Feature sets
FEATURES_FULL = ["ncores", "nhosts", "log_timelimit", "log_wait_sec"]
FEATURES_NO_TIMELIMIT = ["ncores", "nhosts", "log_wait_sec"]

TARGET = "log_runtime"


def load_fresco_data(input_dir: Path, threads: int = 8) -> pd.DataFrame:
    """Load FRESCO data with source_token extracted from filename."""
    _require_duckdb()
    import duckdb

    glob_pattern = str((input_dir / "**" / "*.parquet").as_posix())
    
    con = duckdb.connect(":memory:")
    con.execute(f"PRAGMA threads={threads}")
    
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
            CASE 
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
    df = con.execute(sql).fetchdf()
    con.close()
    
    clusters = df["source_token"].value_counts()
    print(f"[load] Loaded {len(df):,} jobs")
    for cluster, count in clusters.items():
        print(f"       {cluster}: {count:,} jobs")
    
    return df


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare feature matrix."""
    df = df.copy()
    
    # Log-transform target
    df["log_runtime"] = np.log1p(df["runtime_sec"])
    
    # Log-transform skewed features
    df["log_timelimit"] = np.log1p(df["timelimit"].clip(lower=0))
    df["log_wait_sec"] = np.log1p(df["wait_sec"].clip(lower=0))
    
    # Handle missing values
    for col in FEATURES_FULL:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    return df


def time_split(df: pd.DataFrame, train_frac: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by time to avoid leakage."""
    df = df.copy()
    df["time_idx"] = df["start_year"] * 100 + df["start_month"]
    
    sorted_times = df["time_idx"].sort_values().unique()
    n_train = int(len(sorted_times) * train_frac)
    cutoff = sorted_times[n_train]
    
    train = df[df["time_idx"] < cutoff].copy()
    test = df[df["time_idx"] >= cutoff].copy()
    
    print(f"[split] Train: {len(train):,}, Test: {len(test):,}, Cutoff: {cutoff}")
    return train, test


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray, 
                   y_true_original: np.ndarray) -> dict:
    """Compute evaluation metrics."""
    _require_sklearn()
    from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
    
    r2 = r2_score(y_true, y_pred)
    mae_log = mean_absolute_error(y_true, y_pred)
    mdae_log = np.median(np.abs(y_true - y_pred))
    rmse_log = np.sqrt(mean_squared_error(y_true, y_pred))
    
    y_pred_original = np.expm1(y_pred)
    y_pred_original = np.clip(y_pred_original, 0, None)
    
    mae_sec = mean_absolute_error(y_true_original, y_pred_original)
    mdae_sec = np.median(np.abs(y_true_original - y_pred_original))
    
    mask = y_true_original > 60
    if mask.sum() > 0:
        pct_errors = np.abs(y_true_original[mask] - y_pred_original[mask]) / y_true_original[mask] * 100
        mape = np.mean(pct_errors)
        mdape = np.median(pct_errors)
    else:
        mape = np.nan
        mdape = np.nan
    
    return {
        "r2": r2, "mae_log": mae_log, "mdae_log": mdae_log, "rmse_log": rmse_log,
        "mae_sec": mae_sec, "mdae_sec": mdae_sec, "mape": mape, "mdape": mdape,
    }


def train_xgboost(X_train: np.ndarray, y_train: np.ndarray,
                  X_val: np.ndarray, y_val: np.ndarray,
                  params: dict = None):
    """Train XGBoost model with early stopping."""
    _require_xgboost()
    import xgboost as xgb
    
    if params is None:
        params = {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "n_jobs": -1,
        }
    
    model = xgb.XGBRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    return model


def train_ridge(X_train: np.ndarray, y_train: np.ndarray, alpha: float = 1.0):
    """Train Ridge Regression for comparison."""
    _require_sklearn()
    from sklearn.linear_model import Ridge
    
    model = Ridge(alpha=alpha, random_state=42)
    model.fit(X_train, y_train)
    return model


def train_command(args):
    """Train XGBoost models with ablation."""
    _require_xgboost()
    _require_sklearn()
    
    input_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "models").mkdir(exist_ok=True)
    (out_dir / "figures").mkdir(exist_ok=True)
    
    # Load data
    df = load_fresco_data(input_dir, threads=args.threads)
    df = prepare_features(df)
    
    clusters = sorted(df["source_token"].unique())
    print(f"\n[train] Training for clusters: {clusters}")
    
    all_metrics = []
    
    for cluster in clusters:
        print(f"\n{'='*70}")
        print(f"CLUSTER: {cluster}")
        print("="*70)
        
        cluster_df = df[df["source_token"] == cluster].copy()
        
        if len(cluster_df) < 1000:
            print(f"[skip] Only {len(cluster_df)} jobs")
            continue
        
        train_df, test_df = time_split(cluster_df, train_frac=0.8)
        
        if len(test_df) < 100:
            print(f"[skip] Insufficient test data")
            continue
        
        # Further split train for validation (early stopping)
        val_size = int(len(train_df) * 0.1)
        val_df = train_df.tail(val_size)
        train_df = train_df.head(len(train_df) - val_size)
        
        y_train = train_df["log_runtime"].values
        y_val = val_df["log_runtime"].values
        y_test = test_df["log_runtime"].values
        y_test_original = test_df["runtime_sec"].values
        
        # Define variants
        variants = {
            "xgb_full": (FEATURES_FULL, "xgboost"),
            "xgb_no_timelimit": (FEATURES_NO_TIMELIMIT, "xgboost"),
            "ridge_full": (FEATURES_FULL, "ridge"),
            "ridge_no_timelimit": (FEATURES_NO_TIMELIMIT, "ridge"),
        }
        
        for variant_name, (features, model_type) in variants.items():
            print(f"\n--- {variant_name} ---")
            
            available = [f for f in features if f in train_df.columns]
            X_train = train_df[available].values
            X_val = val_df[available].values
            X_test = test_df[available].values
            
            if model_type == "xgboost":
                model = train_xgboost(X_train, y_train, X_val, y_val)
            else:
                model = train_ridge(X_train, y_train)
            
            y_pred = model.predict(X_test)
            metrics = evaluate_model(y_test, y_pred, y_test_original)
            metrics["variant"] = variant_name
            metrics["model_type"] = model_type
            metrics["cluster"] = cluster
            metrics["n_train"] = len(train_df)
            metrics["n_test"] = len(test_df)
            metrics["n_features"] = len(available)
            all_metrics.append(metrics)
            
            print(f"[eval] R² = {metrics['r2']:.4f}")
            print(f"[eval] MdAE (log) = {metrics['mdae_log']:.4f}")
            print(f"[eval] MdAPE = {metrics['mdape']:.1f}%")
            
            # Save model
            model_path = out_dir / "models" / f"{variant_name}_{cluster}.pkl"
            with open(model_path, "wb") as f:
                pickle.dump({"model": model, "features": available}, f)
    
    # Save results
    if all_metrics:
        metrics_df = pd.DataFrame(all_metrics)
        metrics_df.to_csv(out_dir / "metrics_comparison.csv", index=False)
        
        # Create comparison summary
        print("\n" + "="*70)
        print("COMPARISON SUMMARY: XGBoost vs Ridge")
        print("="*70)
        
        summary = metrics_df.pivot_table(
            index=["cluster", "variant"],
            values=["r2", "mdae_log", "mdape"],
            aggfunc="first"
        ).round(4)
        print(summary.to_string())
        
        # Generate comparison plot
        generate_comparison_plot(out_dir, metrics_df)
    
    print("\n[done] Training complete!")


def generate_comparison_plot(out_dir: Path, metrics_df: pd.DataFrame):
    """Generate XGBoost vs Ridge comparison plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    clusters = metrics_df["cluster"].unique()
    x = np.arange(len(clusters))
    width = 0.2
    
    # R² comparison
    ax = axes[0]
    for i, variant in enumerate(["ridge_full", "ridge_no_timelimit", "xgb_full", "xgb_no_timelimit"]):
        data = metrics_df[metrics_df["variant"] == variant]
        values = [data[data["cluster"] == c]["r2"].values[0] if len(data[data["cluster"] == c]) > 0 else 0 for c in clusters]
        ax.bar(x + i * width, values, width, label=variant)
    
    ax.set_xlabel("Cluster")
    ax.set_ylabel("R²")
    ax.set_title("R² Comparison: XGBoost vs Ridge")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(clusters)
    ax.legend(fontsize=8)
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    
    # MdAPE comparison
    ax = axes[1]
    for i, variant in enumerate(["ridge_full", "ridge_no_timelimit", "xgb_full", "xgb_no_timelimit"]):
        data = metrics_df[metrics_df["variant"] == variant]
        values = [data[data["cluster"] == c]["mdape"].values[0] if len(data[data["cluster"] == c]) > 0 else 0 for c in clusters]
        ax.bar(x + i * width, values, width, label=variant)
    
    ax.set_xlabel("Cluster")
    ax.set_ylabel("MdAPE (%)")
    ax.set_title("MdAPE Comparison: XGBoost vs Ridge")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(clusters)
    ax.legend(fontsize=8)
    
    plt.tight_layout()
    plt.savefig(out_dir / "figures" / "xgb_vs_ridge_comparison.png", dpi=150)
    plt.close()
    
    print(f"[plot] Saved comparison plot")


def main():
    parser = argparse.ArgumentParser(description="EXP-004: XGBoost Ablation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    train_parser = subparsers.add_parser("train", help="Train XGBoost models")
    train_parser.add_argument("--input-dir", required=True, help="FRESCO chunks directory")
    train_parser.add_argument("--out-dir", required=True, help="Output directory")
    train_parser.add_argument("--threads", type=int, default=8, help="DuckDB threads")
    train_parser.set_defaults(func=train_command)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
