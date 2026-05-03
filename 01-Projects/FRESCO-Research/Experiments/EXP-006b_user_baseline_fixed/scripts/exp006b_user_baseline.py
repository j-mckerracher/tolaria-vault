#!/usr/bin/env python3
"""
EXP-006b: User Baseline (Fixed)
================================
Fixed version addressing issues from EXP-006:
1. Proper time splits with reasonable test set sizes
2. Data validation and filtering
3. Log-space metrics throughout
4. Handle timelimit edge cases

Key tests:
1. User-median baseline vs models (time-based split)
2. User-aware split to confirm leakage
3. User ID as feature to quantify upper bound
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor


def load_all_clusters(input_dir: str, threads: int = 8) -> pd.DataFrame:
    """Load all clusters with data validation."""
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
            filename,
            CASE 
                WHEN regexp_matches(filename, '.*[/\\\\]\\d{{2}}_S\\.parquet$') THEN 'S'
                WHEN regexp_matches(filename, '.*[/\\\\]\\d{{2}}_C\\.parquet$') THEN 'C'
                ELSE 'NONE'
            END AS source_token
        FROM read_parquet('{input_dir}/**/*.parquet', filename=true)
        WHERE start_time IS NOT NULL
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
        source_token,
        EXTRACT(YEAR FROM start_time) * 100 + EXTRACT(MONTH FROM start_time) AS yearmonth,
        EXTRACT(EPOCH FROM (end_time - start_time)) AS runtime_sec
    FROM agg
    """
    
    print(f"[load] Loading data from {input_dir}...")
    df = con.execute(sql).fetchdf()
    print(f"[load] Raw: {len(df):,} jobs")
    
    # Data validation
    print("\n[validate] Checking data quality...")
    print(f"  runtime_sec: min={df['runtime_sec'].min():.1f}, max={df['runtime_sec'].max():.1f}")
    print(f"  runtime_sec <= 0: {(df['runtime_sec'] <= 0).sum():,} jobs")
    print(f"  timelimit null: {df['timelimit'].isna().sum():,} jobs")
    print(f"  timelimit <= 0: {(df['timelimit'] <= 0).sum():,} jobs")
    
    # Filter invalid rows
    df = df[df['runtime_sec'] > 0].copy()
    df = df[df['timelimit'].notna() & (df['timelimit'] > 0)].copy()
    df = df[df['ncores'].notna() & (df['ncores'] > 0)].copy()
    df = df[df['nhosts'].notna() & (df['nhosts'] > 0)].copy()
    df = df[df['username'].notna()].copy()
    
    print(f"[validate] After filtering: {len(df):,} jobs")
    
    for st in sorted(df['source_token'].unique()):
        n = (df['source_token'] == st).sum()
        users = df[df['source_token'] == st]['username'].nunique()
        print(f"       {st}: {n:,} jobs, {users:,} unique users")
    
    return df


