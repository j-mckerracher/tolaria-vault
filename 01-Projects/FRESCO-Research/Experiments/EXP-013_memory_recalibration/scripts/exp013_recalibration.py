#!/usr/bin/env python3
"""EXP-013: Memory recalibration for cross-site transfer.

Tests whether simple affine calibration in log space can rescue the catastrophic
transfer failures observed in EXP-011 (R² ≤ -21).

Strategy:
1. Train source models (same as EXP-011)
2. For each transfer scenario, fit affine calibration on small target sample:
   log(y_target) = a * log(y_pred_source) + b
3. Test three calibration set sizes: 1%, 5%, 10% of target data
4. Compare R² before vs after calibration

Expected: If EXP-012's hypothesis is correct (systematic offsets), calibration
should dramatically improve R² from negative to positive values.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor


CLUSTERS = ["S", "C", "NONE"]


@dataclass
class CalibrationResult:
    """Results from one calibration experiment."""
    train_cluster: str
    test_cluster: str
    calib_frac: float
    n_calib: int
    n_test: int
    # Before calibration
    r2_before: float
    mae_before: float
    # Calibration parameters
    calib_slope: float
    calib_intercept: float
    # After calibration
    r2_after: float
    mae_after: float
    # Improvement
    r2_improvement: float


def load_and_clean(input_dir: str, threads: int = 8) -> pd.DataFrame:
    """Load FRESCO data (same as EXP-011)."""
    temp_db_dir = "/depot/sbagchi/data/josh/FRESCO-Research/Experiments/EXP-013_memory_recalibration/temp"
    os.makedirs(temp_db_dir, exist_ok=True)
    
    con = duckdb.connect()
    con.execute(f"SET threads TO {threads}")
    con.execute("SET memory_limit = '48GB'")
    con.execute(f"SET temp_directory = '{temp_db_dir}'")

    sql = f"""
    WITH raw AS (
        SELECT
            jid,
            CAST(timelimit AS DOUBLE) AS timelimit_raw,
            CAST(ncores AS BIGINT) AS ncores,
            CAST(nhosts AS BIGINT) AS nhosts,
            start_time,
            end_time,
            CAST(value_memused AS DOUBLE) AS value_memused,
            filename,
            CASE
                WHEN filename LIKE '%_S.parquet' THEN 'S'
                WHEN filename LIKE '%_C.parquet' THEN 'C'
                ELSE 'NONE'
            END AS cluster
        FROM read_parquet('{input_dir}/**/*.parquet', filename=true)
        WHERE start_time IS NOT NULL AND end_time IS NOT NULL
    ),
    mem_agg AS (
        SELECT
            cluster,
            jid,
            MAX(value_memused) AS peak_memused,
            COUNT(CASE WHEN value_memused IS NOT NULL AND value_memused > 0 THEN 1 END) AS mem_sample_count
        FROM raw
        GROUP BY cluster, jid
    ),
    job_agg AS (
        SELECT
            cluster,
            jid,
            MAX(timelimit_raw) AS timelimit_raw,
            MAX(ncores) AS ncores,
            MAX(nhosts) AS nhosts,
            MIN(start_time) AS start_time,
            MAX(end_time) AS end_time
        FROM raw
        GROUP BY cluster, jid
    )
    SELECT
        j.jid,
        CASE WHEN j.cluster = 'S' THEN j.timelimit_raw * 60.0 ELSE j.timelimit_raw END AS timelimit_sec,
        j.ncores,
        j.nhosts,
        j.cluster,
        EXTRACT(YEAR FROM j.start_time) * 100 + EXTRACT(MONTH FROM j.start_time) AS yearmonth,
        EXTRACT(EPOCH FROM (j.end_time - j.start_time)) AS runtime_sec,
        m.peak_memused,
        m.mem_sample_count
    FROM job_agg j
    LEFT JOIN mem_agg m ON j.cluster = m.cluster AND j.jid = m.jid
    """

    print("[load] Loading data...")
    df = con.execute(sql).fetchdf()
    print(f"[load] Raw: {len(df):,} jobs")
    
    # Filter
    df = df[
        (df.mem_sample_count > 0) &
        (df.peak_memused > 0) &
        (df.runtime_sec > 0) &
        (df.runtime_sec < 30 * 86400) &
        (df.timelimit_sec > 0) &
        (df.timelimit_sec < 365 * 86400) &
        (df.ncores > 0) &
        (df.nhosts > 0)
    ].copy()
    
    print(f"[clean] After filters: {len(df):,} jobs")
    for cluster in CLUSTERS:
        cdf = df[df.cluster == cluster]
        print(f"        {cluster}: {len(cdf):,} jobs")
    
    con.close()
    return df


def time_split(df: pd.DataFrame, cluster: str, test_frac: float = 0.2):
    """Split data by time (last test_frac of yearmonths)."""
    cdf = df[df.cluster == cluster].copy()
    months = sorted(cdf.yearmonth.unique())
    cutoff_idx = int(len(months) * (1 - test_frac))
    cutoff = months[cutoff_idx]
    
    train = cdf[cdf.yearmonth < cutoff].copy()
    test = cdf[cdf.yearmonth >= cutoff].copy()
    
    print(f"[split] {cluster}: Train {len(train):,}, Test {len(test):,}, Cutoff: {cutoff}")
    return train, test


def prepare_features(df: pd.DataFrame):
    """Prepare features (same as EXP-011)."""
    X = np.column_stack([
        np.log1p(df.ncores.values),
        np.log1p(df.nhosts.values),
        np.log1p(df.timelimit_sec.values),
    ])
    y = np.log(df.peak_memused.values)
    return X, y


def train_model(X_train, y_train, seed=42):
    """Train XGBoost model (same as EXP-011)."""
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=seed,
    )
    model.fit(X_train, y_train)
    return model


def calibrate_affine(y_pred_log, y_true_log):
    """Fit affine calibration: y_true = a * y_pred + b."""
    lr = LinearRegression()
    lr.fit(y_pred_log.reshape(-1, 1), y_true_log)
    slope = lr.coef_[0]
    intercept = lr.intercept_
    return slope, intercept


def apply_calibration(y_pred_log, slope, intercept):
    """Apply affine calibration."""
    return slope * y_pred_log + intercept


def run_recalibration_experiment(
    df: pd.DataFrame,
    train_cluster: str,
    test_cluster: str,
    calib_fracs: list[float],
    seed: int = 42,
) -> list[CalibrationResult]:
    """Run recalibration experiment for one transfer scenario."""
    
    # Split data
    train_df, _ = time_split(df, train_cluster)
    test_df_full, _ = time_split(df, test_cluster)
    
    # Train source model
    X_train, y_train = prepare_features(train_df)
    model = train_model(X_train, y_train, seed=seed)
    
    # Prepare test set
    X_test, y_test = prepare_features(test_df_full)
    y_pred_uncalib = model.predict(X_test)
    
    # Baseline (no calibration)
    r2_before = r2_score(y_test, y_pred_uncalib)
    mae_before = mean_absolute_error(y_test, y_pred_uncalib)
    
    print(f"\n[recalib] {train_cluster} → {test_cluster}")
    print(f"          Before calibration: R²={r2_before:.4f}, MAE={mae_before:.4f}")
    
    results = []
    
    for calib_frac in calib_fracs:
        # Sample calibration set
        n_calib = int(len(test_df_full) * calib_frac)
        calib_df = test_df_full.sample(n=n_calib, random_state=seed)
        
        # Remaining test set
        test_df = test_df_full[~test_df_full.index.isin(calib_df.index)]
        
        # Get predictions for calibration set
        X_calib, y_calib = prepare_features(calib_df)
        y_pred_calib = model.predict(X_calib)
        
        # Fit calibration
        slope, intercept = calibrate_affine(y_pred_calib, y_calib)
        
        # Apply calibration to test set
        X_test_remain, y_test_remain = prepare_features(test_df)
        y_pred_uncalib_test = model.predict(X_test_remain)
        y_pred_calib_test = apply_calibration(y_pred_uncalib_test, slope, intercept)
        
        # Evaluate
        r2_after = r2_score(y_test_remain, y_pred_calib_test)
        mae_after = mean_absolute_error(y_test_remain, y_pred_calib_test)
        r2_improvement = r2_after - r2_before
        
        print(f"          Calib {calib_frac*100:.0f}% (n={n_calib:,}): "
              f"R²={r2_after:.4f} (Δ={r2_improvement:+.4f}), "
              f"slope={slope:.3f}, intercept={intercept:.3f}")
        
        results.append(CalibrationResult(
            train_cluster=train_cluster,
            test_cluster=test_cluster,
            calib_frac=calib_frac,
            n_calib=n_calib,
            n_test=len(test_df),
            r2_before=r2_before,
            mae_before=mae_before,
            calib_slope=slope,
            calib_intercept=intercept,
            r2_after=r2_after,
            mae_after=mae_after,
            r2_improvement=r2_improvement,
        ))
    
    return results


def main():
    parser = argparse.ArgumentParser(description="EXP-013: Memory recalibration")
    parser.add_argument("--input-dir", required=True, help="Path to FRESCO chunks")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--threads", type=int, default=8, help="DuckDB threads")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    print("[EXP-013] Memory Recalibration")
    print(f"[config] Input: {args.input_dir}")
    print(f"[config] Output: {args.out_dir}")
    
    # Load data
    df = load_and_clean(args.input_dir, threads=args.threads)
    
    # Calibration fractions to test
    calib_fracs = [0.01, 0.05, 0.10]
    
    # Focus on problematic transfers from EXP-011
    transfer_scenarios = [
        ("S", "NONE"),  # Worst case: R² = -21.3
        ("C", "NONE"),  # Also very bad: R² = -7.7
        ("NONE", "S"),  # Bad: R² = -6.4
        ("S", "C"),     # Moderate: R² = -0.12
        ("C", "S"),     # Moderate: R² = -0.33
        ("NONE", "C"),  # Bad: R² = -6.7
    ]
    
    all_results = []
    
    for train_cluster, test_cluster in transfer_scenarios:
        results = run_recalibration_experiment(
            df, train_cluster, test_cluster, calib_fracs, seed=args.seed
        )
        all_results.extend(results)
    
    # Save results
    results_df = pd.DataFrame([
        {
            "train_cluster": r.train_cluster,
            "test_cluster": r.test_cluster,
            "calib_frac": r.calib_frac,
            "n_calib": r.n_calib,
            "n_test": r.n_test,
            "r2_before": r.r2_before,
            "mae_before": r.mae_before,
            "calib_slope": r.calib_slope,
            "calib_intercept": r.calib_intercept,
            "r2_after": r.r2_after,
            "mae_after": r.mae_after,
            "r2_improvement": r.r2_improvement,
        }
        for r in all_results
    ])
    
    out_path = f"{args.out_dir}/exp013_recalibration_results.csv"
    results_df.to_csv(out_path, index=False)
    print(f"\n[save] Results saved to {out_path}")
    print("EXP-013 complete")


if __name__ == "__main__":
    main()
