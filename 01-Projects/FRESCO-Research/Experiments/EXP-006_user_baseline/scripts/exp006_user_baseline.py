#!/usr/bin/env python3
"""
EXP-006: User Baseline Experiment
=================================
Quantify how much of the apparent model performance is user memorization.

Tests:
1. User-median baseline: Predict each job as user's historical median runtime
2. User-ID as feature: Add user identifier to model features
3. Compare against XGBoost/Ridge on time-based split

If user-median baseline rivals XGBoost, user identity is the dominant signal.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import hashlib

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor


def load_all_clusters(input_dir: str, threads: int = 8) -> pd.DataFrame:
    """Load all clusters with user info and source_token."""
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
            filename,
            CASE 
                WHEN regexp_matches(filename, '.*[/\\\\]\\d{{2}}_S\\.parquet$') THEN 'S'
                WHEN regexp_matches(filename, '.*[/\\\\]\\d{{2}}_C\\.parquet$') THEN 'C'
                ELSE 'NONE'
            END AS source_token
        FROM read_parquet('{input_dir}/**/*.parquet', filename=true)
        WHERE CAST(timelimit AS DOUBLE) > 0
          AND start_time IS NOT NULL
          AND end_time IS NOT NULL
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
            MAX(account) AS account,
            MAX(source_token) AS source_token
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
        source_token,
        EXTRACT(YEAR FROM start_time) * 100 + EXTRACT(MONTH FROM start_time) AS yearmonth,
        EXTRACT(EPOCH FROM (end_time - start_time)) AS runtime_sec
    FROM agg
    WHERE EXTRACT(EPOCH FROM (end_time - start_time)) > 0
    """
    
    print(f"[load] Loading data from {input_dir}...")
    df = con.execute(sql).fetchdf()
    print(f"[load] Loaded {len(df):,} jobs")
    for st in sorted(df['source_token'].unique()):
        n = (df['source_token'] == st).sum()
        users = df[df['source_token'] == st]['username'].nunique()
        print(f"       {st}: {n:,} jobs, {users:,} unique users")
    return df


