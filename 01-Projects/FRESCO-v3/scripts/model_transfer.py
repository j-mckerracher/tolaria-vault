#!/usr/bin/env python3
"""Phase 3: transfer modeling on proxy or authoritative v3 inputs."""

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


def _smape_median(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.abs(y_true) + np.abs(y_pred) + 1e-8
    return float(np.median(2 * np.abs(y_true - y_pred) / denom) * 100.0)


def _evaluate(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> dict:
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


def _bootstrap_r2(y_true_log: np.ndarray, y_pred_log: np.ndarray, n_boot: int, seed: int) -> dict:
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


def _covariance(x: np.ndarray) -> np.ndarray:
    n = x.shape[0]
    if n < 2:
        return np.eye(x.shape[1])
    xc = x - np.mean(x, axis=0, keepdims=True)
    return (xc.T @ xc) / float(n - 1)


def _matrix_power(cov: np.ndarray, power: float) -> np.ndarray:
    vals, vecs = np.linalg.eigh(cov)
    vals = np.clip(vals, 1e-12, None)
    vals_power = np.power(vals, power)
    return vecs @ np.diag(vals_power) @ vecs.T


def _coral_matrix(x_src: np.ndarray, x_tgt: np.ndarray, reg: float) -> np.ndarray:
    n_feat = x_src.shape[1]
    cs = _covariance(x_src) + reg * np.eye(n_feat)
    ct = _covariance(x_tgt) + reg * np.eye(n_feat)
    return _matrix_power(cs, -0.5) @ _matrix_power(ct, 0.5)


def _quantile_output_correct(
    y_ref_log: np.ndarray, y_pred_log: np.ndarray, n_quantiles: int
) -> np.ndarray:
    if len(y_ref_log) == 0 or len(y_pred_log) == 0:
        return y_pred_log

    n_quantiles = _effective_quantile_count(y_ref_log, y_pred_log, n_quantiles)
    quantiles = np.linspace(0.0, 1.0, n_quantiles)
    ref_q = np.quantile(y_ref_log, quantiles)
    pred_q = np.quantile(y_pred_log, quantiles)
    pred_unique, inverse_idx = np.unique(pred_q, return_inverse=True)
    ref_unique = np.array(
        [np.median(ref_q[inverse_idx == idx]) for idx in range(len(pred_unique))],
        dtype=float,
    )
    if len(pred_unique) == 1:
        return np.full_like(y_pred_log, ref_unique[0], dtype=float)
    return np.interp(
        y_pred_log,
        pred_unique,
        ref_unique,
        left=ref_unique[0],
        right=ref_unique[-1],
    )


def _effective_quantile_count(
    y_ref_log: np.ndarray, y_pred_log: np.ndarray, n_quantiles: int
) -> int:
    return max(2, min(int(n_quantiles), len(y_ref_log), len(y_pred_log)))


def _limitations(label_column: str, label_proxy: bool, no_data: bool) -> list[str]:
    notes = [
        "Model uses the feature set specified in the run config; treat this as an ablation baseline, not the final intended Phase 3 feature set."
    ]
    if label_proxy:
        notes.insert(
            0,
            f"Label {label_column} is marked proxy=true in the config; interpret results as proxy-target transfer only.",
        )
    if no_data:
        notes.append("No training/test or target rows remained after overlap, label, and regime filters; metrics were not computed.")
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
        "script": str((repo_root / "scripts" / "model_transfer.py").resolve()),
        "config": str(cfg_path),
        "git": git_info(repo_root),
        "python": sys.version.replace("\n", " "),
        "cwd": os.getcwd(),
    }
    write_json(exp_dir / "manifests" / "run_metadata.json", metadata)
    write_json(exp_dir / "manifests" / "input_files_used.json", used_files)
    capture_environment_artifacts(exp_dir / "validation", cwd=repo_root)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    cfg_path = resolve_path(args.config, repo_root)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    run_id = cfg["run_id"]
    exp_dir = (repo_root / "experiments" / run_id).resolve()
    for directory in ["config", "logs", "results", "manifests", "validation"]:
        (exp_dir / directory).mkdir(parents=True, exist_ok=True)

    (exp_dir / "config" / Path(cfg_path).name).write_text(
        cfg_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    log_path = exp_dir / "logs" / "model_transfer.log"

    def log(message: str) -> None:
        line = f"[{utc_now_iso()}] {message}"
        print(line)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    seed = int(cfg.get("random_seed", cfg.get("split", {}).get("seed", 1337)))
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

    overlap = cfg.get("overlap_run", {})
    matched_source_idx = resolve_path(overlap["matched_source_indices"], repo_root)
    matched_target_idx = resolve_path(overlap["matched_target_indices"], repo_root)

    log(f"run_id={run_id}")
    log(f"config={cfg_path}")
    log(f"source={source} target={target} regime={regime}")
    log(f"label={label_col} transform={label_transform} proxy={label_proxy}")
    log(f"features={feature_cols}")
    log(f"matched_source_indices={matched_source_idx}")
    log(f"matched_target_indices={matched_target_idx}")
    log(f"sample_n_row_groups_per_file={sample_n_row_groups}")

    src_jids = set(pd.read_parquet(matched_source_idx)["jid"].astype("string").tolist())
    tgt_jids = set(pd.read_parquet(matched_target_idx)["jid"].astype("string").tolist())

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
                f"Sampling plan {sampling_plan_path} must define entries for both {source} and {target}."
            )
        source_sampling_seed = sampling_plan_seed_for_cluster(sampling_plan, source)
        target_sampling_seed = sampling_plan_seed_for_cluster(sampling_plan, target)
        log(f"sampling_plan_path={sampling_plan_path}")

    src, src_meta = read_job_level_frame(
        manifest_rows=manifest_rows,
        cluster=source,
        columns=needed,
        max_rows=max_src,
        seed=seed,
        sample_n_row_groups_per_file=sample_n_row_groups,
        row_group_plan=source_sampling_plan,
        plan_seed=source_sampling_seed,
    )
    tgt, tgt_meta = read_job_level_frame(
        manifest_rows=manifest_rows,
        cluster=target,
        columns=needed,
        max_rows=max_tgt,
        seed=seed + 1,
        sample_n_row_groups_per_file=sample_n_row_groups,
        row_group_plan=target_sampling_plan,
        plan_seed=target_sampling_seed,
    )
    log(
        f"source_raw_rows_sampled={src_meta['raw_rows_sampled']} "
        f"source_job_rows={src_meta['job_rows']} source_files_used={len(src_meta['used_paths'])}"
    )
    if src_meta["read_errors"]:
        log(f"source_sampling_read_errors={len(src_meta['read_errors'])}")
        for error in src_meta["read_errors"][:5]:
            log(
                "source_read_error "
                f"path={error['path']} row_group={error['row_group']} error={error['error']}"
            )
    log(
        f"target_raw_rows_sampled={tgt_meta['raw_rows_sampled']} "
        f"target_job_rows={tgt_meta['job_rows']} target_files_used={len(tgt_meta['used_paths'])}"
    )
    if tgt_meta["read_errors"]:
        log(f"target_sampling_read_errors={len(tgt_meta['read_errors'])}")
        for error in tgt_meta["read_errors"][:5]:
            log(
                "target_read_error "
                f"path={error['path']} row_group={error['row_group']} error={error['error']}"
            )

    src = src.loc[regime_mask(src, regime)].copy()
    tgt = tgt.loc[regime_mask(tgt, regime)].copy()

    src = src.loc[src["jid"].astype("string").isin(src_jids)].copy()
    tgt = tgt.loc[tgt["jid"].astype("string").isin(tgt_jids)].copy()
    log(f"source_rows_after_overlap={len(src)} target_rows_after_overlap={len(tgt)}")

    for column in feature_cols:
        src[column] = pd.to_numeric(src[column], errors="coerce")
        tgt[column] = pd.to_numeric(tgt[column], errors="coerce")

    src[label_col] = pd.to_numeric(src[label_col], errors="coerce")
    tgt[label_col] = pd.to_numeric(tgt[label_col], errors="coerce")
    src = src.loc[src[label_col].notna() & (src[label_col] > 0)].copy()
    tgt = tgt.loc[tgt[label_col].notna() & (tgt[label_col] > 0)].copy()
    log(f"source_rows_after_label={len(src)} target_rows_after_label={len(tgt)}")

    hash_cache: dict[str, str] = {}
    used_files = build_file_records(src_meta["used_paths"], source, hash_cache=hash_cache)
    used_files.extend(build_file_records(tgt_meta["used_paths"], target, hash_cache=hash_cache))
    if sampling_plan_path is not None:
        used_files.extend(build_file_records([sampling_plan_path], "sampling_plan", hash_cache=hash_cache))
    used_files.extend(
        build_file_records(
            [matched_source_idx, matched_target_idx],
            "overlap",
            hash_cache=hash_cache,
        )
    )

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
    for column in feature_cols:
        X_src[column] = np.log1p(X_src[column])
        X_tgt[column] = np.log1p(X_tgt[column])

    split = cfg.get("split", {"type": "random", "test_frac": 0.2, "seed": seed})
    test_frac = float(split.get("test_frac", 0.2))
    rng = np.random.default_rng(int(split.get("seed", seed)))

    n_src = len(X_src)
    idx = np.arange(n_src)
    rng.shuffle(idx)
    n_test = int(round(test_frac * n_src))
    test_idx = idx[:n_test]
    train_idx = idx[n_test:]
    no_data = no_data or len(train_idx) == 0 or len(test_idx) == 0 or len(X_tgt) == 0

    model_cfg = cfg.get("model", {"type": "ridge", "alpha": 1.0})
    model_type = str(model_cfg.get("type", "ridge")).lower()
    adaptation_cfg = cfg.get("adaptation", {"type": "none"})
    adaptation_type = str(adaptation_cfg.get("type", "none")).lower()
    adaptation_applied = False
    adaptation_details: dict | None = None
    log(f"adaptation={adaptation_type}")
    if adaptation_type not in {"none", "coral", "quantile_output"}:
        raise ValueError(f"Unsupported adaptation.type: {adaptation_type}")

    if not no_data and adaptation_type == "coral":
        reg = float(adaptation_cfg.get("reg", 1e-6))
        transform = _coral_matrix(
            X_src.iloc[train_idx].to_numpy(dtype=float),
            X_tgt.to_numpy(dtype=float),
            reg,
        )
        X_src = pd.DataFrame(
            X_src.to_numpy(dtype=float) @ transform,
            columns=feature_cols,
            index=X_src.index,
        )
        X_tgt = pd.DataFrame(
            X_tgt.to_numpy(dtype=float) @ transform,
            columns=feature_cols,
            index=X_tgt.index,
        )
        adaptation_applied = True
        adaptation_details = {"type": "coral", "reg": reg}
    elif not no_data and adaptation_type == "quantile_output":
        n_quantiles = int(adaptation_cfg.get("n_quantiles", 100))
        if n_quantiles < 2:
            raise ValueError("quantile_output requires n_quantiles >= 2")
        adaptation_applied = True
        adaptation_details = {
            "type": "quantile_output",
            "n_quantiles_requested": n_quantiles,
        }

    if model_type == "huber":
        regressor = HuberRegressor(
            epsilon=float(model_cfg.get("epsilon", 1.35)),
            alpha=float(model_cfg.get("alpha", 0.0001)),
            max_iter=int(model_cfg.get("max_iter", 500)),
        )
        reg_step = ("huber", regressor)
    else:
        regressor = Ridge(alpha=float(model_cfg.get("alpha", 1.0)), random_state=seed)
        reg_step = ("ridge", regressor)

    model = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            reg_step,
        ]
    )

    log(
        f"training_rows={len(train_idx)} source_test_rows={len(test_idx)} "
        f"target_eval_rows={len(X_tgt)} no_data={no_data}"
    )

    metrics = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "dataset_label": cfg.get("dataset_label"),
        "pair": {"source": source, "target": target},
        "regime": regime,
        "label": {"column": label_col, "transform": label_transform, "proxy": label_proxy},
        "features": feature_cols,
        "model": model_cfg,
        "adaptation": {
            "applied": adaptation_applied,
            "config": adaptation_details if adaptation_details is not None else adaptation_cfg,
        },
        "overlap": {
            "run_id": overlap.get("run_id"),
            "overlap_band": overlap.get("overlap_band"),
            "matched_source_n": int(len(src)),
            "matched_target_n": int(len(tgt)),
        },
        "eval": {
            "source_test": None,
            "target": None,
            "target_r2_bootstrap": None,
        },
        "limitations": _limitations(label_col, label_proxy, no_data=no_data),
    }
    metrics["limitations"].append(describe_regime(regime))

    if no_data:
        write_json(exp_dir / "results" / "metrics.json", metrics)
        _write_common_artifacts(exp_dir, repo_root, cfg_path, run_id, used_files)
        log("no data after filters; metrics not computed")
        return 0

    model.fit(X_src.iloc[train_idx], y_src[train_idx])
    y_src_pred = model.predict(X_src.iloc[test_idx])
    y_tgt_pred = model.predict(X_tgt)
    if adaptation_type == "quantile_output":
        y_src_train_pred = model.predict(X_src.iloc[train_idx])
        n_quantiles_used = _effective_quantile_count(
            y_src_train_pred,
            y_tgt_pred,
            int(adaptation_cfg.get("n_quantiles", 100)),
        )
        y_tgt_pred = _quantile_output_correct(
            y_src_train_pred,
            y_tgt_pred,
            n_quantiles_used,
        )
        metrics["adaptation"]["config"]["n_quantiles_used"] = n_quantiles_used

    metrics["eval"] = {
        "source_test": _evaluate(y_src[test_idx], y_src_pred),
        "target": _evaluate(y_tgt, y_tgt_pred),
        "target_r2_bootstrap": _bootstrap_r2(y_tgt, y_tgt_pred, n_boot=n_boot, seed=seed),
    }
    write_json(exp_dir / "results" / "metrics.json", metrics)

    src_pred_df = pd.DataFrame(
        {
            "jid": src.iloc[test_idx]["jid"].astype("string").to_numpy(),
            "y_true_log": y_src[test_idx],
            "y_pred_log": y_src_pred,
        }
    )
    tgt_pred_df = pd.DataFrame(
        {
            "jid": tgt["jid"].astype("string").to_numpy(),
            "y_true_log": y_tgt,
            "y_pred_log": y_tgt_pred,
        }
    )
    src_pred_df.to_parquet(exp_dir / "results" / "predictions_source_test.parquet", index=False)
    tgt_pred_df.to_parquet(exp_dir / "results" / "predictions_target.parquet", index=False)

    _write_common_artifacts(exp_dir, repo_root, cfg_path, run_id, used_files)
    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
