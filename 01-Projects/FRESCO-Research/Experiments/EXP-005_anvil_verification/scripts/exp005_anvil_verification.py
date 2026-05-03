#!/usr/bin/env python3
"""
EXP-005: Anvil Verification Experiment
=======================================
Verify FIND-016: Does Anvil uniquely recover signal without timelimit?

Tests:
1. no_timelimit with vs without month feature
2. Add cores_per_node interaction feature
3. User-aware split (hold out entire users)

Hypothesis: If Anvil's no_timelimit gain is due to:
- Month feature → removing month will collapse performance
- Nonlinear interactions → cores_per_node should help
- User leakage → user-aware split will show lower R²
"""
from __future__ import annotations

import argparse
import pickle
from pathlib import Path
import hashlib

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


def load_anvil_data(input_dir: str, threads: int = 8) -> pd.DataFrame:
    """Load ONLY Anvil data (source_token='NONE') with user info."""
    con = duckdb.connect()
    con.execute(f"SET threads TO {threads}")
    con.execute("SET memory_limit = '48GB'")
    
    sql = f"""
    WITH raw AS (
        SELECT
            jid,
            CAST(timelimit AS DOUBLE) AS timelimit,
            CAST(ncores AS BIGINT) AS ncores,
            CAST(nhosts AS BIGINT) AS nhosts,
            start_time,
            end_time,
            username,
            account,
            filename
        FROM read_parquet('{input_dir}/**/*.parquet', filename=true)
        WHERE CAST(timelimit AS DOUBLE) > 0
          AND start_time IS NOT NULL
          AND end_time IS NOT NULL
          AND NOT regexp_matches(filename, '.*[/\\\\]\\d{{2}}_[SC]\\.parquet$')
    ),
    agg AS (
        SELECT
            jid,
            MAX(timelimit) AS timelimit,
            MAX(ncores) AS ncores,
            MAX(nhosts) AS nhosts,
            MIN(start_time) AS start_time,
            MAX(end_time) AS end_time,
            MAX(username) AS username,
            MAX(account) AS account
        FROM raw
        GROUP BY jid
    )
    SELECT
        jid,
        timelimit,
        ncores,
        nhosts,
        start_time,
        end_time,
        username,
        account,
        EXTRACT(YEAR FROM start_time) * 100 + EXTRACT(MONTH FROM start_time) AS yearmonth,
        EXTRACT(EPOCH FROM (end_time - start_time)) AS runtime_sec
    FROM agg
    WHERE EXTRACT(EPOCH FROM (end_time - start_time)) > 0
    """
    
    print(f"[load] Loading Anvil data from {input_dir}...")
    df = con.execute(sql).fetchdf()
    print(f"[load] Loaded {len(df):,} Anvil jobs")
    print(f"       Unique users: {df['username'].nunique():,}")
    print(f"       Unique accounts: {df['account'].nunique():,}")
    return df


def prepare_features(df: pd.DataFrame, variant: str) -> tuple[np.ndarray, list[str]]:
    """
    Prepare features based on variant.
    
    Variants:
    - no_timelimit: ncores, nhosts, month
    - no_month: ncores, nhosts (no timelimit, no month)
    - cores_per_node: ncores, nhosts, cores_per_node (no timelimit)
    - full_interaction: ncores, nhosts, month, cores_per_node (no timelimit)
    """
    df = df.copy()
    df['log_ncores'] = np.log1p(df['ncores'])
    df['log_nhosts'] = np.log1p(df['nhosts'])
    df['cores_per_node'] = df['ncores'] / df['nhosts'].clip(lower=1)
    df['log_cores_per_node'] = np.log1p(df['cores_per_node'])
    df['month'] = (df['yearmonth'] % 100).astype(int)
    
    if variant == 'no_timelimit':
        # Original: ncores, nhosts, month
        feature_cols = ['log_ncores', 'log_nhosts', 'month']
    elif variant == 'no_month':
        # Remove month: ncores, nhosts only
        feature_cols = ['log_ncores', 'log_nhosts']
    elif variant == 'cores_per_node':
        # Add interaction: ncores, nhosts, cores_per_node
        feature_cols = ['log_ncores', 'log_nhosts', 'log_cores_per_node']
    elif variant == 'full_interaction':
        # All: ncores, nhosts, month, cores_per_node
        feature_cols = ['log_ncores', 'log_nhosts', 'month', 'log_cores_per_node']
    else:
        raise ValueError(f"Unknown variant: {variant}")
    
    X = df[feature_cols].values
    return X, feature_cols


