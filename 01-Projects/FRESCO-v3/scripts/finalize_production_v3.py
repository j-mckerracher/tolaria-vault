#!/usr/bin/env python3
"""Backfill validation, manifests, and reproducibility artifacts for an existing v3 build."""

from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from fresco_data_loader import (
    capture_environment_artifacts,
    load_manifest_rows_with_format,
    resolve_path,
    sha256_file,
    utc_now_iso,
    write_json,
    write_manifest_rows,
)


CANONICAL_ARROW_TYPES = {
    "jid": "string",
    "jid_global": "string",
    "cluster": "string",
    "username": "string",
    "account": "string",
    "jobname": "string",
    "nhosts": "int64",
    "ncores": "int64",
    "timelimit_sec": "double",
    "timelimit": "double",
    "timelimit_original": "double",
    "timelimit_unit_original": "string",
    "queue": "string",
    "host": "string",
    "host_list": "string",
    "exitcode": "string",
    "unit": "string",
    "time": "timestamp[us]",
    "submit_time": "timestamp[us]",
    "start_time": "timestamp[us]",
    "end_time": "timestamp[us]",
    "value_cpuuser": "double",
    "value_gpu": "double",
    "value_memused": "double",
    "value_memused_minus_diskcache": "double",
    "value_nfs": "double",
    "value_block": "double",
    "memory_includes_cache": "bool",
    "memory_collection_method": "string",
    "memory_aggregation": "string",
    "memory_sampling_interval_sec": "double",
}


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _infer_manifest_path(output_root: Path, basename: str) -> Path:
    jsonl_path = output_root / "manifests" / f"{basename}.jsonl"
    if jsonl_path.exists():
        return jsonl_path
    json_path = output_root / "manifests" / f"{basename}.json"
    if json_path.exists():
        return json_path
    return jsonl_path


def _pick_output_file(
    output_root: Path,
    run_id: str,
    output_manifest_rows: list[dict[str, Any]],
    explicit_output_path: str | None,
    repo_root: Path,
) -> Path:
    if explicit_output_path:
        return resolve_path(explicit_output_path, repo_root)
    if output_manifest_rows:
        for row in output_manifest_rows:
            path = Path(row["path"])
            if path.exists():
                return path
    return output_root / f"{run_id}_v3.parquet"


