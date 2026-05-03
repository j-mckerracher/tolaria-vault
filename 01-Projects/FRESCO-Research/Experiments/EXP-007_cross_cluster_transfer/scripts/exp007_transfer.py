#!/usr/bin/env python3
"""
EXP-007: Cross-Cluster Transfer
================================
Test whether models trained on one cluster generalize to another.

Key questions:
1. Can Stampede model predict Conte runtimes?
2. Can Conte model predict Stampede runtimes?
3. Is transfer symmetric or asymmetric?
4. Does timelimit help or hurt transfer?

This addresses PATH-C research questions about multi-site generalization.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from itertools import product

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor


def load_and_clean(input_dir: str, threads: int = 8) -> pd.DataFrame:
    """Load data with timelimit normalization."""
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
            END AS cluster
        FROM read_parquet('{input_dir}/**/*.parquet', filename=true)
        WHERE start_time IS NOT NULL AND end_time IS NOT NULL
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
            MAX(cluster) AS cluster
        FROM raw
        GROUP BY jid
    )
    SELECT
        jid,
        -- Normalize timelimit to seconds (S is in minutes)
        CASE WHEN cluster = 'S' THEN timelimit_raw * 60.0 ELSE timelimit_raw END AS timelimit_sec,
        ncores,
        nhosts,
        cluster,
        EXTRACT(YEAR FROM start_time) * 100 + EXTRACT(MONTH FROM start_time) AS yearmonth,
        EXTRACT(EPOCH FROM (end_time - start_time)) AS runtime_sec
    FROM agg
    """
    
    print(f"[load] Loading data...")
    df = con.execute(sql).fetchdf()
    print(f"[load] Raw: {len(df):,} jobs")
    
    # Clean
    df = df[df['runtime_sec'] > 0].copy()
    df = df[df['runtime_sec'] < 30 * 24 * 3600].copy()  # < 30 days
    df = df[df['timelimit_sec'].notna() & (df['timelimit_sec'] > 0)].copy()
    df = df[df['timelimit_sec'] < 365 * 24 * 3600].copy()
    df = df[df['ncores'].notna() & (df['ncores'] > 0)].copy()
    df = df[df['nhosts'].notna() & (df['nhosts'] > 0)].copy()
    
    print(f"[clean] After: {len(df):,} jobs")
    for c in sorted(df['cluster'].unique()):
        print(f"       {c}: {(df['cluster'] == c).sum():,} jobs")
    
    return df


def time_split(df: pd.DataFrame, test_frac: float = 0.2):
    """Time-based split within a cluster."""
    yearmonths = sorted(df['yearmonth'].unique())
    n_test = max(1, int(len(yearmonths) * test_frac))
    cutoff = yearmonths[-n_test]
    
    train = df[df['yearmonth'] < cutoff].copy()
    test = df[df['yearmonth'] >= cutoff].copy()
    return train, test, cutoff


def make_features(df: pd.DataFrame, include_timelimit: bool = True) -> np.ndarray:
    """Create feature matrix."""
    X = np.column_stack([
        np.log1p(df['ncores'].values),
        np.log1p(df['nhosts'].values)
    ])
    if include_timelimit:
        X = np.column_stack([X, np.log1p(df['timelimit_sec'].values)])
    return X


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Evaluate in log space."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    mdae = np.median(np.abs(y_true - y_pred))
    
    # sMAPE
    y_t = np.exp(y_true)
    y_p = np.exp(y_pred)
    smape = np.median(2 * np.abs(y_t - y_p) / (np.abs(y_t) + np.abs(y_p) + 1e-8) * 100)
    
    return {'r2': r2, 'mae_log': mae, 'mdae_log': mdae, 'smape': smape}


