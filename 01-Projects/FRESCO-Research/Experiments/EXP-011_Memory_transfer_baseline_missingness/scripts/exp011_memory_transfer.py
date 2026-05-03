#!/usr/bin/env python3
"""EXP-011: Memory transfer baseline + missingness analysis.

Goals (PATH-C RQ-2B):
1) Compute job-level peak memory labels from FRESCO raw snapshots.
2) Run within-site + cross-site transfer experiments (like EXP-007/008).
3) Quantify memory metric missingness/coverage per cluster.
4) Provide bootstrap confidence intervals for transfer metrics.

Uses simple features (no runtime): log1p(ncores), log1p(nhosts), log1p(timelimit_sec).
Label: log(peak_memused) where peak_memused = max(value_memused) per jid.
Restricts to jobs with at least 1 memory sample.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor


CLUSTERS = ["S", "C", "NONE"]


def _smape_median(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> float:
    y_t = np.exp(y_true_log)
    y_p = np.exp(y_pred_log)
    return float(
        np.median(2 * np.abs(y_t - y_p) / (np.abs(y_t) + np.abs(y_p) + 1e-8) * 100)
    )


def evaluate(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> dict:
    return {
        "r2": float(r2_score(y_true_log, y_pred_log)),
        "mae_log": float(mean_absolute_error(y_true_log, y_pred_log)),
        "mdae_log": float(np.median(np.abs(y_true_log - y_pred_log))),
        "smape": _smape_median(y_true_log, y_pred_log),
    }


def load_and_clean(input_dir: str, threads: int = 8) -> tuple[pd.DataFrame, dict[str, float]]:
    """Load FRESCO chunks, compute job-level peak memory, and report missingness.

    Returns:
        df_model: job-level data filtered to jobs with ≥1 memory sample
        coverage_by_cluster: fraction of jobs with ≥1 memory sample (pre-filter)
    """
    # Use data depot for temp files to avoid disk quota issues
    temp_db_dir = "/depot/sbagchi/data/josh/FRESCO-Research/Experiments/EXP-011_Memory_transfer_baseline_missingness/temp"
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

    print("[load] Loading data with memory metrics...")
    df = con.execute(sql).fetchdf()
    print(f"[load] Raw: {len(df):,} jobs")

    # Report missingness before filtering (coverage computed on the full job set).
    total = len(df)
    has_mem = (df["mem_sample_count"] > 0).sum()
    print(
        f"[missingness] Jobs with ≥1 memory sample: {has_mem:,} / {total:,} ({100 * has_mem / total:.1f}%)"
    )

    coverage_by_cluster: dict[str, float] = {}
    for c in sorted(df["cluster"].unique()):
        c_total = int((df["cluster"] == c).sum())
        c_has = int(((df["cluster"] == c) & (df["mem_sample_count"] > 0)).sum())
        cov = (c_has / c_total) if c_total > 0 else float("nan")
        coverage_by_cluster[c] = float(cov)
        print(f"              {c}: {c_has:,} / {c_total:,} ({100 * cov:.1f}%)")

    # Filter to jobs with at least 1 memory sample for modeling.
    df = df[df["mem_sample_count"] > 0].copy()
    df = df[df["peak_memused"].notna() & (df["peak_memused"] > 0)].copy()
    print(f"[filter] After requiring ≥1 mem sample and peak_memused > 0: {len(df):,} jobs")

    # Standard filters similar to exp008
    df = df[df["runtime_sec"] > 0].copy()
    df = df[df["runtime_sec"] < 30 * 24 * 3600].copy()  # < 30 days
    df = df[df["timelimit_sec"].notna() & (df["timelimit_sec"] > 0)].copy()
    df = df[df["timelimit_sec"] < 365 * 24 * 3600].copy()
    df = df[df["ncores"].notna() & (df["ncores"] > 0)].copy()
    df = df[df["nhosts"].notna() & (df["nhosts"] > 0)].copy()

    print(f"[clean] After standard filters: {len(df):,} jobs")
    for c in sorted(df["cluster"].unique()):
        print(f"        {c}: {(df['cluster'] == c).sum():,} jobs")

    return df, coverage_by_cluster


def time_split(df: pd.DataFrame, test_frac: float = 0.2):
    yearmonths = sorted(df["yearmonth"].unique())
    n_test = max(1, int(len(yearmonths) * test_frac))
    cutoff = yearmonths[-n_test]
    train = df[df["yearmonth"] < cutoff].copy()
    test = df[df["yearmonth"] >= cutoff].copy()
    return train, test, cutoff


def make_features(df: pd.DataFrame, cluster_conditioning: bool) -> np.ndarray:
    """Simple features: log1p(ncores), log1p(nhosts), log1p(timelimit_sec).
    
    No runtime features since we're predicting memory (pre-job info only).
    """
    X = np.column_stack(
        [
            np.log1p(df["ncores"].values),
            np.log1p(df["nhosts"].values),
            np.log1p(df["timelimit_sec"].values),
        ]
    )

    if cluster_conditioning:
        # One-hot cluster for pooled training.
        cl = df["cluster"].values
        onehot = np.column_stack([(cl == c).astype(np.float32) for c in CLUSTERS])
        X = np.column_stack([X, onehot])

    return X


@dataclass
class TrainSpec:
    name: str
    train_clusters: tuple[str, ...]
    pooled: bool
    cluster_conditioning: bool


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


def _bootstrap_ci(rng: np.random.Generator, y_true: np.ndarray, y_pred: np.ndarray, n_boot: int) -> dict:
    n = len(y_true)
    idx = np.arange(n)

    r2s = []
    maes = []
    mdaes = []
    smapes = []

    for _ in range(n_boot):
        b = rng.choice(idx, size=n, replace=True)
        m = evaluate(y_true[b], y_pred[b])
        r2s.append(m["r2"])
        maes.append(m["mae_log"])
        mdaes.append(m["mdae_log"])
        smapes.append(m["smape"])

    def ci(x):
        lo, hi = np.percentile(x, [2.5, 97.5])
        return float(lo), float(hi)

    return {
        "r2_ci_low": ci(r2s)[0],
        "r2_ci_high": ci(r2s)[1],
        "mae_log_ci_low": ci(maes)[0],
        "mae_log_ci_high": ci(maes)[1],
        "mdae_log_ci_low": ci(mdaes)[0],
        "mdae_log_ci_high": ci(mdaes)[1],
        "smape_ci_low": ci(smapes)[0],
        "smape_ci_high": ci(smapes)[1],
    }


def _shift_metrics(train_X: np.ndarray, test_X: np.ndarray) -> dict:
    # Simple, reproducible shift metrics (same as exp008).
    # 1) Mean absolute standardized mean difference (SMD)
    mu_tr = train_X.mean(axis=0)
    mu_te = test_X.mean(axis=0)
    sd_tr = train_X.std(axis=0) + 1e-8
    smd = np.abs(mu_tr - mu_te) / sd_tr

    # 2) Approximate Jensen-Shannon divergence on each feature histogram
    jsds = []
    for j in range(train_X.shape[1]):
        x = np.concatenate([train_X[:, j], test_X[:, j]])
        lo, hi = np.quantile(x, [0.001, 0.999])
        if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
            continue
        bins = np.linspace(lo, hi, 51)
        p, _ = np.histogram(train_X[:, j], bins=bins, density=True)
        q, _ = np.histogram(test_X[:, j], bins=bins, density=True)
        p = p + 1e-12
        q = q + 1e-12
        p = p / p.sum()
        q = q / q.sum()
        m = 0.5 * (p + q)
        jsd = 0.5 * (np.sum(p * np.log(p / m)) + np.sum(q * np.log(q / m)))
        jsds.append(float(jsd))

    return {
        "shift_smd_mean": float(np.mean(smd)),
        "shift_smd_max": float(np.max(smd)),
        "shift_jsd_mean": float(np.mean(jsds)) if jsds else np.nan,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--test-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-boot", type=int, default=200)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df, coverage_by_cluster = load_and_clean(args.input_dir, threads=args.threads)

    # Prepare per-cluster splits.
    cluster_data = {}
    for c in CLUSTERS:
        cdf = df[df["cluster"] == c]
        if len(cdf) < 2000:  # Need enough data for memory analysis
            print(f"[skip] {c}: Only {len(cdf):,} jobs, skipping (need ≥2000)")
            continue
        train, test, cutoff = time_split(cdf, test_frac=args.test_frac)
        if len(train) < 1000 or len(test) < 1000:
            print(f"[skip] {c}: Train {len(train):,}, Test {len(test):,} (need ≥1000 each)")
            continue

        cov = coverage_by_cluster.get(c, float("nan"))
        cluster_data[c] = {
            "train": train,
            "test": test,
            "cutoff": cutoff,
            "mem_coverage": cov,
        }
        print(f"[split] {c}: Train {len(train):,}, Test {len(test):,}, Cutoff: {cutoff}")
        print(f"        Memory coverage (overall): {100*cov:.1f}%")

    # Specs: similar to exp008 (single-cluster + pooled models).
    specs = [
        TrainSpec("single", ("S",), pooled=False, cluster_conditioning=False),
        TrainSpec("single", ("C",), pooled=False, cluster_conditioning=False),
        TrainSpec("single", ("NONE",), pooled=False, cluster_conditioning=False),
        TrainSpec("pooled_all_no_cluster", tuple(CLUSTERS), pooled=True, cluster_conditioning=False),
        TrainSpec("pooled_all_with_cluster", tuple(CLUSTERS), pooled=True, cluster_conditioning=True),
    ]

    rows = []
    rng = np.random.default_rng(args.seed)

    for spec in specs:
        # Skip if any train cluster is missing
        if not all(c in cluster_data for c in spec.train_clusters):
            print(f"[skip] {spec.name} clusters={spec.train_clusters}: missing data")
            continue

        train_df = pd.concat([cluster_data[c]["train"] for c in spec.train_clusters], ignore_index=True)
        X_train = make_features(train_df, cluster_conditioning=spec.cluster_conditioning)
        y_train = np.log(train_df["peak_memused"].values)

        model = _fit_xgb(X_train, y_train, seed=args.seed)
        print(f"[train] {spec.name} clusters={spec.train_clusters} conditioning={spec.cluster_conditioning}")

        for test_cluster in CLUSTERS:
            if test_cluster not in cluster_data:
                continue

            test_df = cluster_data[test_cluster]["test"]
            X_test = make_features(test_df, cluster_conditioning=spec.cluster_conditioning)
            y_test = np.log(test_df["peak_memused"].values)

            y_pred = model.predict(X_test)

            m = evaluate(y_test, y_pred)
            ci = _bootstrap_ci(rng, y_test, y_pred, n_boot=args.n_boot)
            shift = _shift_metrics(X_train, X_test)

            rows.append(
                {
                    "train_spec": spec.name,
                    "train_clusters": "+".join(spec.train_clusters),
                    "cluster_conditioning": spec.cluster_conditioning,
                    "test_cluster": test_cluster,
                    "n_train": len(train_df),
                    "n_test": len(test_df),
                    "train_mem_coverage": float(
                        np.mean([cluster_data[c]["mem_coverage"] for c in spec.train_clusters])
                    ),
                    "test_mem_coverage": cluster_data[test_cluster]["mem_coverage"],
                    **m,
                    **ci,
                    **shift,
                }
            )

    results = pd.DataFrame(rows)
    out_csv = out_dir / "exp011_results.csv"
    results.to_csv(out_csv, index=False)
    print(f"[save] {out_csv}")


if __name__ == "__main__":
    main()
