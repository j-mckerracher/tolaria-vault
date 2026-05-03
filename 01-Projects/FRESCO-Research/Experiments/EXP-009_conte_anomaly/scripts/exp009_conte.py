#!/usr/bin/env python3
"""
EXP-009: Conte Anomaly Resolution
=================================
Investigate why Conte performance is anomalous.

Hypotheses:
H1 Under-specification: Conte has near-constant resources; training on NONE learns slopes that help.
H2 Non-stationarity: Conte time split is harsh/drifting; random split changes results.

Conditions:
1. C (Time Split) -> C (Time Split) [Baseline]
2. C (Random Split) -> C (Random Split) [Test H2]
3. NONE (Time Split) -> C (Time Split) [Test H1 - Full Transfer]
4. NONE (Constrained) -> C (Time Split) [Test H1 - Constrained Transfer]
   - Constrained: ncores=1 & nhosts=1
"""
from __future__ import annotations

import argparse
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor


def load_and_clean(input_dir: str, threads: int = 8) -> pd.DataFrame:
    """Load data with timelimit normalization."""
    con = duckdb.connect()
    con.execute(f"SET threads TO {threads}")
    con.execute("SET memory_limit = '48GB'")
    
    # Same query as EXP-007
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
    WHERE cluster IN ('C', 'NONE')
    """
    
    print(f"[load] Loading data (C and NONE only)...")
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


def make_features(df: pd.DataFrame) -> np.ndarray:
    """Create feature matrix."""
    X = np.column_stack([
        np.log1p(df['ncores'].values),
        np.log1p(df['nhosts'].values),
        np.log1p(df['timelimit_sec'].values)
    ])
    return X


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Evaluate in log space."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    
    # sMAPE
    y_t = np.exp(y_true)
    y_p = np.exp(y_pred)
    smape = np.median(2 * np.abs(y_t - y_p) / (np.abs(y_t) + np.abs(y_p) + 1e-8) * 100)
    
    return {'r2': r2, 'mae_log': mae, 'smape': smape}


def train_model(train_df):
    X = make_features(train_df)
    y = np.log(train_df['runtime_sec'].values)
    
    model = XGBRegressor(
        n_estimators=100, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8,
        n_jobs=-1, random_state=42, verbosity=0
    )
    model.fit(X, y)
    return model


def run_experiment(args):
    df = load_and_clean(args.input_dir, args.threads)
    results = []
    
    # 1. Prepare Data Splits
    print("\n[setup] Preparing splits...")
    
    # Conte Data
    df_c = df[df['cluster'] == 'C']
    c_train_time, c_test_time, c_cutoff = time_split(df_c)
    c_train_rand, c_test_rand = train_test_split(df_c, test_size=0.2, random_state=42)
    
    print(f"  Conte Time Split: Train={len(c_train_time):,}, Test={len(c_test_time):,} (Cutoff: {c_cutoff})")
    print(f"  Conte Random Split: Train={len(c_train_rand):,}, Test={len(c_test_rand):,}")

    # NONE Data (for transfer)
    df_none = df[df['cluster'] == 'NONE']
    none_train_time, _, _ = time_split(df_none) # We only need train for transfer
    
    # Constrained NONE (ncores=1, nhosts=1)
    none_train_const = none_train_time[
        (none_train_time['ncores'] == 1) & (none_train_time['nhosts'] == 1)
    ].copy()
    
    print(f"  NONE Time Split (Train): {len(none_train_time):,}")
    print(f"  NONE Constrained (Train): {len(none_train_const):,}")

    # 2. Run Conditions
    
    # Condition A: C (Time) -> C (Time) [Baseline]
    print("\n[H2] Testing Condition A (Baseline): C Time -> C Time")
    model_c_time = train_model(c_train_time)
    y_true = np.log(c_test_time['runtime_sec'].values)
    y_pred = model_c_time.predict(make_features(c_test_time))
    res_a = evaluate(y_true, y_pred)
    res_a.update({'condition': 'A_Baseline', 'train': 'C_Time', 'test': 'C_Time'})
    results.append(res_a)
    print(f"  R²={res_a['r2']:.4f}, sMAPE={res_a['smape']:.1f}%")

    # Condition B: C (Random) -> C (Random) [H2 Test]
    print("\n[H2] Testing Condition B (Random): C Random -> C Random")
    model_c_rand = train_model(c_train_rand)
    y_true = np.log(c_test_rand['runtime_sec'].values)
    y_pred = model_c_rand.predict(make_features(c_test_rand))
    res_b = evaluate(y_true, y_pred)
    res_b.update({'condition': 'B_Random', 'train': 'C_Rand', 'test': 'C_Rand'})
    results.append(res_b)
    print(f"  R²={res_b['r2']:.4f}, sMAPE={res_b['smape']:.1f}%")

    # Condition C: NONE (Full) -> C (Time) [H1 Test]
    print("\n[H1] Testing Condition C (Transfer Full): NONE Full -> C Time")
    model_none_full = train_model(none_train_time)
    y_true = np.log(c_test_time['runtime_sec'].values)
    y_pred = model_none_full.predict(make_features(c_test_time))
    res_c = evaluate(y_true, y_pred)
    res_c.update({'condition': 'C_Transfer_Full', 'train': 'NONE_Full', 'test': 'C_Time'})
    results.append(res_c)
    print(f"  R²={res_c['r2']:.4f}, sMAPE={res_c['smape']:.1f}%")

    # Condition D: NONE (Constrained) -> C (Time) [H1 Control]
    print("\n[H1] Testing Condition D (Transfer Constrained): NONE Constrained -> C Time")
    model_none_const = train_model(none_train_const)
    y_true = np.log(c_test_time['runtime_sec'].values)
    y_pred = model_none_const.predict(make_features(c_test_time))
    res_d = evaluate(y_true, y_pred)
    res_d.update({'condition': 'D_Transfer_Const', 'train': 'NONE_Const', 'test': 'C_Time'})
    results.append(res_d)
    print(f"  R²={res_d['r2']:.4f}, sMAPE={res_d['smape']:.1f}%")

    # 3. Interpret Results
    print("\n" + "="*70)
    print("CONTE ANOMALY ANALYSIS")
    print("="*70)
    
    # H2 Analysis
    gap_h2 = res_b['r2'] - res_a['r2']
    print(f"\nH2 (Non-stationarity):")
    print(f"  Baseline (Time): R²={res_a['r2']:.4f}")
    print(f"  Random Split:    R²={res_b['r2']:.4f}")
    print(f"  Gap: {gap_h2:+.4f}")
    if gap_h2 > 0.1:
        print("  => STRONG EVIDENCE for H2 (Time split is much harder than random)")
    elif gap_h2 > 0.05:
        print("  => WEAK EVIDENCE for H2")
    else:
        print("  => NO EVIDENCE for H2")

    # H1 Analysis
    gap_transfer = res_c['r2'] - res_a['r2']
    gap_slope = res_c['r2'] - res_d['r2']
    
    print(f"\nH1 (Under-specification):")
    print(f"  Baseline (C->C):       R²={res_a['r2']:.4f}")
    print(f"  Transfer (NONE->C):    R²={res_c['r2']:.4f} (Gap: {gap_transfer:+.4f})")
    print(f"  Constrained (NONE*->C): R²={res_d['r2']:.4f} (Slope Benefit: {gap_slope:+.4f})")
    
    if gap_transfer > 0 and gap_slope > 0.05:
        print("  => STRONG EVIDENCE for H1 (Training on varied data improves C prediction)")
    elif gap_transfer > 0:
        print("  => WEAK EVIDENCE for H1 (Transfer helps, but maybe not just due to slope)")
    else:
        print("  => NO EVIDENCE for H1")

    # Save
    out_path = Path(args.out_dir) / 'conte_anomaly_results.csv'
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"\n[save] {out_path}")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    p = subparsers.add_parser('run')
    p.add_argument('--input-dir', required=True)
    p.add_argument('--out-dir', required=True)
    p.add_argument('--threads', type=int, default=8)
    p.set_defaults(func=run_experiment)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
