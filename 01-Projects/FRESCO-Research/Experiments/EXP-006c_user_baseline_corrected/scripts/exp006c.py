#!/usr/bin/env python3
"""
EXP-006c: User Baseline (Corrected)
===================================
Fixes from EXP-006b:
1. Fixed feature inclusion bug ('timelimit' in 'no_timelimit' was True)
2. Normalize timelimit to seconds across clusters (S uses minutes)
3. Remove extreme outliers (runtime > 30 days)
4. Focus on Stampede which has cleanest data
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


def load_and_clean(input_dir: str, threads: int = 8) -> pd.DataFrame:
    """Load data with proper cleaning and timelimit normalization."""
    con = duckdb.connect()
    con.execute(f"SET threads TO {threads}")
    con.execute("SET memory_limit = '48GB'")
    
    sql = f"""
    WITH raw AS (
        SELECT
            jid,
            CAST(timelimit AS DOUBLE) AS timelimit_raw,
            CAST(ncores AS BIGINT) AS ncores,
            CAST(nhosts AS BIGINT) AS nhosts,
            start_time,
            end_time,
            username,
            filename,
            CASE 
                WHEN filename LIKE '%_S.parquet' THEN 'S'
                WHEN filename LIKE '%_C.parquet' THEN 'C'
                ELSE 'NONE'
            END AS source_token
        FROM read_parquet('{input_dir}/**/*.parquet', filename=true)
        WHERE start_time IS NOT NULL
          AND end_time IS NOT NULL
    ),
    agg AS (
        SELECT
            jid,
            MAX(timelimit_raw) AS timelimit_raw,
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
        timelimit_raw,
        -- Normalize timelimit to seconds (S is in minutes, C/NONE in seconds)
        CASE 
            WHEN source_token = 'S' THEN timelimit_raw * 60.0
            ELSE timelimit_raw
        END AS timelimit_sec,
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
    
    # Validate timelimit normalization
    for st in ['S', 'C', 'NONE']:
        sdf = df[df['source_token'] == st]
        if len(sdf) > 0:
            print(f"  {st} timelimit_sec: min={sdf['timelimit_sec'].min():.0f}, max={sdf['timelimit_sec'].max():.0f}")
    
    # Data cleaning
    print("\n[clean] Filtering invalid data...")
    n_before = len(df)
    
    # Remove invalid runtimes
    df = df[df['runtime_sec'] > 0].copy()
    df = df[df['runtime_sec'] < 30 * 24 * 3600].copy()  # < 30 days
    
    # Remove invalid timelimits
    df = df[df['timelimit_sec'].notna() & (df['timelimit_sec'] > 0)].copy()
    df = df[df['timelimit_sec'] < 365 * 24 * 3600].copy()  # < 1 year
    
    # Remove invalid resources
    df = df[df['ncores'].notna() & (df['ncores'] > 0)].copy()
    df = df[df['nhosts'].notna() & (df['nhosts'] > 0)].copy()
    df = df[df['username'].notna()].copy()
    
    print(f"[clean] Removed {n_before - len(df):,} invalid jobs")
    print(f"[clean] After filtering: {len(df):,} jobs")
    
    for st in sorted(df['source_token'].unique()):
        n = (df['source_token'] == st).sum()
        users = df[df['source_token'] == st]['username'].nunique()
        print(f"       {st}: {n:,} jobs, {users:,} unique users")
    
    return df


def time_based_split(df: pd.DataFrame, test_frac: float = 0.2):
    """Time-based split."""
    yearmonths = sorted(df['yearmonth'].unique())
    n_test = max(1, int(len(yearmonths) * test_frac))
    cutoff = yearmonths[-(n_test)]
    
    train = df[df['yearmonth'] < cutoff].copy()
    test = df[df['yearmonth'] >= cutoff].copy()
    
    print(f"[split] Time: Train {len(train):,}, Test {len(test):,}, Cutoff: {cutoff}")
    return train, test


def user_aware_split(df: pd.DataFrame, test_frac: float = 0.2, seed: int = 42):
    """User-aware split."""
    np.random.seed(seed)
    users = df['username'].unique()
    np.random.shuffle(users)
    
    n_test = max(1, int(len(users) * test_frac))
    test_users = set(users[:n_test])
    
    test = df[df['username'].isin(test_users)].copy()
    train = df[~df['username'].isin(test_users)].copy()
    
    print(f"[split] User: Train {len(train):,} ({len(users)-n_test:,} users), "
          f"Test {len(test):,} ({n_test:,} users)")
    return train, test


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Evaluate predictions in log space."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    mdae = np.median(np.abs(y_true - y_pred))
    
    # Symmetric MAPE
    y_t = np.exp(y_true)
    y_p = np.exp(y_pred)
    smape = np.median(2 * np.abs(y_t - y_p) / (np.abs(y_t) + np.abs(y_p) + 1e-8) * 100)
    
    return {'r2': r2, 'mae_log': mae, 'mdae_log': mdae, 'smape': smape}


def train_command(args):
    """Run corrected user baseline experiment."""
    df = load_and_clean(args.input_dir, args.threads)
    
    results = []
    
    # Focus on Stampede for clean analysis
    for cluster in ['S', 'C', 'NONE']:
        cdf = df[df['source_token'] == cluster].copy()
        if len(cdf) < 10000:
            continue
        
        print(f"\n{'='*70}")
        print(f"CLUSTER: {cluster} ({len(cdf):,} jobs)")
        print('='*70)
        
        for split_name in ['time_based', 'user_aware']:
            print(f"\n--- {split_name} ---")
            
            if split_name == 'time_based':
                train_df, test_df = time_based_split(cdf)
            else:
                train_df, test_df = user_aware_split(cdf)
            
            if len(train_df) < 1000 or len(test_df) < 1000:
                continue
            
            y_train = np.log(train_df['runtime_sec'].values)
            y_test = np.log(test_df['runtime_sec'].values)
            
            # Baselines
            # 1. Global median
            pred = np.full_like(y_test, np.median(y_train))
            m = evaluate(y_test, pred)
            m.update({'variant': 'global_median', 'model': 'baseline', 
                     'cluster': cluster, 'split': split_name})
            results.append(m)
            print(f"  global_median:      R²={m['r2']:.4f}, sMAPE={m['smape']:.1f}%")
            
            # 2. User median
            user_med = train_df.groupby('username').apply(
                lambda g: np.median(np.log(g['runtime_sec']))
            ).to_dict()
            fallback = np.median(y_train)
            pred = np.array([user_med.get(u, fallback) for u in test_df['username']])
            m = evaluate(y_test, pred)
            m.update({'variant': 'user_median', 'model': 'baseline',
                     'cluster': cluster, 'split': split_name})
            results.append(m)
            print(f"  user_median:        R²={m['r2']:.4f}, sMAPE={m['smape']:.1f}%")
            
            # Model variants - FIXED: explicit checks
            def make_X(data, include_timelimit=False, include_user=False, user_enc=None):
                X = np.column_stack([
                    np.log1p(data['ncores'].values),
                    np.log1p(data['nhosts'].values)
                ])
                if include_timelimit:
                    X = np.column_stack([X, np.log1p(data['timelimit_sec'].values)])
                if include_user:
                    if user_enc is None:
                        user_enc = LabelEncoder()
                        uids = user_enc.fit_transform(data['username'])
                    else:
                        known = set(user_enc.classes_)
                        safe = data['username'].apply(lambda x: x if x in known else '__UNK__')
                        if '__UNK__' not in known:
                            user_enc.classes_ = np.append(user_enc.classes_, '__UNK__')
                        uids = user_enc.transform(safe)
                    X = np.column_stack([X, uids])
                return X, user_enc
            
            variants = [
                ('resources_only', False, False),
                ('with_timelimit', True, False),
                ('with_user', False, True),
                ('full', True, True),
            ]
            
            for name, use_tl, use_user in variants:
                X_train, enc = make_X(train_df, use_tl, use_user)
                X_test, _ = make_X(test_df, use_tl, use_user, enc)
                
                model = XGBRegressor(
                    n_estimators=100, max_depth=6, learning_rate=0.1,
                    subsample=0.8, colsample_bytree=0.8,
                    n_jobs=-1, random_state=42, verbosity=0
                )
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                
                m = evaluate(y_test, pred)
                m.update({'variant': name, 'model': 'xgboost',
                         'cluster': cluster, 'split': split_name,
                         'n_features': X_train.shape[1]})
                results.append(m)
                print(f"  {name:18s}: R²={m['r2']:.4f}, sMAPE={m['smape']:.1f}% (features={X_train.shape[1]})")
    
    # Save
    results_df = pd.DataFrame(results)
    out_path = Path(args.out_dir) / 'user_baseline_corrected.csv'
    results_df.to_csv(out_path, index=False)
    print(f"\n[save] {out_path}")
    
    # Summary
    print("\n" + "="*70)
    print("LEAKAGE QUANTIFICATION")
    print("="*70)
    
    for cluster in ['S', 'C', 'NONE']:
        time_df = results_df[(results_df['cluster'] == cluster) & 
                            (results_df['split'] == 'time_based') &
                            (results_df['variant'] == 'with_timelimit')]
        user_df = results_df[(results_df['cluster'] == cluster) & 
                            (results_df['split'] == 'user_aware') &
                            (results_df['variant'] == 'with_timelimit')]
        
        if len(time_df) > 0 and len(user_df) > 0:
            delta = time_df['r2'].values[0] - user_df['r2'].values[0]
            print(f"  {cluster}: Δ R² = {delta:+.4f} (time={time_df['r2'].values[0]:.4f}, user={user_df['r2'].values[0]:.4f})")
    
    print("\n[done] Corrected experiment complete!")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    p = subparsers.add_parser('train')
    p.add_argument('--input-dir', required=True)
    p.add_argument('--out-dir', required=True)
    p.add_argument('--threads', type=int, default=8)
    p.set_defaults(func=train_command)
    
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == '__main__':
    main()
