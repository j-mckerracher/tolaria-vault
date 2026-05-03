#!/usr/bin/env python3
"""EXP-009: Conte anomaly resolution.

Goal: resolve the "Conte anomaly" (NONE→C outperforming C→C) by testing two explanations:

H2 (Non-stationarity): Conte's time-based split is unusually harsh due to drift.
  Evidence: B (C→C random split) >> A (C→C time split)

H1 (Under-specification): Conte's resource requests are too low-variance to learn slopes.
  Evidence: C (NONE→C) > D (NONE filtered to ncores=1, nhosts=1) and C > A

This script mirrors EXP-007/008 in spirit:
- DuckDB read_parquet
- job-level (jid) aggregation across snapshots
- Stampede (S) timelimit normalization minutes→seconds
- runtime/timelimit/ncores/nhosts sanity filters

Outputs: a CSV with metrics + counts for each condition.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor


CLUSTER_CONTE = "C"
CLUSTER_NONE = "NONE"


def load_and_clean(input_dir: str, threads: int = 8) -> pd.DataFrame:
    """Load parquet shards, aggregate by jid, normalize timelimit for S, and filter."""

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
            MAX(cluster) AS cluster
        FROM raw
        GROUP BY jid
    )
    SELECT
        jid,
        CASE WHEN cluster = 'S' THEN timelimit_raw * 60.0 ELSE timelimit_raw END AS timelimit_sec,
        ncores,
        nhosts,
        cluster,
        EXTRACT(YEAR FROM start_time) * 100 + EXTRACT(MONTH FROM start_time) AS yearmonth,
        EXTRACT(EPOCH FROM (end_time - start_time)) AS runtime_sec
    FROM agg
    """

    print("[load] Loading data...")
    df = con.execute(sql).fetchdf()
    print(f"[load] Raw: {len(df):,} jobs")

    # Clean: match EXP-007/008 spirit.
    df = df[df["runtime_sec"] > 0].copy()
    df = df[df["runtime_sec"] < 30 * 24 * 3600].copy()  # < 30 days

    df = df[df["timelimit_sec"].notna() & (df["timelimit_sec"] > 0)].copy()
    df = df[df["timelimit_sec"] < 365 * 24 * 3600].copy()

    df = df[df["ncores"].notna() & (df["ncores"] > 0)].copy()
    df = df[df["nhosts"].notna() & (df["nhosts"] > 0)].copy()

    print(f"[clean] After: {len(df):,} jobs")
    for c in sorted(df["cluster"].unique()):
        print(f"       {c}: {(df['cluster'] == c).sum():,} jobs")

    return df


def time_split(df: pd.DataFrame, test_frac: float = 0.2):
    yearmonths = sorted(df["yearmonth"].unique())
    n_test = max(1, int(len(yearmonths) * test_frac))
    cutoff = yearmonths[-n_test]
    train = df[df["yearmonth"] < cutoff].copy()
    test = df[df["yearmonth"] >= cutoff].copy()
    return train, test, cutoff


def _random_split_with_sizes(df: pd.DataFrame, n_train: int, n_test: int, seed: int):
    if n_train + n_test > len(df):
        raise ValueError(f"Need {n_train + n_test} rows but only have {len(df)}")

    rng = np.random.default_rng(seed)
    idx = np.arange(len(df))
    rng.shuffle(idx)
    tr_idx = idx[:n_train]
    te_idx = idx[n_train : n_train + n_test]
    return df.iloc[tr_idx].copy(), df.iloc[te_idx].copy()


def make_features(df: pd.DataFrame, include_timelimit: bool) -> np.ndarray:
    X = np.column_stack([
        np.log1p(df["ncores"].values),
        np.log1p(df["nhosts"].values),
    ])
    if include_timelimit:
        X = np.column_stack([X, np.log1p(df["timelimit_sec"].values)])
    return X


def evaluate(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> dict:
    y_t = np.exp(y_true_log)
    y_p = np.exp(y_pred_log)
    smape = float(np.median(2 * np.abs(y_t - y_p) / (np.abs(y_t) + np.abs(y_p) + 1e-8) * 100))
    return {
        "r2": float(r2_score(y_true_log, y_pred_log)),
        "mae_log": float(mean_absolute_error(y_true_log, y_pred_log)),
        "mdae_log": float(np.median(np.abs(y_true_log - y_pred_log))),
        "smape": smape,
    }


def _fit_xgb(X: np.ndarray, y: np.ndarray, seed: int) -> XGBRegressor:
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=seed,
        verbosity=0,
    )
    model.fit(X, y)
    return model