def time_based_split(df: pd.DataFrame, test_frac: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Time-based split with reasonable test size."""
    yearmonths = sorted(df['yearmonth'].unique())
    n_test = max(1, int(len(yearmonths) * test_frac))
    cutoff = yearmonths[-(n_test)]
    
    train = df[df['yearmonth'] < cutoff].copy()
    test = df[df['yearmonth'] >= cutoff].copy()
    
    print(f"[split] Time-based: Train {len(train):,}, Test {len(test):,}, Cutoff: {cutoff}")
    return train, test


def user_aware_split(df: pd.DataFrame, test_frac: float = 0.2, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """User-aware split: hold out entire users."""
    np.random.seed(seed)
    users = df['username'].unique()
    np.random.shuffle(users)
    
    n_test_users = max(1, int(len(users) * test_frac))
    test_users = set(users[:n_test_users])
    
    test = df[df['username'].isin(test_users)].copy()
    train = df[~df['username'].isin(test_users)].copy()
    
    print(f"[split] User-aware: Train {len(train):,} ({len(users) - n_test_users:,} users), "
          f"Test {len(test):,} ({n_test_users:,} users)")
    return train, test


def evaluate_log_space(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> dict:
    """Evaluate in log space with proper metrics."""
    r2 = r2_score(y_true_log, y_pred_log)
    mae = mean_absolute_error(y_true_log, y_pred_log)
    rmse = np.sqrt(mean_squared_error(y_true_log, y_pred_log))
    mdae = np.median(np.abs(y_true_log - y_pred_log))
    
    # Multiplicative error (exp of log error)
    mult_error = np.exp(np.abs(y_true_log - y_pred_log))
    median_mult_error = np.median(mult_error)
    
    # Symmetric MAPE in original space
    y_true = np.exp(y_true_log)
    y_pred = np.exp(y_pred_log)
    smape = np.median(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8) * 100)
    
    return {
        'r2': r2,
        'mae_log': mae,
        'mdae_log': mdae,
        'rmse_log': rmse,
        'median_mult_error': median_mult_error,
        'smape': smape
    }


def train_command(args):
    """Run fixed user baseline experiments."""
    df = load_all_clusters(args.input_dir, args.threads)
    
    results = []
    clusters = ['S', 'C', 'NONE']
    
    for cluster in clusters:
        cdf = df[df['source_token'] == cluster].copy()
        if len(cdf) < 10000:
            print(f"\n[skip] {cluster}: Not enough data ({len(cdf)} jobs)")
            continue
        
        print(f"\n{'='*70}")
        print(f"CLUSTER: {cluster} ({len(cdf):,} jobs)")
        print('='*70)
        
        for split_type in ['time_based', 'user_aware']:
            print(f"\n--- Split: {split_type} ---")
            
            if split_type == 'time_based':
                train_df, test_df = time_based_split(cdf)
            else:
                train_df, test_df = user_aware_split(cdf)
            
            if len(train_df) < 1000 or len(test_df) < 1000:
                print(f"[skip] Not enough data after split")
                continue
            
            y_train_log = np.log(train_df['runtime_sec'].values)
            y_test_log = np.log(test_df['runtime_sec'].values)
            
            # 1. Global median baseline
            global_median = np.median(y_train_log)
            y_pred = np.full_like(y_test_log, global_median)
            metrics = evaluate_log_space(y_test_log, y_pred)
            metrics.update({'variant': 'global_median', 'model': 'baseline', 
                           'cluster': cluster, 'split': split_type,
                           'n_train': len(train_df), 'n_test': len(test_df)})
            results.append(metrics)
            print(f"  global_median: R²={metrics['r2']:.4f}, sMAPE={metrics['smape']:.1f}%")
            
            # 2. User-median baseline
            user_medians = train_df.groupby('username').apply(
                lambda g: np.median(np.log(g['runtime_sec']))
            ).to_dict()
            fallback = global_median
            y_pred = np.array([user_medians.get(u, fallback) for u in test_df['username']])
            metrics = evaluate_log_space(y_test_log, y_pred)
            metrics.update({'variant': 'user_median', 'model': 'baseline',
                           'cluster': cluster, 'split': split_type,
                           'n_train': len(train_df), 'n_test': len(test_df)})
            results.append(metrics)
            print(f"  user_median:   R²={metrics['r2']:.4f}, sMAPE={metrics['smape']:.1f}%")
            
            # Prepare features
            def make_features(data, variant, user_enc=None):
                X_list = [
                    np.log1p(data['ncores'].values).reshape(-1, 1),
                    np.log1p(data['nhosts'].values).reshape(-1, 1)
                ]
                if 'timelimit' in variant:
                    X_list.append(np.log1p(data['timelimit'].values).reshape(-1, 1))
                if 'user' in variant:
                    if user_enc is None:
                        user_enc = LabelEncoder()
                        uids = user_enc.fit_transform(data['username'])
                    else:
                        known = set(user_enc.classes_)
                        safe = data['username'].apply(lambda x: x if x in known else '__UNK__')
                        if '__UNK__' not in known:
                            user_enc.classes_ = np.append(user_enc.classes_, '__UNK__')
                        uids = user_enc.transform(safe)
                    X_list.append(uids.reshape(-1, 1))
                return np.hstack(X_list), user_enc
            
            # 3-6. Model variants
            variants = ['no_timelimit', 'with_timelimit', 'with_user', 'with_timelimit_user']
            for variant in variants:
                X_train, user_enc = make_features(train_df, variant)
                X_test, _ = make_features(test_df, variant, user_enc)
                
                # XGBoost
                model = XGBRegressor(
                    n_estimators=100, max_depth=6, learning_rate=0.1,
                    subsample=0.8, colsample_bytree=0.8, n_jobs=-1,
                    random_state=42, verbosity=0
                )
                model.fit(X_train, y_train_log)
                y_pred = model.predict(X_test)
                
                metrics = evaluate_log_space(y_test_log, y_pred)
                metrics.update({'variant': variant, 'model': 'xgboost',
                               'cluster': cluster, 'split': split_type,
                               'n_train': len(train_df), 'n_test': len(test_df)})
                results.append(metrics)
                print(f"  {variant} (xgb): R²={metrics['r2']:.4f}, sMAPE={metrics['smape']:.1f}%")
    
    # Save results
    results_df = pd.DataFrame(results)
    out_path = Path(args.out_dir) / 'user_baseline_fixed.csv'
    results_df.to_csv(out_path, index=False)
    print(f"\n[save] Results saved to {out_path}")
    
    # Summary
    print("\n" + "="*70)
    print("KEY COMPARISONS")
    print("="*70)
    
    for cluster in clusters:
        cdf = results_df[results_df['cluster'] == cluster]
        if len(cdf) == 0:
            continue
        
        print(f"\n{cluster}:")
        for split in ['time_based', 'user_aware']:
            sdf = cdf[cdf['split'] == split]
            if len(sdf) == 0:
                continue
            
            print(f"  {split}:")
            for _, row in sdf.iterrows():
                print(f"    {row['variant']:20s} ({row['model']:8s}): R²={row['r2']:7.4f}, sMAPE={row['smape']:6.1f}%")
    
    # Leakage quantification
    print("\n" + "-"*70)
    print("LEAKAGE QUANTIFICATION (time_based - user_aware)")
    print("-"*70)
    
    for cluster in clusters:
        cdf = results_df[(results_df['cluster'] == cluster) & 
                         (results_df['variant'] == 'no_timelimit') &
                         (results_df['model'] == 'xgboost')]
        if len(cdf) < 2:
            continue
        
        time_r2 = cdf[cdf['split'] == 'time_based']['r2'].values
        user_r2 = cdf[cdf['split'] == 'user_aware']['r2'].values
        
        if len(time_r2) > 0 and len(user_r2) > 0:
            delta = time_r2[0] - user_r2[0]
            print(f"  {cluster}: Δ R² = {delta:+.4f} (time={time_r2[0]:.4f}, user={user_r2[0]:.4f})")
    
    print("\n[done] Fixed user baseline complete!")


def main():
    parser = argparse.ArgumentParser(description='EXP-006b: User Baseline Fixed')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    train_parser = subparsers.add_parser('train', help='Run experiments')
    train_parser.add_argument('--input-dir', required=True)
    train_parser.add_argument('--out-dir', required=True)
    train_parser.add_argument('--threads', type=int, default=8)
    train_parser.set_defaults(func=train_command)
    
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == '__main__':
    main()
