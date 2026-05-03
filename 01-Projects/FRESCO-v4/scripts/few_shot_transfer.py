#!/usr/bin/env python3
"""Few-shot cross-cluster transfer modeling for FRESCO v4.

Extends v3 model_transfer.py with few-shot calibration: sample N labeled
target examples for calibration, hold out the rest for evaluation.

Strategies:
  - zero_shot:       N=0, train on source only (v3 baseline).
  - output_recal:    Train on source, fit linear y=a*pred+b from N target labels.
  - fine_tune:       Train on source ∪ N target (upweighted target rows).
  - stacked:         Source model produces predictions; second-stage model
                     trained on N target labels using [source_pred, features].
  - target_only:     Train only on N target labels. No source data.
  - full_target:     Train on full target train set (upper bound ceiling).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fresco_data_loader import (
    build_file_records,
    capture_environment_artifacts,
    describe_regime,
    git_info,
    load_manifest_rows,
    load_sampling_plan,
    read_job_level_frame,
    regime_mask,
    regime_required_columns,
    resolve_path,
    sampling_plan_entries_for_cluster,
    sampling_plan_seed_for_cluster,
    utc_now_iso,
    write_json,
)


# ---------------------------------------------------------------------------
# Metrics helpers (carried from v3 model_transfer.py)
# ---------------------------------------------------------------------------

def _smape_median(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.abs(y_true) + np.abs(y_pred) + 1e-8
    return float(np.median(2 * np.abs(y_true - y_pred) / denom) * 100.0)


def _empty_eval_metrics() -> dict:
    return {
        "r2": None,
        "mae_log": None,
        "mdae_log": None,
        "smape": None,
        "bias_log": None,
        "slope": None,
        "intercept": None,
        "overflow_pred": False,
    }


def _evaluate(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> dict:
    if len(y_true_log) == 0:
        return _empty_eval_metrics()

    y_true = np.expm1(y_true_log)
    y_pred = np.expm1(y_pred_log)
    overflow = bool(np.any(~np.isfinite(y_pred)))
    if overflow:
        y_pred = np.where(np.isfinite(y_pred), y_pred, np.nan)
    resid = y_true_log - y_pred_log

    A = np.vstack([y_pred_log, np.ones_like(y_pred_log)]).T
    slope, intercept = np.linalg.lstsq(A, y_true_log, rcond=None)[0]

    return {
        "r2": float(r2_score(y_true_log, y_pred_log)),
        "mae_log": float(mean_absolute_error(y_true_log, y_pred_log)),
        "mdae_log": float(np.median(np.abs(resid))),
        "smape": _smape_median(y_true, y_pred),
        "bias_log": float(np.mean(resid)),
        "slope": float(slope),
        "intercept": float(intercept),
        "overflow_pred": overflow,
    }


def _safe_predict(model, X: np.ndarray) -> np.ndarray:
    if len(X) == 0:
        return np.array([], dtype=float)
    return np.asarray(model.predict(X), dtype=float)


def _bootstrap_r2(
    y_true_log: np.ndarray, y_pred_log: np.ndarray, n_boot: int, seed: int
) -> dict:
    rng = np.random.default_rng(seed)
    n = len(y_true_log)
    if n == 0:
        return {"r2_mean": None, "r2_ci_lower": None, "r2_ci_upper": None}
    stats = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        stats.append(r2_score(y_true_log[idx], y_pred_log[idx]))
    stats = np.array(stats, dtype=float)
    return {
        "r2_mean": float(np.mean(stats)),
        "r2_ci_lower": float(np.quantile(stats, 0.025)),
        "r2_ci_upper": float(np.quantile(stats, 0.975)),
    }


# ---------------------------------------------------------------------------
# Few-shot calibration strategies
# ---------------------------------------------------------------------------

def _resolve_calibration_request(
    n_target: int,
    n_labels: int,
    min_eval_rows: int,
) -> dict:
    requested_n_labels = int(n_labels)
    min_target_eval_rows = max(1, int(min_eval_rows))
    normalized_request = max(requested_n_labels, 0)
    max_calibration_n = max(n_target - min_target_eval_rows, 0)
    effective_n_labels = min(normalized_request, max_calibration_n)
    return {
        "requested_n_labels": requested_n_labels,
        "effective_n_labels": int(effective_n_labels),
        "min_target_eval_rows": int(min_target_eval_rows),
        "available_target_rows": int(n_target),
        "was_capped": bool(effective_n_labels < normalized_request),
    }


def _sample_calibration_set(
    n_target: int,
    y_tgt_log: np.ndarray,
    n_labels: int,
    seed: int,
    min_eval_rows: int = 1,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Sample N target indices for calibration, stratified by label quartile.

    Returns (cal_idx, eval_idx, split_meta) where the arrays index the target
    cohort and split_meta records any capping applied to preserve evaluation
    holdout rows.
    """
    split_meta = _resolve_calibration_request(n_target, n_labels, min_eval_rows)
    effective_n_labels = int(split_meta["effective_n_labels"])
    if effective_n_labels <= 0:
        return (
            np.array([], dtype=int),
            np.arange(n_target, dtype=int),
            split_meta,
        )

    rng = np.random.default_rng(seed)
    quartiles = np.digitize(
        y_tgt_log, np.quantile(y_tgt_log, [0.25, 0.5, 0.75])
    )
    all_idx = np.arange(n_target)
    cal_indices: list[int] = []

    # Stratified sampling: proportional allocation per quartile
    unique_q = np.unique(quartiles)
    per_q = max(1, effective_n_labels // len(unique_q))
    remainder = effective_n_labels - per_q * len(unique_q)

    for i, q in enumerate(unique_q):
        q_idx = all_idx[quartiles == q]
        n_take = per_q + (1 if i < remainder else 0)
        n_take = min(n_take, len(q_idx))
        chosen = rng.choice(q_idx, size=n_take, replace=False)
        cal_indices.extend(chosen.tolist())

    # If rounding left us short, sample remaining from unchosen
    if len(cal_indices) < effective_n_labels:
        unchosen = np.setdiff1d(all_idx, cal_indices)
        extra = rng.choice(
            unchosen,
            size=min(effective_n_labels - len(cal_indices), len(unchosen)),
            replace=False,
        )
        cal_indices.extend(extra.tolist())

    cal_idx = np.array(sorted(cal_indices[:effective_n_labels]), dtype=int)
    eval_idx = np.setdiff1d(all_idx, cal_idx)
    split_meta["effective_n_labels"] = int(len(cal_idx))
    return cal_idx, eval_idx, split_meta


def _calibrate_output_recal(
    y_cal_true_log: np.ndarray,
    y_cal_pred_log: np.ndarray,
    y_all_pred_log: np.ndarray,
) -> tuple[np.ndarray, dict]:
    """Linear output recalibration: y_corrected = a * y_pred + b."""
    if len(y_cal_true_log) < 2:
        return y_all_pred_log, {"a": 1.0, "b": 0.0, "n_cal": len(y_cal_true_log)}

    A = np.vstack([y_cal_pred_log, np.ones_like(y_cal_pred_log)]).T
    coeffs = np.linalg.lstsq(A, y_cal_true_log, rcond=None)[0]
    a, b = float(coeffs[0]), float(coeffs[1])
    y_corrected = a * y_all_pred_log + b
    return y_corrected, {"a": a, "b": b, "n_cal": len(y_cal_true_log)}


def _calibrate_fine_tune(
    X_src_train: np.ndarray,
    y_src_train_log: np.ndarray,
    X_cal: np.ndarray,
    y_cal_log: np.ndarray,
    X_eval: np.ndarray,
    model_cfg: dict,
    seed: int,
) -> tuple[np.ndarray, dict]:
    """Fine-tune: retrain on source ∪ N target with upweighted target rows."""
    n_src = len(X_src_train)
    n_cal = len(X_cal)
    if n_cal == 0:
        pipe = _build_pipeline(model_cfg, seed)
        pipe.fit(X_src_train, y_src_train_log)
        return _safe_predict(pipe, X_eval), {"target_weight": 0.0, "n_cal": 0}

    target_weight = n_src / max(n_cal, 1)
    if len(X_eval) == 0:
        return np.array([], dtype=float), {
            "target_weight": float(target_weight),
            "n_cal": n_cal,
        }

    X_combined = np.vstack([X_src_train, X_cal])
    y_combined = np.concatenate([y_src_train_log, y_cal_log])
    w = np.concatenate([np.ones(n_src), np.full(n_cal, target_weight)])

    pipe = _build_pipeline(model_cfg, seed)
    # Pipeline doesn't pass sample_weight through easily, so fit manually
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    X_transformed = scaler.fit_transform(imputer.fit_transform(X_combined))

    regressor = _make_regressor(model_cfg, seed)
    if hasattr(regressor, "sample_weight"):
        regressor.fit(X_transformed, y_combined, sample_weight=w)
    else:
        # Ridge supports sample_weight
        regressor.fit(X_transformed, y_combined, sample_weight=w)

    X_eval_t = scaler.transform(imputer.transform(X_eval))
    return np.asarray(regressor.predict(X_eval_t), dtype=float), {
        "target_weight": float(target_weight),
        "n_cal": n_cal,
    }


def _calibrate_stacked(
    source_pred_cal_log: np.ndarray,
    X_cal: np.ndarray,
    y_cal_log: np.ndarray,
    source_pred_eval_log: np.ndarray,
    X_eval: np.ndarray,
    seed: int,
) -> tuple[np.ndarray, dict]:
    """Stacked: second-stage Ridge on [source_pred, features] for N cal labels."""
    if len(y_cal_log) < 2:
        return source_pred_eval_log, {"n_cal": len(y_cal_log), "n_stage2_features": 0}

    # Build stage-2 feature matrix: [source_prediction, original_features]
    X2_cal = np.column_stack([source_pred_cal_log.reshape(-1, 1), X_cal])
    X2_eval = np.column_stack([source_pred_eval_log.reshape(-1, 1), X_eval])

    if len(X2_eval) == 0:
        return np.array([], dtype=float), {
            "n_cal": len(y_cal_log),
            "n_stage2_features": X2_cal.shape[1],
        }

    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=1.0, random_state=seed)),
    ])
    pipe.fit(X2_cal, y_cal_log)
    return np.asarray(pipe.predict(X2_eval), dtype=float), {
        "n_cal": len(y_cal_log),
        "n_stage2_features": X2_cal.shape[1],
    }