def _manifest_entry_size(entry: dict[str, Any]) -> int | None:
    value = entry.get("size_bytes", entry.get("bytes"))
    if value in (None, ""):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _enrich_manifest_rows(
    rows: list[dict[str, Any]],
    extra_by_path: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        row_copy = dict(row)
        path_text = row_copy.get("path")
        if path_text:
            path = Path(path_text)
            if path.exists():
                row_copy.setdefault("sha256", sha256_file(path))
                if "size_bytes" in row_copy:
                    row_copy["size_bytes"] = int(row_copy["size_bytes"])
                elif "bytes" in row_copy:
                    row_copy["bytes"] = int(row_copy["bytes"])
                else:
                    row_copy["size_bytes"] = int(path.stat().st_size)
        if extra_by_path and path_text in extra_by_path:
            row_copy.update(extra_by_path[path_text])
        enriched.append(row_copy)
    return enriched


def _stream_validation(output_file: Path, expected_clusters: list[str]) -> tuple[dict, dict, dict, dict]:
    parquet_file = pq.ParquetFile(str(output_file))
    schema = parquet_file.schema_arrow
    schema_types = {field.name: str(field.type) for field in schema}
    column_names = list(schema.names)

    missing_required_columns = sorted(
        column for column in CANONICAL_ARROW_TYPES if column not in schema_types
    )
    dtype_mismatches = {
        column: {
            "expected": CANONICAL_ARROW_TYPES[column],
            "observed": schema_types[column],
        }
        for column in CANONICAL_ARROW_TYPES
        if column in schema_types and CANONICAL_ARROW_TYPES[column] != schema_types[column]
    }

    total_rows = int(parquet_file.metadata.num_rows)
    global_missing = {column: 0 for column in column_names}
    cluster_missing: dict[str, dict[str, int]] = {}
    cluster_counts: dict[str, int] = {}
    pandas_dtypes: dict[str, set[str]] = {column: set() for column in column_names}
    observed_clusters: set[str] = set()

    violations = {
        "missing_jid_rows": 0,
        "missing_cluster_rows": 0,
        "unexpected_cluster_rows": 0,
        "negative_timelimit_sec_rows": 0,
        "negative_runtime_sec_rows": 0,
        "negative_queue_time_sec_rows": 0,
        "runtime_fraction_gt_1_05_rows": 0,
        "start_after_end_rows": 0,
        "submit_after_start_rows": 0,
    }

    for row_group in range(parquet_file.num_row_groups):
        df = parquet_file.read_row_group(row_group).to_pandas()

        for column in column_names:
            if column in df.columns:
                pandas_dtypes[column].add(str(df[column].dtype))
                global_missing[column] += int(df[column].isna().sum())
            else:
                global_missing[column] += int(len(df))

        if "cluster" in df.columns:
            cluster_values = df["cluster"].astype("string").fillna("unknown")
            observed_clusters.update(c for c in cluster_values.unique().tolist() if c not in (None, "unknown"))
        else:
            cluster_values = pd.Series(["unknown"] * len(df), index=df.index, dtype="string")

        if "jid" in df.columns:
            violations["missing_jid_rows"] += int(df["jid"].isna().sum())
        if "cluster" in df.columns:
            violations["missing_cluster_rows"] += int(df["cluster"].isna().sum())
            if expected_clusters:
                violations["unexpected_cluster_rows"] += int(
                    (~cluster_values.isin(expected_clusters) & cluster_values.ne("unknown")).sum()
                )

        if "timelimit_sec" in df.columns:
            timelimit = pd.to_numeric(df["timelimit_sec"], errors="coerce")
            violations["negative_timelimit_sec_rows"] += int((timelimit < 0).sum())
        else:
            timelimit = pd.Series(np.nan, index=df.index, dtype="float64")

        if "start_time" in df.columns and "end_time" in df.columns:
            start_time = pd.to_datetime(df["start_time"], errors="coerce")
            end_time = pd.to_datetime(df["end_time"], errors="coerce")
            runtime = (end_time - start_time).dt.total_seconds()
            violations["negative_runtime_sec_rows"] += int((runtime < 0).sum())
            violations["start_after_end_rows"] += int((start_time > end_time).sum())
            if "timelimit_sec" in df.columns:
                violations["runtime_fraction_gt_1_05_rows"] += int(
                    ((timelimit > 0) & ((runtime / timelimit) > 1.05)).sum()
                )
        else:
            start_time = pd.Series(pd.NaT, index=df.index)
            runtime = pd.Series(np.nan, index=df.index, dtype="float64")

        if "submit_time" in df.columns and "start_time" in df.columns:
            submit_time = pd.to_datetime(df["submit_time"], errors="coerce")
            queue_time = (start_time - submit_time).dt.total_seconds()
            violations["negative_queue_time_sec_rows"] += int((queue_time < 0).sum())
            violations["submit_after_start_rows"] += int((submit_time > start_time).sum())

        unique_clusters = cluster_values.unique().tolist()
        for cluster_name in unique_clusters:
            if cluster_name is None:
                cluster_name = "unknown"
            mask = cluster_values == cluster_name
            cluster_df = df.loc[mask]
            cluster_counts[str(cluster_name)] = cluster_counts.get(str(cluster_name), 0) + int(len(cluster_df))
            miss = cluster_missing.setdefault(
                str(cluster_name),
                {column: 0 for column in column_names},
            )
            for column in column_names:
                if column in cluster_df.columns:
                    miss[column] += int(cluster_df[column].isna().sum())
                else:
                    miss[column] += int(len(cluster_df))

    dtype_report = {
        "run_id": None,
        "created_utc": utc_now_iso(),
        "output_parquet": str(output_file),
        "row_group_count": int(parquet_file.num_row_groups),
        "total_rows": total_rows,
        "schema": schema_types,
        "required_columns_present": sorted(column for column in CANONICAL_ARROW_TYPES if column in schema_types),
        "missing_required_columns": missing_required_columns,
        "dtype_mismatches": dtype_mismatches,
        "pandas_dtypes_observed": {
            column: sorted(values) for column, values in pandas_dtypes.items()
        },
    }

    missingness_report = {
        "created_utc": utc_now_iso(),
        "output_parquet": str(output_file),
        "total_rows": total_rows,
        "per_cluster_row_counts": cluster_counts,
        "global_missingness": {
            column: (global_missing[column] / total_rows if total_rows > 0 else None)
            for column in column_names
        },
        "per_cluster_missingness": {
            cluster_name: {
                column: (
                    cluster_missing[cluster_name][column] / cluster_counts[cluster_name]
                    if cluster_counts[cluster_name] > 0
                    else None
                )
                for column in column_names
            }
            for cluster_name in sorted(cluster_counts)
        },
    }

    sanity_report = {
        "created_utc": utc_now_iso(),
        "output_parquet": str(output_file),
        "counts": {
            "row_group_count": int(parquet_file.num_row_groups),
            "total_rows": total_rows,
            "column_count": len(column_names),
            "cluster_row_counts": cluster_counts,
        },
        "expected_clusters": expected_clusters,
        "observed_clusters": sorted(observed_clusters),
        "violations": violations,
        "checks": {
            "required_columns_present": len(missing_required_columns) == 0,
            "expected_clusters_only": violations["unexpected_cluster_rows"] == 0,
            "timestamp_columns_us": all(
                schema_types.get(column) == "timestamp[us]"
                for column in ["time", "submit_time", "start_time", "end_time"]
                if column in schema_types
            ),
            "no_negative_durations": (
                violations["negative_runtime_sec_rows"] == 0
                and violations["negative_queue_time_sec_rows"] == 0
                and violations["start_after_end_rows"] == 0
                and violations["submit_after_start_rows"] == 0
            ),
        },
    }

    schema_report = {
        "created_utc": utc_now_iso(),
        "row_count": total_rows,
        "column_count": len(column_names),
        "row_group_count": int(parquet_file.num_row_groups),
        "clusters_present": sorted(observed_clusters),
        "schema": schema_types,
        "missing_required_columns": missing_required_columns,
        "dtype_mismatches": dtype_mismatches,
    }

    return dtype_report, missingness_report, sanity_report, schema_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default=None)
    parser.add_argument("--output-parquet", default=None)
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--output-manifest", default=None)
    parser.add_argument("--started-at", default=None)
    parser.add_argument("--completed-at", default=None)
    parser.add_argument("--pipeline-git-commit", default=None)
    parser.add_argument("--slurm-job-id", default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    cfg_path = resolve_path(args.config, repo_root)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    run_id = cfg["run_id"]
    input_root_value = cfg.get("input_root", cfg.get("input_dir"))
    output_root_value = args.output_root or cfg.get("output_root", cfg.get("output_dir"))
    if not output_root_value:
        raise ValueError("Could not determine output root from config or --output-root.")

    input_root = resolve_path(input_root_value, repo_root) if input_root_value else None
    output_root = resolve_path(output_root_value, repo_root)
    manifests_dir = output_root / "manifests"
    validation_dir = output_root / "validation"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    input_manifest_path = (
        resolve_path(args.input_manifest, repo_root)
        if args.input_manifest
        else _infer_manifest_path(output_root, "input_manifest")
    )
    output_manifest_path = (
        resolve_path(args.output_manifest, repo_root)
        if args.output_manifest
        else _infer_manifest_path(output_root, "output_manifest")
    )

    input_rows: list[dict[str, Any]] = []
    output_rows: list[dict[str, Any]] = []
    input_manifest_format = "jsonl"
    output_manifest_format = "jsonl"

    if input_manifest_path.exists():
        input_rows, input_manifest_format, input_manifest_path = load_manifest_rows_with_format(
            input_manifest_path, repo_root
        )
    if output_manifest_path.exists():
        output_rows, output_manifest_format, output_manifest_path = load_manifest_rows_with_format(
            output_manifest_path, repo_root
        )

    output_file = _pick_output_file(
        output_root=output_root,
        run_id=run_id,
        output_manifest_rows=output_rows,
        explicit_output_path=args.output_parquet,
        repo_root=repo_root,
    )
    if not output_file.exists():
        raise FileNotFoundError(f"Output parquet not found: {output_file}")

    dtype_report, missingness_report, sanity_report, schema_report = _stream_validation(
        output_file=output_file,
        expected_clusters=list(cfg.get("clusters", [])),
    )
    dtype_report["run_id"] = run_id
    missingness_report["run_id"] = run_id
    sanity_report["run_id"] = run_id
    schema_report["run_id"] = run_id

    write_json(validation_dir / "dtype_report.json", dtype_report)
    write_json(validation_dir / "missingness_report.json", missingness_report)
    write_json(validation_dir / "sanity_checks.json", sanity_report)
    write_json(validation_dir / "schema_report.json", schema_report)

    environment = capture_environment_artifacts(
        validation_dir,
        cwd=repo_root,
        include_conda_env=True,
        include_host_info=True,
    )

    output_size = int(output_file.stat().st_size)
    output_hash = sha256_file(output_file)
    extra_output_fields = {
        str(output_file): {
            "path": str(output_file),
            "row_count": int(dtype_report["total_rows"]),
            "sha256": output_hash,
            "size_bytes": output_size,
            "clusters": sanity_report["observed_clusters"],
        }
    }
    if output_rows:
        output_rows = _enrich_manifest_rows(output_rows, extra_by_path=extra_output_fields)
    else:
        output_rows = [
            {
                "path": str(output_file),
                "row_count": int(dtype_report["total_rows"]),
                "size_bytes": output_size,
                "sha256": output_hash,
                "clusters": sanity_report["observed_clusters"],
                "written_at": utc_now_iso(),
            }
        ]

    if input_rows:
        input_rows = _enrich_manifest_rows(input_rows)

    write_manifest_rows(input_manifest_path, input_rows, input_manifest_format)
    write_manifest_rows(output_manifest_path, output_rows, output_manifest_format)

    existing_metadata_path = manifests_dir / "run_metadata.json"
    existing_metadata = _load_json_if_exists(existing_metadata_path)
    completed_at = args.completed_at or existing_metadata.get("completed_at") or utc_now_iso()
    started_at = args.started_at or existing_metadata.get("started_at")
    pipeline_git_commit = (
        args.pipeline_git_commit
        or existing_metadata.get("pipeline_git_commit")
        or existing_metadata.get("git_commit")
        or "unknown"
    )
    slurm_job_id = args.slurm_job_id or os.environ.get("SLURM_JOB_ID")

    run_metadata = {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "config_path": str(cfg_path),
        "config_sha256": sha256_file(cfg_path),
        "config": cfg,
        "input_root": str(input_root) if input_root else None,
        "output_root": str(output_root),
        "output_parquet": str(output_file),
        "manifests": {
            "input_manifest": str(input_manifest_path),
            "output_manifest": str(output_manifest_path),
        },
        "validation_artifacts": {
            "dtype_report": str(validation_dir / "dtype_report.json"),
            "missingness_report": str(validation_dir / "missingness_report.json"),
            "sanity_checks": str(validation_dir / "sanity_checks.json"),
            "schema_report": str(validation_dir / "schema_report.json"),
            "python_version": str(validation_dir / "python_version.txt"),
            "pip_freeze": str(validation_dir / "pip_freeze.txt"),
            "conda_env": str(validation_dir / "conda_env.yml"),
            "host_info": str(validation_dir / "host_info.txt"),
        },
        "clusters": sanity_report["observed_clusters"] or list(cfg.get("clusters", [])),
        "row_counts": {
            "output_total": int(dtype_report["total_rows"]),
            "output_manifest_total": int(
                sum(int(row.get("row_count", 0) or 0) for row in output_rows)
            ),
            "input_manifest_total": int(
                sum(int(row.get("row_count", 0) or 0) for row in input_rows)
            ),
            "per_cluster": missingness_report["per_cluster_row_counts"],
        },
        "file_counts": {
            "input_manifest_entries": len(input_rows),
            "output_manifest_entries": len(output_rows),
        },
        "file_sizes": {
            "output_bytes": output_size,
            "input_manifest_total_bytes": int(
                sum(_manifest_entry_size(row) or 0 for row in input_rows)
            ),
        },
        "python_version": environment["python_version"],
        "python_executable": environment["python_executable"],
        "conda_env": environment.get("conda_env"),
        "host": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
        },
        "slurm_job_id": slurm_job_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "pipeline_git_commit": pipeline_git_commit,
        "git_commit": pipeline_git_commit,
    }
    write_json(existing_metadata_path, run_metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