def time_based_split(df: pd.DataFrame, test_months: int = 2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Standard time-based split: train on earlier months, test on later."""
    yearmonths = sorted(df['yearmonth'].unique())
    cutoff_idx = len(yearmonths) - test_months
    cutoff = yearmonths[cutoff_idx]
    
    train = df[df['yearmonth'] < cutoff].copy()
    test = df[df['yearmonth'] >= cutoff].copy()
    
    print(f"[split] Time-based: Train {len(train):,}, Test {len(test):,}, Cutoff: {cutoff}")
    return train, test


def user_aware_split(df: pd.DataFrame, test_frac: float = 0.2, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    User-aware split: hold out entire users.
    All jobs from a user are either in train or test, never both.
    """
    np.random.seed(seed)
    users = df['username'].unique()
    np.random.shuffle(users)
    
    n_test_users = int(len(users) * test_frac)
    test_users = set(users[:n_test_users])
    
    test = df[df['username'].isin(test_users)].copy()
    train = df[~df['username'].isin(test_users)].copy()
    
    print(f"[split] User-aware: Train {len(train):,} jobs ({len(users) - n_test_users:,} users), "
          f"Test {len(test):,} jobs ({n_test_users:,} users)")
    return train, test


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray, log_space: bool = True) -> dict:
    """Calculate evaluation metrics."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mdae = np.median(np.abs(y_true - y_pred))
    
    if log_space:
        # Convert to runtime space for interpretable errors
        y_true_sec = np.exp(y_true)
        y_pred_sec = np.exp(y_pred)
        mae_sec = mean_absolute_error(y_true_sec, y_pred_sec)
        mdae_sec = np.median(np.abs(y_true_sec - y_pred_sec))
        
        # Percentage errors
        with np.errstate(divide='ignore', invalid='ignore'):
            ape = np.abs(y_true_sec - y_pred_sec) / y_true_sec * 100
            ape = ape[np.isfinite(ape)]
        mape = np.mean(ape) if len(ape) > 0 else np.nan
        mdape = np.median(ape) if len(ape) > 0 else np.nan
    else:
        mae_sec = mae
        mdae_sec = mdae
        mape = np.nan
        mdape = np.nan
    
    return {
        'r2': r2,
        'mae_log': mae,
        'mdae_log': mdae,
        'rmse_log': rmse,
        'mae_sec': mae_sec,
        'mdae_sec': mdae_sec,
        'mape': mape,
        'mdape': mdape
    }


def train_and_evaluate(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    variant: str,
    model_type: str = 'xgboost'
) -> dict:
    """Train model and evaluate."""
    X_train, feature_cols = prepare_features(train_df, variant)
    X_test, _ = prepare_features(test_df, variant)
    
    y_train = np.log(train_df['runtime_sec'].values)
    y_test = np.log(test_df['runtime_sec'].values)
    
    if model_type == 'xgboost':
        model = XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            random_state=42,
            verbosity=0
        )
    else:
        model = Ridge(alpha=1.0)
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    metrics = evaluate_model(y_test, y_pred, log_space=True)
    metrics['variant'] = variant
    metrics['model_type'] = model_type
    metrics['n_train'] = len(train_df)
    metrics['n_test'] = len(test_df)
    metrics['n_features'] = len(feature_cols)
    metrics['features'] = ','.join(feature_cols)
    
    return metrics


def train_command(args):
    """Run verification experiments."""
    df = load_anvil_data(args.input_dir, args.threads)
    
    results = []
    variants = ['no_timelimit', 'no_month', 'cores_per_node', 'full_interaction']
    split_types = ['time_based', 'user_aware']
    
    for split_type in split_types:
        print(f"\n{'='*70}")
        print(f"SPLIT TYPE: {split_type}")
        print('='*70)
        
        if split_type == 'time_based':
            train_df, test_df = time_based_split(df)
        else:
            train_df, test_df = user_aware_split(df)
        
        for variant in variants:
            for model_type in ['xgboost', 'ridge']:
                print(f"\n--- {variant} / {model_type} ---")
                
                metrics = train_and_evaluate(train_df, test_df, variant, model_type)
                metrics['split_type'] = split_type
                results.append(metrics)
                
                print(f"[eval] R² = {metrics['r2']:.4f}")
                print(f"[eval] MdAE (log) = {metrics['mdae_log']:.4f}")
                print(f"[eval] MdAPE = {metrics['mdape']:.1f}%")
    
    # Save results
    results_df = pd.DataFrame(results)
    out_path = Path(args.out_dir) / 'verification_results.csv'
    results_df.to_csv(out_path, index=False)
    print(f"\n[save] Results saved to {out_path}")
    
    # Summary comparison
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    # Pivot for comparison
    pivot = results_df.pivot_table(
        index=['split_type', 'variant'],
        columns='model_type',
        values=['r2', 'mdape']
    ).round(4)
    print(pivot)
    
    # Key comparisons
    print("\n" + "-"*70)
    print("KEY VERIFICATION TESTS:")
    print("-"*70)
    
    # Test 1: Does removing month collapse performance?
    xgb_no_tl = results_df[(results_df['variant'] == 'no_timelimit') & 
                           (results_df['model_type'] == 'xgboost') &
                           (results_df['split_type'] == 'time_based')]['r2'].values[0]
    xgb_no_month = results_df[(results_df['variant'] == 'no_month') & 
                              (results_df['model_type'] == 'xgboost') &
                              (results_df['split_type'] == 'time_based')]['r2'].values[0]
    print(f"\n1. Month feature importance:")
    print(f"   no_timelimit R² = {xgb_no_tl:.4f}")
    print(f"   no_month R² = {xgb_no_month:.4f}")
    print(f"   Δ R² = {xgb_no_tl - xgb_no_month:.4f}")
    if abs(xgb_no_tl - xgb_no_month) < 0.05:
        print(f"   → Month is NOT driving the signal")
    else:
        print(f"   → Month IS contributing significantly")
    
    # Test 2: Does cores_per_node help?
    xgb_cpn = results_df[(results_df['variant'] == 'cores_per_node') & 
                         (results_df['model_type'] == 'xgboost') &
                         (results_df['split_type'] == 'time_based')]['r2'].values[0]
    print(f"\n2. Cores_per_node interaction:")
    print(f"   no_month R² = {xgb_no_month:.4f}")
    print(f"   cores_per_node R² = {xgb_cpn:.4f}")
    print(f"   Δ R² = {xgb_cpn - xgb_no_month:.4f}")
    if xgb_cpn > xgb_no_month + 0.02:
        print(f"   → Interaction feature helps!")
    else:
        print(f"   → Interaction adds minimal value")
    
    # Test 3: User-aware vs time-based split
    xgb_time = results_df[(results_df['variant'] == 'no_timelimit') & 
                          (results_df['model_type'] == 'xgboost') &
                          (results_df['split_type'] == 'time_based')]['r2'].values[0]
    xgb_user = results_df[(results_df['variant'] == 'no_timelimit') & 
                          (results_df['model_type'] == 'xgboost') &
                          (results_df['split_type'] == 'user_aware')]['r2'].values[0]
    print(f"\n3. User leakage test:")
    print(f"   time_based R² = {xgb_time:.4f}")
    print(f"   user_aware R² = {xgb_user:.4f}")
    print(f"   Δ R² = {xgb_time - xgb_user:.4f}")
    if xgb_time - xgb_user > 0.10:
        print(f"   → SIGNIFICANT leakage detected! User-aware split shows lower R²")
    elif xgb_time - xgb_user > 0.05:
        print(f"   → Moderate leakage detected")
    else:
        print(f"   → No significant leakage")
    
    print("\n[done] Verification complete!")


def main():
    parser = argparse.ArgumentParser(description='EXP-005: Anvil Verification')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    train_parser = subparsers.add_parser('train', help='Run verification experiments')
    train_parser.add_argument('--input-dir', required=True, help='Path to FRESCO chunks')
    train_parser.add_argument('--out-dir', required=True, help='Output directory')
    train_parser.add_argument('--threads', type=int, default=8, help='DuckDB threads')
    train_parser.set_defaults(func=train_command)
    
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == '__main__':
    main()