def _calibrate_target_only(
    X_cal: np.ndarray,
    y_cal_log: np.ndarray,
    X_eval: np.ndarray,
    model_cfg: dict,
    seed: int,
) -> tuple[np.ndarray, dict]:
    """Target-only baseline: train only on N calibration labels."""
    if len(y_cal_log) < 2:
        mean_pred = np.mean(y_cal_log) if len(y_cal_log) > 0 else 0.0
        return np.full(len(X_eval), mean_pred), {"n_cal": len(y_cal_log)}

    if len(X_eval) == 0:
        return np.array([], dtype=float), {"n_cal": len(y_cal_log)}

    pipe = _build_pipeline(model_cfg, seed)
    pipe.fit(X_cal, y_cal_log)
    return _safe_predict(pipe, X_eval), {"n_cal": len(y_cal_log)}


# ---------------------------------------------------------------------------
# Model construction helpers
# ---------------------------------------------------------------------------

def _make_regressor(model_cfg: dict, seed: int):
    model_type = str(model_cfg.get("type", "ridge")).lower()
    if model_type == "huber":
        return HuberRegressor(
            epsilon=float(model_cfg.get("epsilon", 1.35)),
            alpha=float(model_cfg.get("alpha", 0.0001)),
            max_iter=int(model_cfg.get("max_iter", 500)),
        )
    return Ridge(alpha=float(model_cfg.get("alpha", 1.0)), random_state=seed)