def train_command(args):
    """Run cross-cluster transfer experiments."""
    df = load_and_clean(args.input_dir, args.threads)
    
    clusters = ['S', 'C', 'NONE']
    results = []
    
    # Split each cluster into train/test by time
    cluster_data = {}
    for c in clusters:
        cdf = df[df['cluster'] == c]
        if len(cdf) < 10000:
            continue
        train, test, cutoff = time_split(cdf)
        if len(train) < 1000 or len(test) < 1000:
            continue
        cluster_data[c] = {'train': train, 'test': test, 'cutoff': cutoff}
        print(f"[split] {c}: Train {len(train):,}, Test {len(test):,}, Cutoff: {cutoff}")
    
    # Train models on each cluster
    models = {}
    for c in cluster_data:
        train = cluster_data[c]['train']
        X = make_features(train, include_timelimit=True)
        y = np.log(train['runtime_sec'].values)
        
        model = XGBRegressor(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=42, verbosity=0
        )
        model.fit(X, y)
        models[c] = model
        print(f"[train] Trained model on {c}")
    
    # Test each model on each cluster's test set
    print("\n" + "="*70)
    print("TRANSFER MATRIX")
    print("="*70)
    
    for train_cluster in cluster_data:
        for test_cluster in cluster_data:
            test_df = cluster_data[test_cluster]['test']
            X_test = make_features(test_df, include_timelimit=True)
            y_test = np.log(test_df['runtime_sec'].values)
            
            # Predict
            y_pred = models[train_cluster].predict(X_test)
            
            # Evaluate
            m = evaluate(y_test, y_pred)
            m['train_cluster'] = train_cluster
            m['test_cluster'] = test_cluster
            m['n_train'] = len(cluster_data[train_cluster]['train'])
            m['n_test'] = len(test_df)
            m['is_transfer'] = train_cluster != test_cluster
            results.append(m)
            
            transfer_label = "TRANSFER" if train_cluster != test_cluster else "SAME"
            print(f"  Train: {train_cluster} -> Test: {test_cluster} ({transfer_label}): "
                  f"R²={m['r2']:.4f}, sMAPE={m['smape']:.1f}%")
    
    # Also test without timelimit
    print("\n" + "="*70)
    print("TRANSFER MATRIX (without timelimit)")
    print("="*70)
    
    models_no_tl = {}
    for c in cluster_data:
        train = cluster_data[c]['train']
        X = make_features(train, include_timelimit=False)
        y = np.log(train['runtime_sec'].values)
        
        model = XGBRegressor(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=42, verbosity=0
        )
        model.fit(X, y)
        models_no_tl[c] = model
    
    for train_cluster in cluster_data:
        for test_cluster in cluster_data:
            test_df = cluster_data[test_cluster]['test']
            X_test = make_features(test_df, include_timelimit=False)
            y_test = np.log(test_df['runtime_sec'].values)
            
            y_pred = models_no_tl[train_cluster].predict(X_test)
            
            m = evaluate(y_test, y_pred)
            m['train_cluster'] = train_cluster
            m['test_cluster'] = test_cluster
            m['n_train'] = len(cluster_data[train_cluster]['train'])
            m['n_test'] = len(test_df)
            m['is_transfer'] = train_cluster != test_cluster
            m['variant'] = 'no_timelimit'
            results.append(m)
            
            transfer_label = "TRANSFER" if train_cluster != test_cluster else "SAME"
            print(f"  Train: {train_cluster} -> Test: {test_cluster} ({transfer_label}): "
                  f"R²={m['r2']:.4f}, sMAPE={m['smape']:.1f}%")
    
    # Save results
    results_df = pd.DataFrame(results)
    out_path = Path(args.out_dir) / 'transfer_matrix.csv'
    results_df.to_csv(out_path, index=False)
    print(f"\n[save] {out_path}")
    
    # Summary
    print("\n" + "="*70)
    print("TRANSFER GAP ANALYSIS (with timelimit)")
    print("="*70)
    
    with_tl = [r for r in results if r.get('variant') != 'no_timelimit']
    
    for test_cluster in cluster_data:
        same = [r for r in with_tl if r['train_cluster'] == test_cluster and r['test_cluster'] == test_cluster]
        transfers = [r for r in with_tl if r['train_cluster'] != test_cluster and r['test_cluster'] == test_cluster]
        
        if same and transfers:
            same_r2 = same[0]['r2']
            best_transfer = max(transfers, key=lambda x: x['r2'])
            worst_transfer = min(transfers, key=lambda x: x['r2'])
            
            print(f"\nTest on {test_cluster}:")
            print(f"  Same-cluster: R²={same_r2:.4f}")
            print(f"  Best transfer ({best_transfer['train_cluster']}): R²={best_transfer['r2']:.4f} (Δ={best_transfer['r2'] - same_r2:+.4f})")
            print(f"  Worst transfer ({worst_transfer['train_cluster']}): R²={worst_transfer['r2']:.4f} (Δ={worst_transfer['r2'] - same_r2:+.4f})")
    
    print("\n[done] Cross-cluster transfer complete!")


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
