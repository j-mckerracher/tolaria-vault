#!/usr/bin/env python3
"""EXP-010: Few-shot calibration on target site.

We extend the EXP-007/008 runtime pipeline:
- Load job-level dataset via DuckDB read_parquet + jid aggregation.
- Time-split each cluster (last 20% yearmonths test).
- Train on a source dataset, then optionally add k target-train examples.

Output: results CSV with metrics + bootstrap CIs for each (condition, k).
"""

from __future__ import annotations

import argparse
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


def load_and_clean(input_dir: str, threads: int = 8) -> pd.DataFrame:
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

    df = df[df["runtime_sec"] > 0].copy()
    df = df[df["runtime_sec"] < 30 * 24 * 3600].copy()
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


def make_features(df: pd.DataFrame) -> np.ndarray:
    return np.column_stack(
        [
            np.log1p(df["ncores"].values),
            np.log1p(df["nhosts"].values),
            np.log1p(df["timelimit_sec"].values),
        ]
    )


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


@dataclass(frozen=True)
class Condition:
    name: str
    source: str
    target: str


def _run(
    *,
    rng: np.random.Generator,
    condition: Condition,
    k: int,
    source_train: pd.DataFrame,
    target_train: pd.DataFrame,
    target_test: pd.DataFrame,
    seed: int,
    n_boot: int,
) -> dict:
    if k == 0:
        train_df = source_train
        notes = "source_only"
    else:
        k_eff = min(k, len(target_train))
        idx = rng.choice(np.arange(len(target_train)), size=k_eff, replace=False)
        few = target_train.iloc[idx].copy()
        train_df = pd.concat([source_train, few], ignore_index=True)
        notes = f"source_plus_{k_eff}_target_train"

    X_tr = make_features(train_df)
    y_tr = np.log(train_df["runtime_sec"].values)

    X_te = make_features(target_test)
    y_te = np.log(target_test["runtime_sec"].values)

    model = _fit_xgb(X_tr, y_tr, seed=seed)
    y_pred = model.predict(X_te)

    out = evaluate(y_te, y_pred)
    out.update(_bootstrap_ci(rng, y_te, y_pred, n_boot=n_boot))
    out.update(
        {
            "condition": condition.name,
            "source": condition.source,
            "target": condition.target,
            "k": int(k),
            "n_train": int(len(train_df)),
            "n_test": int(len(target_test)),
            "notes": notes,
        }
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--test-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-boot", type=int, default=200)
    ap.add_argument(
        "--k-schedule",
        default="0,100,300,1000,3000,10000,30000,100000",
        help="Comma-separated k values.",
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_and_clean(args.input_dir, threads=args.threads)

    # Cluster-specific time splits.
    splits = {}
    for c in CLUSTERS:
        d = df[df["cluster"] == c].copy()
        tr, te, cutoff = time_split(d, test_frac=args.test_frac)
        splits[c] = (tr, te, cutoff)
        print(f"[split] {c}: train={len(tr):,} test={len(te):,} cutoff={cutoff}")

    k_vals = [int(x.strip()) for x in args.k_schedule.split(",") if x.strip()]

    conditions = [
        Condition(name="NONE_to_C", source="NONE", target="C"),
        Condition(name="S_to_C", source="S", target="C"),
    ]

    rng = np.random.default_rng(args.seed)

    rows: list[dict] = []
    for cond in conditions:
        source_train, _, _ = splits[cond.source]
        target_train, target_test, _ = splits[cond.target]

        for k in k_vals:
            rows.append(
                _run(
                    rng=rng,
                    condition=cond,
                    k=k,
                    source_train=source_train,
                    target_train=target_train,
                    target_test=target_test,
                    seed=args.seed,
                    n_boot=args.n_boot,
                )
            )
            print(f"[done] {cond.name} k={k} r2={rows[-1]['r2']:.4f}")

    res = pd.DataFrame(rows)
    res.to_csv(out_dir / "exp010_results.csv", index=False)

    # Compact table for paper drafts.
    tab = res.pivot_table(index=["condition"], columns=["k"], values=["r2", "smape"], aggfunc="first")
    tab.to_csv(out_dir / "exp010_summary_table.csv")

    print("[write]", out_dir / "exp010_results.csv")
    print("[write]", out_dir / "exp010_summary_table.csv")


if __name__ == "__main__":
    main()