def _build_pipeline(model_cfg: dict, seed: int) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("regressor", _make_regressor(model_cfg, seed)),
    ])


# ---------------------------------------------------------------------------
# Provenance / artifact helpers
# ---------------------------------------------------------------------------

def _limitations(
    label_column: str, label_proxy: bool, no_data: bool, strategy: str, n_labels: int
) -> list[str]:
    notes = []
    if label_proxy:
        notes.append(
            f"Label {label_column} is marked proxy=true; interpret as proxy-target transfer."
        )
    notes.append(
        f"Few-shot strategy={strategy}, N={n_labels}. "
        "Calibration set sampled stratified by label quartile."
    )
    if no_data:
        notes.append("No rows remained after filters; metrics not computed.")
    return notes


def _write_common_artifacts(
    exp_dir: Path,
    repo_root: Path,
    cfg_path: Path,
    run_id: str,
    used_files: list[dict],
) -> None:
    metadata = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "script": str((repo_root / "scripts" / "few_shot_transfer.py").resolve()),
        "config": str(cfg_path),
        "git": git_info(repo_root),
        "python": sys.version.replace("\n", " "),
        "cwd": os.getcwd(),
    }
    write_json(exp_dir / "manifests" / "run_metadata.json", metadata)
    write_json(exp_dir / "manifests" / "input_files_used.json", used_files)
    capture_environment_artifacts(exp_dir / "validation", cwd=repo_root)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="FRESCO v4 few-shot transfer modeling")
    ap.add_argument("--config", required=True, help="Path to experiment config JSON")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    cfg_path = resolve_path(args.config, repo_root)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    run_id = cfg["run_id"]
    exp_dir = (repo_root / "experiments" / run_id).resolve()
    for d in ["config", "logs", "results", "manifests", "validation"]:
        (exp_dir / d).mkdir(parents=True, exist_ok=True)

    (exp_dir / "config" / Path(cfg_path).name).write_text(
        cfg_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    log_path = exp_dir / "logs" / "few_shot_transfer.log"

    def log(msg: str) -> None:
        line = f"[{utc_now_iso()}] {msg}"
        print(line)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    # ---- Config parsing ----
    seed = int(cfg.get("random_seed", cfg.get("split", {}).get("seed", 1337)))
    data_seed = int(cfg.get("data_seed", seed))
    split_seed = int(cfg.get("split", {}).get("seed", seed))
    random.seed(seed)
    np.random.seed(seed)

    source = cfg["source_cluster"]
    target = cfg["target_cluster"]
    regime = cfg.get("regime", "cpu_standard")
    label_col = cfg["label_column"]
    label_transform = cfg.get("label_transform", "log1p")
    label_proxy = bool(cfg.get("label_proxy", True))
    feature_cols = list(cfg["feature_columns"])
    max_src = int(cfg.get("max_rows_source", 200000))
    max_tgt = int(cfg.get("max_rows_target", 200000))
    n_boot = int(cfg.get("n_boot", 200))
    sample_n_row_groups = int(cfg.get("sample_n_row_groups_per_file", 0) or 0) or None
    sampling_plan_cfg = cfg.get("sampling_plan_path")

    # Few-shot config
    fs_cfg = cfg.get("few_shot", {})
    n_labels = int(fs_cfg.get("n_target_labels", 0))
    strategy = str(fs_cfg.get("strategy", "zero_shot")).lower()
    target_label_seed = int(fs_cfg.get("target_label_seed", seed))
    requested_min_target_eval_rows = int(fs_cfg.get("min_target_eval_rows", 1))
    min_target_eval_rows = max(1, requested_min_target_eval_rows)

    overlap = cfg.get("overlap_run", {})
    matched_source_idx = resolve_path(overlap["matched_source_indices"], repo_root)
    matched_target_idx = resolve_path(overlap["matched_target_indices"], repo_root)

    model_cfg = cfg.get("model", {"type": "ridge", "alpha": 1.0})

    log(f"run_id={run_id}")
    log(f"config={cfg_path}")
    log(f"source={source} target={target} regime={regime}")
    log(f"label={label_col} transform={label_transform} proxy={label_proxy}")
    log(f"features={feature_cols}")
    log(
        "seeds: "
        f"random_seed={seed} data_seed={data_seed} "
        f"split_seed={split_seed} target_label_seed={target_label_seed}"
    )
    log(
        "few_shot: "
        f"strategy={strategy} requested_n_labels={n_labels} "
        f"label_seed={target_label_seed} min_target_eval_rows={min_target_eval_rows}"
    )
    if requested_min_target_eval_rows != min_target_eval_rows:
        log(
            "few_shot.min_target_eval_rows="
            f"{requested_min_target_eval_rows} clamped to {min_target_eval_rows}"
        )
    log(f"matched_source_indices={matched_source_idx}")
    log(f"matched_target_indices={matched_target_idx}")

    # ---- Load overlap cohort JIDs ----
    src_jids = set(pd.read_parquet(matched_source_idx)["jid"].astype("string").tolist())
    tgt_jids = set(pd.read_parquet(matched_target_idx)["jid"].astype("string").tolist())

    # ---- Load data ----
    manifest_rows = load_manifest_rows(cfg["inputs_manifest"], repo_root)
    needed = ["jid", label_col] + feature_cols + regime_required_columns(regime)
    needed = list(dict.fromkeys(needed))

    sampling_plan_path: Path | None = None
    source_sampling_plan = None
    target_sampling_plan = None
    source_sampling_seed = None
    target_sampling_seed = None
    if sampling_plan_cfg:
        sampling_plan, sampling_plan_path = load_sampling_plan(sampling_plan_cfg, repo_root)
        source_sampling_plan = sampling_plan_entries_for_cluster(sampling_plan, source)
        target_sampling_plan = sampling_plan_entries_for_cluster(sampling_plan, target)
        if source_sampling_plan is None or target_sampling_plan is None:
            raise ValueError(
                f"Sampling plan must define entries for both {source} and {target}."
            )
        source_sampling_seed = sampling_plan_seed_for_cluster(sampling_plan, source)
        target_sampling_seed = sampling_plan_seed_for_cluster(sampling_plan, target)
        log(f"sampling_plan_path={sampling_plan_path}")

    src, src_meta = read_job_level_frame(
        manifest_rows=manifest_rows, cluster=source, columns=needed,
        max_rows=max_src, seed=data_seed,
        sample_n_row_groups_per_file=sample_n_row_groups,
        row_group_plan=source_sampling_plan, plan_seed=source_sampling_seed,
    )
    tgt, tgt_meta = read_job_level_frame(
        manifest_rows=manifest_rows, cluster=target, columns=needed,
        max_rows=max_tgt, seed=data_seed,
        sample_n_row_groups_per_file=sample_n_row_groups,
        row_group_plan=target_sampling_plan, plan_seed=target_sampling_seed,
    )
    log(f"source_raw={src_meta['raw_rows_sampled']} source_jobs={src_meta['job_rows']}")
    log(f"target_raw={tgt_meta['raw_rows_sampled']} target_jobs={tgt_meta['job_rows']}")

    # ---- Apply regime + overlap filters ----
    src = src.loc[regime_mask(src, regime)].copy()
    tgt = tgt.loc[regime_mask(tgt, regime)].copy()
    src = src.loc[src["jid"].astype("string").isin(src_jids)].copy()
    tgt = tgt.loc[tgt["jid"].astype("string").isin(tgt_jids)].copy()
    log(f"source_overlap={len(src)} target_overlap={len(tgt)}")

    # ---- Coerce types + filter valid labels ----
    for col in feature_cols:
        src[col] = pd.to_numeric(src[col], errors="coerce")
        tgt[col] = pd.to_numeric(tgt[col], errors="coerce")

    src[label_col] = pd.to_numeric(src[label_col], errors="coerce")
    tgt[label_col] = pd.to_numeric(tgt[label_col], errors="coerce")
    src = src.loc[src[label_col].notna() & (src[label_col] > 0)].copy()
    tgt = tgt.loc[tgt[label_col].notna() & (tgt[label_col] > 0)].copy()
    log(f"source_after_label={len(src)} target_after_label={len(tgt)}")

    # ---- Build file provenance ----
    hash_cache: dict[str, str] = {}
    used_files = build_file_records(src_meta["used_paths"], source, hash_cache=hash_cache)
    used_files.extend(build_file_records(tgt_meta["used_paths"], target, hash_cache=hash_cache))
    if sampling_plan_path is not None:
        used_files.extend(build_file_records([sampling_plan_path], "sampling_plan", hash_cache=hash_cache))
    used_files.extend(build_file_records(
        [matched_source_idx, matched_target_idx], "overlap", hash_cache=hash_cache,
    ))

    # ---- Transform features + labels ----
    no_data = len(src) == 0 or len(tgt) == 0
    if not no_data and label_transform == "log1p":
        y_src = np.log1p(src[label_col].to_numpy(dtype=float))
        y_tgt = np.log1p(tgt[label_col].to_numpy(dtype=float))
    elif no_data:
        y_src = np.array([], dtype=float)
        y_tgt = np.array([], dtype=float)
    else:
        raise ValueError(f"Unsupported label_transform: {label_transform}")

    X_src = src[feature_cols].copy()
    X_tgt = tgt[feature_cols].copy()
    for col in feature_cols:
        X_src[col] = np.log1p(X_src[col])
        X_tgt[col] = np.log1p(X_tgt[col])

    # ---- Source train/test split ----
    split_cfg = cfg.get("split", {"type": "random", "test_frac": 0.2, "seed": seed})
    test_frac = float(split_cfg.get("test_frac", 0.2))
    split_rng = np.random.default_rng(split_seed)

    n_src = len(X_src)
    src_idx = np.arange(n_src)
    split_rng.shuffle(src_idx)
    n_test = int(round(test_frac * n_src))
    src_test_idx = src_idx[:n_test]
    src_train_idx = src_idx[n_test:]
    no_data = no_data or len(src_train_idx) == 0 or len(src_test_idx) == 0 or len(X_tgt) == 0

    # ---- Few-shot: split target into calibration + evaluation ----
    n_tgt = len(X_tgt)
    target_split_meta = {
        "requested_n_labels": int(n_labels),
        "effective_n_labels": 0,
        "min_target_eval_rows": int(min_target_eval_rows),
        "available_target_rows": int(n_tgt),
        "was_capped": False,
    }
    if not no_data and strategy not in ("zero_shot", "full_target"):
        cal_idx, eval_idx, target_split_meta = _sample_calibration_set(
            n_tgt, y_tgt, n_labels, target_label_seed, min_target_eval_rows
        )
    elif not no_data and strategy == "full_target":
        # Full-target upper bound: use 80% for training, 20% for eval
        ft_rng = np.random.default_rng(target_label_seed)
        tgt_perm = np.arange(n_tgt)
        ft_rng.shuffle(tgt_perm)
        n_ft_test = int(round(0.2 * n_tgt))
        eval_idx = tgt_perm[:n_ft_test]
        cal_idx = tgt_perm[n_ft_test:]
        target_split_meta["effective_n_labels"] = int(len(cal_idx))
    else:
        cal_idx = np.array([], dtype=int)
        eval_idx = np.arange(n_tgt)

    if target_split_meta["was_capped"]:
        log(
            "capped target calibration request from "
            f"{target_split_meta['requested_n_labels']} to "
            f"{target_split_meta['effective_n_labels']} to preserve "
            f"min_target_eval_rows={target_split_meta['min_target_eval_rows']} "
            f"with target_n={target_split_meta['available_target_rows']}"
        )
    if len(eval_idx) < min_target_eval_rows:
        log(
            "available target evaluation rows fell below the requested minimum: "
            f"actual_eval_n={len(eval_idx)} min_target_eval_rows={min_target_eval_rows}"
        )
    log(f"target_calibration_n={len(cal_idx)} target_eval_n={len(eval_idx)}")
    log(f"source_train_n={len(src_train_idx)} source_test_n={len(src_test_idx)}")

    # ---- Build metrics skeleton ----
    metrics: dict = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "dataset_label": cfg.get("dataset_label"),
        "pair": {"source": source, "target": target},
        "regime": regime,
        "label": {"column": label_col, "transform": label_transform, "proxy": label_proxy},
        "features": feature_cols,
        "model": model_cfg,
        "seeds": {
            "random_seed": int(seed),
            "data_seed": int(data_seed),
            "split_seed": int(split_seed),
            "target_label_seed": int(target_label_seed),
        },
        "few_shot": {
            "strategy": strategy,
            "n_target_labels": n_labels,
            "target_label_seed": target_label_seed,
            "min_target_eval_rows": int(target_split_meta["min_target_eval_rows"]),
            "effective_n_target_labels": int(target_split_meta["effective_n_labels"]),
            "calibration_n_capped": bool(target_split_meta["was_capped"]),
            "min_target_eval_rows_satisfied": bool(len(eval_idx) >= min_target_eval_rows),
            "actual_cal_n": int(len(cal_idx)),
            "actual_eval_n": int(len(eval_idx)),
        },
        "overlap": {
            "run_id": overlap.get("run_id"),
            "overlap_band": overlap.get("overlap_band"),
            "matched_source_n": int(len(src)),
            "matched_target_n": int(len(tgt)),
        },
        "eval": {
            "source_test": None,
            "target_eval": None,
            "target_r2_bootstrap": None,
        },
        "calibration_details": None,
        "limitations": _limitations(label_col, label_proxy, no_data, strategy, n_labels),
    }
    metrics["limitations"].append(describe_regime(regime))
    if target_split_meta["was_capped"]:
        metrics["limitations"].append(
            "Requested target calibration size "
            f"{target_split_meta['requested_n_labels']} was capped to "
            f"{target_split_meta['effective_n_labels']} to preserve at least "
            f"{target_split_meta['min_target_eval_rows']} target evaluation rows."
        )
    if len(eval_idx) < min_target_eval_rows:
        metrics["limitations"].append(
            "Target overlap cohort is smaller than the requested minimum target holdout: "
            f"actual_eval_n={len(eval_idx)} min_target_eval_rows={min_target_eval_rows}."
        )

    if no_data:
        write_json(exp_dir / "results" / "metrics.json", metrics)
        _write_common_artifacts(exp_dir, repo_root, cfg_path, run_id, used_files)
        log("no data after filters; metrics not computed")
        return 0

    # ---- Prepare numpy arrays ----
    X_src_np = X_src.to_numpy(dtype=float)
    X_tgt_np = X_tgt.to_numpy(dtype=float)

    X_src_train = X_src_np[src_train_idx]
    y_src_train = y_src[src_train_idx]
    X_src_test = X_src_np[src_test_idx]
    y_src_test = y_src[src_test_idx]

    X_tgt_cal = X_tgt_np[cal_idx] if len(cal_idx) > 0 else np.empty((0, len(feature_cols)))
    y_tgt_cal = y_tgt[cal_idx] if len(cal_idx) > 0 else np.array([], dtype=float)
    X_tgt_eval = X_tgt_np[eval_idx]
    y_tgt_eval = y_tgt[eval_idx]

    # ---- Save calibration set indices ----
    if len(cal_idx) > 0:
        cal_jids = tgt.iloc[cal_idx]["jid"].astype("string").to_numpy()
        pd.DataFrame({"jid": cal_jids}).to_parquet(
            exp_dir / "results" / "calibration_set_jids.parquet", index=False
        )

    # ---- Execute strategy ----
    calibration_details: dict = {}

    if strategy == "zero_shot":
        # Train source model, predict directly on target eval
        pipe = _build_pipeline(model_cfg, seed)
        pipe.fit(X_src_train, y_src_train)
        y_src_pred = _safe_predict(pipe, X_src_test)
        y_tgt_pred = _safe_predict(pipe, X_tgt_eval)
        calibration_details = {"strategy": "zero_shot", "n_cal": 0}

    elif strategy == "output_recal":
        # Train source model, predict on cal set, fit linear correction
        pipe = _build_pipeline(model_cfg, seed)
        pipe.fit(X_src_train, y_src_train)
        y_src_pred = _safe_predict(pipe, X_src_test)

        y_cal_pred = _safe_predict(pipe, X_tgt_cal)
        y_tgt_raw_pred = _safe_predict(pipe, X_tgt_eval)
        y_tgt_pred, recal_params = _calibrate_output_recal(
            y_tgt_cal, y_cal_pred, y_tgt_raw_pred
        )
        calibration_details = {"strategy": "output_recal", **recal_params}

    elif strategy == "fine_tune":
        # Source model for source-test eval, then retrain with target labels
        pipe_src = _build_pipeline(model_cfg, seed)
        pipe_src.fit(X_src_train, y_src_train)
        y_src_pred = _safe_predict(pipe_src, X_src_test)

        y_tgt_pred, ft_details = _calibrate_fine_tune(
            X_src_train, y_src_train,
            X_tgt_cal, y_tgt_cal,
            X_tgt_eval, model_cfg, seed,
        )
        calibration_details = {"strategy": "fine_tune", **ft_details}

    elif strategy == "stacked":
        # Source model predictions → stage-2 model on cal labels
        pipe = _build_pipeline(model_cfg, seed)
        pipe.fit(X_src_train, y_src_train)
        y_src_pred = _safe_predict(pipe, X_src_test)

        src_pred_cal = _safe_predict(pipe, X_tgt_cal)
        src_pred_eval = _safe_predict(pipe, X_tgt_eval)
        y_tgt_pred, stack_details = _calibrate_stacked(
            src_pred_cal, X_tgt_cal, y_tgt_cal,
            src_pred_eval, X_tgt_eval, seed,
        )
        calibration_details = {"strategy": "stacked", **stack_details}

    elif strategy == "target_only":
        # No source model — train only on N target labels
        pipe_src = _build_pipeline(model_cfg, seed)
        pipe_src.fit(X_src_train, y_src_train)
        y_src_pred = _safe_predict(pipe_src, X_src_test)

        y_tgt_pred, to_details = _calibrate_target_only(
            X_tgt_cal, y_tgt_cal, X_tgt_eval, model_cfg, seed,
        )
        calibration_details = {"strategy": "target_only", **to_details}

    elif strategy == "full_target":
        # Upper bound: train on full target calibration set (80% of target)
        pipe_src = _build_pipeline(model_cfg, seed)
        pipe_src.fit(X_src_train, y_src_train)
        y_src_pred = _safe_predict(pipe_src, X_src_test)

        pipe_tgt = _build_pipeline(model_cfg, seed)
        pipe_tgt.fit(X_tgt_cal, y_tgt_cal)
        y_tgt_pred = _safe_predict(pipe_tgt, X_tgt_eval)
        calibration_details = {"strategy": "full_target", "n_cal": len(cal_idx)}

    else:
        raise ValueError(f"Unknown few-shot strategy: {strategy}")

    # ---- Compute metrics ----
    metrics["eval"] = {
        "source_test": _evaluate(y_src_test, y_src_pred),
        "target_eval": _evaluate(y_tgt_eval, y_tgt_pred),
        "target_r2_bootstrap": _bootstrap_r2(y_tgt_eval, y_tgt_pred, n_boot, seed),
    }
    metrics["calibration_details"] = calibration_details

    write_json(exp_dir / "results" / "metrics.json", metrics)

    # ---- Save predictions ----
    pd.DataFrame({
        "jid": src.iloc[src_test_idx]["jid"].astype("string").to_numpy(),
        "y_true_log": y_src_test,
        "y_pred_log": y_src_pred,
    }).to_parquet(exp_dir / "results" / "predictions_source_test.parquet", index=False)

    pd.DataFrame({
        "jid": tgt.iloc[eval_idx]["jid"].astype("string").to_numpy(),
        "y_true_log": y_tgt_eval,
        "y_pred_log": y_tgt_pred,
    }).to_parquet(exp_dir / "results" / "predictions_target.parquet", index=False)

    _write_common_artifacts(exp_dir, repo_root, cfg_path, run_id, used_files)
    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