def time_based_split(df: pd.DataFrame, cluster: str, test_months: int = 2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Time-based split for a specific cluster."""
    cdf = df[df['source_token'] == cluster].copy()
    yearmonths = sorted(cdf['yearmonth'].unique())
    cutoff_idx = max(1, len(yearmonths) - test_months)
    cutoff = yearmonths[cutoff_idx]
    
    train = cdf[cdf['yearmonth'] < cutoff].copy()
    test = cdf[cdf['yearmonth'] >= cutoff].copy()
    
    print(f"[split] {cluster}: Train {len(train):,}, Test {len(test):,}, Cutoff: {cutoff}")
    return train, test


def compute_user_medians(train_df: pd.DataFrame) -> dict[str, float]:
    """Compute median log(runtime) per user from training data."""
    train_df = train_df.copy()
    train_df['log_runtime'] = np.log(train_df['runtime_sec'])
    user_medians = train_df.groupby('username')['log_runtime'].median().to_dict()
    global_median = train_df['log_runtime'].median()
    return user_medians, global_median


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Calculate evaluation metrics."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mdae = np.median(np.abs(y_true - y_pred))
    
    # Convert to runtime space
    y_true_sec = np.exp(y_true)
    y_pred_sec = np.exp(y_pred)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ape = np.abs(y_true_sec - y_pred_sec) / y_true_sec * 100
        ape = ape[np.isfinite(ape)]
    mdape = np.median(ape) if len(ape) > 0 else np.nan
    
    return {'r2': r2, 'mae_log': mae, 'mdae_log': mdae, 'rmse_log': rmse, 'mdape': mdape}


def prepare_features(df: pd.DataFrame, variant: str, user_encoder: LabelEncoder = None) -> tuple[np.ndarray, list[str], LabelEncoder]:
    """
    Prepare features based on variant.
    
    Variants:
    - no_timelimit: ncores, nhosts
    - with_timelimit: ncores, nhosts, log_timelimit
    - with_user: ncores, nhosts, user_id (encoded)
    - with_timelimit_and_user: ncores, nhosts, log_timelimit, user_id
    """
    df = df.copy()
    # Fill NaN values with 0 for numeric columns
    df['ncores'] = pd.to_numeric(df['ncores'], errors='coerce').fillna(1)
    df['nhosts'] = pd.to_numeric(df['nhosts'], errors='coerce').fillna(1)
    df['timelimit'] = pd.to_numeric(df['timelimit'], errors='coerce').fillna(3600)
    
    df['log_ncores'] = np.log1p(df['ncores'])
    df['log_nhosts'] = np.log1p(df['nhosts'])
    df['log_timelimit'] = np.log1p(df['timelimit'])
    
    if variant == 'no_timelimit':
        feature_cols = ['log_ncores', 'log_nhosts']
        X = df[feature_cols].values
    elif variant == 'with_timelimit':
        feature_cols = ['log_ncores', 'log_nhosts', 'log_timelimit']
        X = df[feature_cols].values
    elif variant == 'with_user':
        if user_encoder is None:
            user_encoder = LabelEncoder()
            user_ids = user_encoder.fit_transform(df['username'])
        else:
            # Handle unseen users
            known = set(user_encoder.classes_)
            df['username_safe'] = df['username'].apply(lambda x: x if x in known else '__UNKNOWN__')
            if '__UNKNOWN__' not in known:
                user_encoder.classes_ = np.append(user_encoder.classes_, '__UNKNOWN__')
            user_ids = user_encoder.transform(df['username_safe'])
        feature_cols = ['log_ncores', 'log_nhosts', 'user_id']
        X = np.column_stack([df['log_ncores'].values, df['log_nhosts'].values, user_ids])
    elif variant == 'with_timelimit_and_user':
        if user_encoder is None:
            user_encoder = LabelEncoder()
            user_ids = user_encoder.fit_transform(df['username'])
        else:
            known = set(user_encoder.classes_)
            df['username_safe'] = df['username'].apply(lambda x: x if x in known else '__UNKNOWN__')
            if '__UNKNOWN__' not in known:
                user_encoder.classes_ = np.append(user_encoder.classes_, '__UNKNOWN__')
            user_ids = user_encoder.transform(df['username_safe'])
        feature_cols = ['log_ncores', 'log_nhosts', 'log_timelimit', 'user_id']
        X = np.column_stack([df['log_ncores'].values, df['log_nhosts'].values, df['log_timelimit'].values, user_ids])
    else:
        raise ValueError(f"Unknown variant: {variant}")
    
    return X, feature_cols, user_encoder


def train_command(args):
    """Run user baseline experiments."""
    df = load_all_clusters(args.input_dir, args.threads)
    
    results = []
    clusters = ['S', 'C', 'NONE']
    
    for cluster in clusters:
        cdf = df[df['source_token'] == cluster]
        if len(cdf) < 1000:
            print(f"\n[skip] {cluster}: Not enough data ({len(cdf)} jobs)")
            continue
            
        print(f"\n{'='*70}")
        print(f"CLUSTER: {cluster}")
        print('='*70)
        
        train_df, test_df = time_based_split(df, cluster)
        
        if len(train_df) < 100 or len(test_df) < 100:
            print(f"[skip] Not enough data after split")
            continue
        
        y_test = np.log(test_df['runtime_sec'].values)
        
        # 1. Global median baseline
        global_median = np.log(train_df['runtime_sec']).median()
        y_pred_global = np.full_like(y_test, global_median)
        metrics = evaluate_model(y_test, y_pred_global)
        metrics.update({'variant': 'global_median', 'model_type': 'baseline', 'cluster': cluster,
                       'n_train': len(train_df), 'n_test': len(test_df)})
        results.append(metrics)
        print(f"\n--- global_median (baseline) ---")
        print(f"[eval] R² = {metrics['r2']:.4f}")
        print(f"[eval] MdAPE = {metrics['mdape']:.1f}%")
        
        # 2. User-median baseline (key test!)
        user_medians, fallback_median = compute_user_medians(train_df)
        y_pred_user = np.array([
            user_medians.get(u, fallback_median) 
            for u in test_df['username']
        ])
        metrics = evaluate_model(y_test, y_pred_user)
        metrics.update({'variant': 'user_median', 'model_type': 'baseline', 'cluster': cluster,
                       'n_train': len(train_df), 'n_test': len(test_df)})
        results.append(metrics)
        print(f"\n--- user_median (key baseline) ---")
        print(f"[eval] R² = {metrics['r2']:.4f}")
        print(f"[eval] MdAPE = {metrics['mdape']:.1f}%")
        
        # 3-6. Model variants
        for variant in ['no_timelimit', 'with_timelimit', 'with_user', 'with_timelimit_and_user']:
            for model_type in ['xgboost', 'ridge']:
                print(f"\n--- {variant} / {model_type} ---")
                
                X_train, _, user_enc = prepare_features(train_df, variant, None)
                X_test, _, _ = prepare_features(test_df, variant, user_enc)
                y_train = np.log(train_df['runtime_sec'].values)
                
                if model_type == 'xgboost':
                    model = XGBRegressor(
                        n_estimators=100, max_depth=6, learning_rate=0.1,
                        subsample=0.8, colsample_bytree=0.8, n_jobs=-1,
                        random_state=42, verbosity=0
                    )
                else:
                    model = Ridge(alpha=1.0)
                
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                metrics = evaluate_model(y_test, y_pred)
                metrics.update({'variant': variant, 'model_type': model_type, 'cluster': cluster,
                               'n_train': len(train_df), 'n_test': len(test_df)})
                results.append(metrics)
                
                print(f"[eval] R² = {metrics['r2']:.4f}")
                print(f"[eval] MdAPE = {metrics['mdape']:.1f}%")
    
    # Save results
    results_df = pd.DataFrame(results)
    out_path = Path(args.out_dir) / 'user_baseline_results.csv'
    results_df.to_csv(out_path, index=False)
    print(f"\n[save] Results saved to {out_path}")
    
    # Summary
    print("\n" + "="*70)
    print("KEY COMPARISON: Does user-median rival XGBoost?")
    print("="*70)
    
    for cluster in clusters:
        cdf = results_df[results_df['cluster'] == cluster]
        if len(cdf) == 0:
            continue
            
        user_med = cdf[cdf['variant'] == 'user_median']['r2'].values
        xgb_no_tl = cdf[(cdf['variant'] == 'no_timelimit') & (cdf['model_type'] == 'xgboost')]['r2'].values
        xgb_tl = cdf[(cdf['variant'] == 'with_timelimit') & (cdf['model_type'] == 'xgboost')]['r2'].values
        xgb_user = cdf[(cdf['variant'] == 'with_user') & (cdf['model_type'] == 'xgboost')]['r2'].values
        
        print(f"\n{cluster}:")
        if len(user_med) > 0:
            print(f"  user_median (baseline):     R² = {user_med[0]:.4f}")
        if len(xgb_no_tl) > 0:
            print(f"  XGBoost no_timelimit:       R² = {xgb_no_tl[0]:.4f}")
        if len(xgb_tl) > 0:
            print(f"  XGBoost with_timelimit:     R² = {xgb_tl[0]:.4f}")
        if len(xgb_user) > 0:
            print(f"  XGBoost with_user:          R² = {xgb_user[0]:.4f}")
        
        if len(user_med) > 0 and len(xgb_no_tl) > 0:
            if user_med[0] >= xgb_no_tl[0] * 0.9:
                print(f"  → USER IDENTITY DOMINATES: user_median rivals XGBoost")
            else:
                print(f"  → XGBoost adds value beyond user identity")
    
    print("\n[done] User baseline experiment complete!")


def main():
    parser = argparse.ArgumentParser(description='EXP-006: User Baseline')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    train_parser = subparsers.add_parser('train', help='Run experiments')
    train_parser.add_argument('--input-dir', required=True, help='Path to FRESCO chunks')
    train_parser.add_argument('--out-dir', required=True, help='Output directory')
    train_parser.add_argument('--threads', type=int, default=8, help='DuckDB threads')
    train_parser.set_defaults(func=train_command)
    
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == '__main__':
    main()
