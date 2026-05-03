#!/usr/bin/env python3
"""Compute a per-cluster feature inventory on sampled, job-level parquet data."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

from fresco_data_loader import (
    build_file_records,
    capture_environment_artifacts,
    git_info,
    load_manifest_rows,
    read_job_level_frame,
    resolve_path,
    sample_input_specs,
    utc_now_iso,
    write_json,
)


def _collect_input_rows(
    cfg: dict,
    repo_root: Path,
    seed: int,
) -> tuple[list[dict], list[str], str]:
    if "inputs" in cfg:
        clusters = [spec["cluster"] for spec in cfg["inputs"]]
        return sample_input_specs(cfg["inputs"], repo_root, seed), clusters, "inputs"

    if "inputs_manifest" in cfg:
        rows = load_manifest_rows(cfg["inputs_manifest"], repo_root)
        clusters = list(cfg.get("clusters") or [])
        if not clusters:
            clusters = sorted({str(row["cluster"]) for row in rows if row.get("cluster")})
        if not clusters:
            raise ValueError(
                "Feature-matrix configs using inputs_manifest must provide clusters when manifest rows omit cluster."
            )
        return rows, clusters, "inputs_manifest"

    raise ValueError("Config must define either 'inputs' or 'inputs_manifest'.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    cfg_path = resolve_path(args.config, repo_root)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    run_id = cfg["run_id"]
    exp_dir = (repo_root / "experiments" / run_id).resolve()
    for directory in ["logs", "results", "manifests", "validation"]:
        (exp_dir / directory).mkdir(parents=True, exist_ok=True)

    log_path = exp_dir / "logs" / "feature_matrix.log"

    def log(message: str) -> None:
        line = f"[{utc_now_iso()}] {message}"
        print(line)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    seed = int(cfg.get("random_seed", 1337))
    random.seed(seed)

    input_rows, clusters, input_mode = _collect_input_rows(cfg, repo_root, seed)
    max_rows_cfg = cfg.get("max_rows_per_cluster")
    max_rows = int(max_rows_cfg) if max_rows_cfg not in (None, "", 0) else None
    sample_n_row_groups = int(cfg.get("sample_n_row_groups_per_file", 0) or 0) or None

    log(f"run_id={run_id}")
    log(f"config={cfg_path}")
    log(f"input_mode={input_mode}")
    log(f"clusters={clusters}")
    log(f"max_rows_per_cluster={max_rows}")
    log(f"sample_n_row_groups_per_file={sample_n_row_groups}")

    per_cluster_frames: dict[str, object] = {}
    per_cluster_meta: dict[str, dict] = {}
    input_manifest: list[dict] = []
    hash_cache: dict[str, str] = {}

    for offset, cluster in enumerate(clusters):
        frame, meta = read_job_level_frame(
            manifest_rows=input_rows,
            cluster=cluster,
            columns=None,
            max_rows=max_rows,
            seed=seed + offset,
            sample_n_row_groups_per_file=sample_n_row_groups,
        )
        if meta["raw_rows_sampled"] == 0:
            raise FileNotFoundError(f"No sampled rows available for cluster={cluster}")
        per_cluster_frames[cluster] = frame
        per_cluster_meta[cluster] = meta
        input_manifest.extend(
            build_file_records(meta["used_paths"], cluster=cluster, hash_cache=hash_cache)
        )
        log(
            f"{cluster}: raw_rows_sampled={meta['raw_rows_sampled']} "
            f"job_rows={meta['job_rows']} files_used={len(meta['used_paths'])} "
            f"row_groups_read={meta['row_groups_read']}"
        )

    union_cols = set().union(*(set(frame.columns) for frame in per_cluster_frames.values()))
    intersection_cols = set(union_cols)
    for cluster in clusters:
        intersection_cols &= set(per_cluster_frames[cluster].columns)

    missingness_mean_by_cluster: dict[str, dict[str, float]] = {}
    dtype_by_cluster: dict[str, dict[str, list[str]]] = {}
    job_rows_profiled: dict[str, int] = {}
    raw_rows_sampled: dict[str, int] = {}
    row_groups_sampled: dict[str, int] = {}
    n_files: dict[str, int] = {}

    for cluster in clusters:
        frame = per_cluster_frames[cluster]
        meta = per_cluster_meta[cluster]
        job_rows_profiled[cluster] = int(len(frame))
        raw_rows_sampled[cluster] = int(meta["raw_rows_sampled"])
        row_groups_sampled[cluster] = int(meta["row_groups_read"])
        n_files[cluster] = int(len(meta["used_paths"]))

        dtype_by_cluster[cluster] = {
            column: [str(frame[column].dtype)] for column in frame.columns
        }

        missingness_mean_by_cluster[cluster] = {}
        for column in sorted(union_cols):
            if column not in frame.columns:
                missingness_mean_by_cluster[cluster][column] = 1.0
            else:
                missingness_mean_by_cluster[cluster][column] = (
                    float(frame[column].isna().mean()) if len(frame) > 0 else 1.0
                )

    cutoff = float(cfg.get("missingness_safe_cutoff", 0.0))
    safe_cols = [
        column
        for column in sorted(intersection_cols)
        if all(
            missingness_mean_by_cluster[cluster].get(column, 1.0) <= cutoff
            for cluster in clusters
        )
    ]

    results = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "dataset_label": cfg.get("dataset_label"),
        "random_seed": seed,
        "missingness_safe_cutoff": cutoff,
        "clusters": clusters,
        "n_files": n_files,
        "raw_rows_sampled": raw_rows_sampled,
        "job_rows_profiled": job_rows_profiled,
        "row_groups_sampled": row_groups_sampled,
        "union_columns": sorted(union_cols),
        "intersection_columns": sorted(intersection_cols),
        "safe_columns": safe_cols,
        "dtype_by_cluster": dtype_by_cluster,
        "missingness_mean_by_cluster": missingness_mean_by_cluster,
        "limitations": [
            "Union/intersection/missingness are computed on sampled job-level frames, not the full raw corpus.",
            "When only raw time-slice value_* columns are present, *_cnt/*_sum/*_max and runtime-derived columns are materialized at analysis time.",
        ],
    }
    write_json(exp_dir / "results" / "feature_matrix.json", results)

    metadata = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "script": str((repo_root / "scripts" / "feature_matrix.py").resolve()),
        "config": str(cfg_path),
        "git": git_info(repo_root),
        "python": sys.version.replace("\n", " "),
        "cwd": os.getcwd(),
        "input_mode": input_mode,
    }
    write_json(exp_dir / "manifests" / "run_metadata.json", metadata)
    write_json(exp_dir / "manifests" / "input_files.json", input_manifest)

    capture_environment_artifacts(
        exp_dir / "validation",
        cwd=repo_root,
        include_conda_env=False,
        include_host_info=False,
    )

    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