def _run_condition(
    *,
    variant: str,
    condition: str,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    include_timelimit: bool,
    seed: int,
    notes: str = "",
) -> dict:
    X_tr = make_features(train_df, include_timelimit=include_timelimit)
    y_tr = np.log(train_df["runtime_sec"].values)

    X_te = make_features(test_df, include_timelimit=include_timelimit)
    y_te = np.log(test_df["runtime_sec"].values)

    model = _fit_xgb(X_tr, y_tr, seed=seed)
    y_pred = model.predict(X_te)

    out = evaluate(y_te, y_pred)
    out.update(
        {
            "variant": variant,
            "condition": condition,
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
            "notes": notes,
        }
    )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--test-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--also-no-timelimit", action="store_true")
    ap.add_argument("--h2-delta", type=float, default=0.10, help="Threshold for 'B >> A' in R2")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_and_clean(args.input_dir, threads=args.threads)

    # Restrict to cases where test is Conte only.
    df_c = df[df["cluster"] == CLUSTER_CONTE].copy()
    df_n = df[df["cluster"] == CLUSTER_NONE].copy()

    print(f"[subset] Conte jobs: {len(df_c):,}")
    print(f"[subset] NONE jobs:  {len(df_n):,}")

    c_train_time, c_test_time, c_cutoff = time_split(df_c, test_frac=args.test_frac)
    n_train_a = len(c_train_time)
    n_test_a = len(c_test_time)

    c_train_rand, c_test_rand = _random_split_with_sizes(df_c, n_train=n_train_a, n_test=n_test_a, seed=args.seed)

    n_train_time, _, n_cutoff = time_split(df_n, test_frac=args.test_frac)  # transfer uses NONE train only
    n_train_const = n_train_time[(n_train_time["ncores"] == 1) & (n_train_time["nhosts"] == 1)].copy()

    print("\n[splits]")
    print(f"  Conte time split:   train={n_train_a:,} test={n_test_a:,} cutoff={c_cutoff}")
    print(f"  Conte random split: train={len(c_train_rand):,} test={len(c_test_rand):,} (matched to time sizes)")
    print(f"  NONE time split:    train={len(n_train_time):,} cutoff={n_cutoff}")
    print(f"  NONE constrained:   train={len(n_train_const):,} (ncores=1, nhosts=1)")

    def run_variant(include_timelimit: bool) -> list[dict]:
        variant = "with_timelimit" if include_timelimit else "no_timelimit"
        results: list[dict] = []

        results.append(
            _run_condition(
                variant=variant,
                condition="A_C_to_C_time",
                train_df=c_train_time,
                test_df=c_test_time,
                include_timelimit=include_timelimit,
                seed=args.seed,
                notes=f"Conte cutoff={c_cutoff}",
            )
        )

        results.append(
            _run_condition(
                variant=variant,
                condition="B_C_to_C_random",
                train_df=c_train_rand,
                test_df=c_test_rand,
                include_timelimit=include_timelimit,
                seed=args.seed,
                notes="Random split; train size matched to A",
            )
        )

        results.append(
            _run_condition(
                variant=variant,
                condition="C_NONE_to_C_transfer",
                train_df=n_train_time,
                test_df=c_test_time,
                include_timelimit=include_timelimit,
                seed=args.seed,
                notes=f"NONE cutoff={n_cutoff}; test is Conte time-test",
            )
        )

        if len(n_train_const) > 0:
            results.append(
                _run_condition(
                    variant=variant,
                    condition="D_NONE_to_C_transfer_supportmatch",
                    train_df=n_train_const,
                    test_df=c_test_time,
                    include_timelimit=include_timelimit,
                    seed=args.seed,
                    notes="NONE train filtered to ncores=1 & nhosts=1; test is Conte time-test",
                )
            )
        else:
            results.append(
                {
                    "variant": variant,
                    "condition": "D_NONE_to_C_transfer_supportmatch",
                    "r2": np.nan,
                    "mae_log": np.nan,
                    "mdae_log": np.nan,
                    "smape": np.nan,
                    "n_train": int(len(n_train_const)),
                    "n_test": int(len(c_test_time)),
                    "notes": "No rows after ncores=1 & nhosts=1 filter",
                }
            )

        return results

    results_all: list[dict] = []
    results_all.extend(run_variant(include_timelimit=True))
    if args.also_no_timelimit:
        results_all.extend(run_variant(include_timelimit=False))

    res_df = pd.DataFrame(results_all)
    out_csv = out_dir / "exp009_conte_anomaly_results.csv"
    res_df.to_csv(out_csv, index=False)
    print(f"\n[save] {out_csv}")

    # Hypothesis readout (based on with-timelimit results).
    r2 = {r["condition"]: float(r["r2"]) for r in results_all if r["variant"] == "with_timelimit"}

    r2_a = r2.get("A_C_to_C_time", float("nan"))
    r2_b = r2.get("B_C_to_C_random", float("nan"))
    r2_c = r2.get("C_NONE_to_C_transfer", float("nan"))
    r2_d = r2.get("D_NONE_to_C_transfer_supportmatch", float("nan"))

    print("\n" + "=" * 78)
    print("HYPOTHESIS READOUT (with timelimit)")
    print("=" * 78)

    delta_ba = r2_b - r2_a
    h2_supported = bool(np.isfinite(delta_ba) and (delta_ba >= args.h2_delta))
    print("H2 (non-stationarity) supported if B >> A")
    print(f"  A (C→C time):   R2={r2_a:.4f}")
    print(f"  B (C→C random): R2={r2_b:.4f}")
    print(f"  B-A: {delta_ba:+.4f}  (threshold={args.h2_delta:.2f})")
    print(f"  => H2_supported={h2_supported}")

    h1_supported = bool(np.isfinite(r2_c) and np.isfinite(r2_d) and np.isfinite(r2_a) and (r2_c > r2_d) and (r2_c > r2_a))
    print("\nH1 (under-specification) supported if C > D and C > A")
    print(f"  A (C→C time):      R2={r2_a:.4f}")
    print(f"  C (NONE→C):        R2={r2_c:.4f}")
    print(f"  D (NONE*→C match): R2={r2_d:.4f}")
    if np.isfinite(r2_c) and np.isfinite(r2_a):
        print(f"  C-A: {r2_c - r2_a:+.4f}")
    if np.isfinite(r2_c) and np.isfinite(r2_d):
        print(f"  C-D: {r2_c - r2_d:+.4f}")
    print(f"  => H1_supported={h1_supported}")


if __name__ == "__main__":
    main()
