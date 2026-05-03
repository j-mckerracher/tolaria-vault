#!/usr/bin/env python3
"""Phase 2: overlap-aware regime matching on proxy or authoritative v3 inputs."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
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

def _ks(a: pd.Series, b: pd.Series) -> float | None:
    a_values = pd.to_numeric(a, errors="coerce").dropna().to_numpy()
    b_values = pd.to_numeric(b, errors="coerce").dropna().to_numpy()
    if len(a_values) == 0 or len(b_values) == 0:
        return None
    return float(ks_2samp(a_values, b_values, alternative="two-sided", mode="asymp").statistic)


def _write_empty_outputs(
    exp_dir: Path,
    run_id: str,
    cfg_path: Path,
    repo_root: Path,
    cfg: dict,
    source: str,
    target: str,
    feature_cols: list[str],
    overlap_band: list[float],
    n_source: int,
    n_target: int,
    notes: list[str],
    used_files: list[dict],
) -> None:
    report = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "dataset_label": cfg.get("dataset_label"),
        "source_cluster": source,
        "target_cluster": target,
        "regime": cfg.get("regime", "cpu_standard"),
        "feature_columns": feature_cols,
        "overlap_band": overlap_band,
        "n_source": int(n_source),
        "n_target": int(n_target),
        "n_source_overlap": 0,
        "n_target_overlap": 0,
        "target_overlap_coverage": 0.0,
        "domain_classifier_auc": None,
        "ks_by_feature_all": {feature: None for feature in feature_cols},
        "ks_by_feature_overlap": {feature: None for feature in feature_cols},
        "notes": notes,
    }
    write_json(exp_dir / "results" / "overlap_report.json", report)

    empty = pd.DataFrame(
        {
            "jid": pd.Series(dtype="string"),
            "cluster": pd.Series(dtype="string"),
            "propensity_source": pd.Series(dtype="float64"),
            "in_overlap": pd.Series(dtype="bool"),
        }
    )
    empty.to_parquet(exp_dir / "results" / "matched_indices.parquet", index=False)
    empty.to_parquet(exp_dir / "results" / "matched_source_indices.parquet", index=False)
    empty.to_parquet(exp_dir / "results" / "matched_target_indices.parquet", index=False)

    metadata = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "script": str((repo_root / "scripts" / "regime_matching.py").resolve()),
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

    log_path = exp_dir / "logs" / "regime_matching.log"

    def log(message: str) -> None:
        line = f"[{utc_now_iso()}] {message}"
        print(line)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    seed = int(cfg.get("random_seed", 1337))
    random.seed(seed)
    np.random.seed(seed)

    source = cfg["source_cluster"]
    target = cfg["target_cluster"]
    feature_cols = list(cfg["feature_columns"])
    overlap_lo, overlap_hi = cfg.get("overlap_band", [0.2, 0.8])
    max_rows = int(cfg.get("max_rows_per_cluster", 200000))
    sample_n_row_groups = int(cfg.get("sample_n_row_groups_per_file", 0) or 0) or None
    sampling_plan_cfg = cfg.get("sampling_plan_path")

    manifest_rows = load_manifest_rows(cfg["inputs_manifest"], repo_root)
    needed = ["jid"] + sorted(
        set(feature_cols + regime_required_columns(cfg.get("regime", "cpu_standard")))
    )

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

    log(f"run_id={run_id}")
    log(f"config={cfg_path}")
    log(f"source={source} target={target} regime={cfg.get('regime')}")
    log(f"features={feature_cols}")
    log(f"overlap_band=[{overlap_lo},{overlap_hi}] max_rows_per_cluster={max_rows}")
    log(f"sample_n_row_groups_per_file={sample_n_row_groups}")
    if sampling_plan_path is not None:
        log(f"sampling_plan_path={sampling_plan_path}")

    src, src_meta = read_job_level_frame(
        manifest_rows=manifest_rows,
        cluster=source,
        columns=needed,
        max_rows=max_rows,
        seed=seed,
        sample_n_row_groups_per_file=sample_n_row_groups,
        row_group_plan=source_sampling_plan,
        plan_seed=source_sampling_seed,
    )
    tgt, tgt_meta = read_job_level_frame(
        manifest_rows=manifest_rows,
        cluster=target,
        columns=needed,
        max_rows=max_rows,
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

    regime = cfg.get("regime", "cpu_standard")
    src = src.loc[regime_mask(src, regime)].copy()
    tgt = tgt.loc[regime_mask(tgt, regime)].copy()

    log(f"source_rows_after_regime={len(src)} target_rows_after_regime={len(tgt)}")
    regime_note = describe_regime(regime)

    hash_cache: dict[str, str] = {}
    used_files = build_file_records(src_meta["used_paths"], source, hash_cache=hash_cache)
    used_files.extend(build_file_records(tgt_meta["used_paths"], target, hash_cache=hash_cache))
    if sampling_plan_path is not None:
        used_files.extend(build_file_records([sampling_plan_path], "sampling_plan", hash_cache=hash_cache))

    if len(src) == 0 or len(tgt) == 0:
        _write_empty_outputs(
            exp_dir=exp_dir,
            run_id=run_id,
            cfg_path=cfg_path,
            repo_root=repo_root,
            cfg=cfg,
            source=source,
            target=target,
            feature_cols=feature_cols,
            overlap_band=[overlap_lo, overlap_hi],
            n_source=len(src),
            n_target=len(tgt),
            notes=[
                        "Propensity model was not trained because one side had zero rows after sampling and regime filtering.",
                        regime_note,
                    ],
                    used_files=used_files,
                )
        log("no rows after filtering; wrote empty overlap artifacts")
        return 0

    src["domain"] = 1
    tgt["domain"] = 0
    combined = pd.concat([src, tgt], ignore_index=True)
    y = combined.pop("domain").astype(int).to_numpy()

    jid = combined["jid"].astype("string")
    X = combined[feature_cols].copy()
    for column in feature_cols:
        X[column] = pd.to_numeric(X[column], errors="coerce")

    numeric_features = feature_cols
    model = Pipeline(
        steps=[
            (
                "prep",
                ColumnTransformer(
                    transformers=[
                        (
                            "num",
                            Pipeline(
                                steps=[
                                    ("impute", SimpleImputer(strategy="median")),
                                    ("scale", StandardScaler()),
                                ]
                            ),
                            numeric_features,
                        )
                    ],
                    remainder="drop",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=float(cfg.get("propensity_model", {}).get("C", 1.0)),
                    max_iter=int(cfg.get("propensity_model", {}).get("max_iter", 2000)),
                    class_weight=cfg.get("propensity_model", {}).get("class_weight", "balanced"),
                    solver="lbfgs",
                ),
            ),
        ]
    )

    log("training domain classifier...")
    model.fit(X, y)

    proba_src = model.predict_proba(X)[:, 1]
    auc = float(roc_auc_score(y, proba_src))
    in_overlap = (proba_src >= float(overlap_lo)) & (proba_src <= float(overlap_hi))

    is_source = y == 1
    is_target = y == 0
    n_source = int(is_source.sum())
    n_target = int(is_target.sum())
    n_source_overlap = int(in_overlap[is_source].sum())
    n_target_overlap = int(in_overlap[is_target].sum())
    target_covered = float(n_target_overlap / n_target) if n_target > 0 else 0.0

    src_overlap_mask = pd.Series(in_overlap[is_source], index=src.index)
    tgt_overlap_mask = pd.Series(in_overlap[is_target], index=tgt.index)
    ks_all = {feature: _ks(src[feature], tgt[feature]) for feature in feature_cols}
    ks_overlap = {
        feature: _ks(src.loc[src_overlap_mask, feature], tgt.loc[tgt_overlap_mask, feature])
        for feature in feature_cols
    }

    report = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "dataset_label": cfg.get("dataset_label"),
        "source_cluster": source,
        "target_cluster": target,
        "regime": regime,
        "feature_columns": feature_cols,
        "overlap_band": [overlap_lo, overlap_hi],
        "n_source": n_source,
        "n_target": n_target,
        "n_source_overlap": n_source_overlap,
        "n_target_overlap": n_target_overlap,
        "target_overlap_coverage": target_covered,
        "domain_classifier_auc": auc,
        "ks_by_feature_all": ks_all,
        "ks_by_feature_overlap": ks_overlap,
        "notes": [
            "Propensity model is trained on sampled job-level frames aggregated from parquet inputs.",
            regime_note,
        ],
    }
    write_json(exp_dir / "results" / "overlap_report.json", report)

    out_df = pd.DataFrame(
        {
            "jid": jid,
            "cluster": np.where(is_source, source, target),
            "propensity_source": proba_src,
            "in_overlap": in_overlap,
        }
    )
    out_df.to_parquet(exp_dir / "results" / "matched_indices.parquet", index=False)
    out_df.loc[is_source & in_overlap].to_parquet(
        exp_dir / "results" / "matched_source_indices.parquet", index=False
    )
    out_df.loc[is_target & in_overlap].to_parquet(
        exp_dir / "results" / "matched_target_indices.parquet", index=False
    )

    metadata = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "script": str((repo_root / "scripts" / "regime_matching.py").resolve()),
        "config": str(cfg_path),
        "git": git_info(repo_root),
        "python": sys.version.replace("\n", " "),
        "cwd": os.getcwd(),
    }
    write_json(exp_dir / "manifests" / "run_metadata.json", metadata)
    write_json(exp_dir / "manifests" / "input_files_used.json", used_files)
    capture_environment_artifacts(exp_dir / "validation", cwd=repo_root)

    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
