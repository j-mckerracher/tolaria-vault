#!/usr/bin/env python3
"""Shared manifest loading, sampling, aggregation, and provenance helpers."""

from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import os
import platform
import random
import re
import socket
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


RAW_METRIC_AGG_SUFFIXES = ("_cnt", "_sum", "_max")
KNOWN_DATETIME_COLUMNS = {"time", "submit_time", "start_time", "end_time"}
KNOWN_BOOL_COLUMNS = {"memory_includes_cache"}
KNOWN_STRING_COLUMNS = {
    "jid",
    "jid_global",
    "cluster",
    "username",
    "account",
    "jobname",
    "timelimit_unit_original",
    "queue",
    "partition",
    "host",
    "host_list",
    "node_type",
    "gpu_model",
    "exitcode",
    "unit",
    "memory_collection_method",
    "memory_aggregation",
    "memory_original_unit",
}
KNOWN_NUMERIC_COLUMNS = {
    "nhosts",
    "ncores",
    "node_cores",
    "gpu_count_per_node",
    "timelimit",
    "timelimit_sec",
    "timelimit_original",
    "runtime_sec",
    "queue_time_sec",
    "runtime_fraction",
    "peak_memory_gb",
    "node_memory_gb",
    "peak_memory_fraction",
    "memory_sampling_interval_sec",
    "memory_original_value",
}
HARDWARE_METADATA_COLUMNS = {
    "partition",
    "node_type",
    "node_cores",
    "gpu_count_per_node",
    "gpu_model",
    "node_memory_gb",
}
MEMORY_DERIVED_COLUMNS = {
    "peak_memory_gb",
    "peak_memory_fraction",
    "memory_original_value",
    "memory_original_unit",
}


def utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@lru_cache(maxsize=1)
def _load_clusters_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[1] / "config" / "clusters.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    except OSError as exc:
        return 1, "", str(exc)
    return proc.returncode, proc.stdout, proc.stderr


def git_info(start_dir: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "git_root": None,
        "git_commit": None,
        "git_status_porcelain": None,
    }
    rc, out, _ = run_command(["git", "rev-parse", "--show-toplevel"], start_dir)
    git_root = Path(out.strip()) if rc == 0 and out.strip() else start_dir
    info["git_root"] = str(git_root)

    rc, out, _ = run_command(["git", "rev-parse", "HEAD"], git_root)
    info["git_commit"] = out.strip() if rc == 0 else None

    rc, out, _ = run_command(["git", "status", "--porcelain=v1"], git_root)
    info["git_status_porcelain"] = out if rc == 0 else None
    return info


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _is_absolute_like(path_text: str) -> bool:
    return bool(
        re.match(r"^[A-Za-z]:[\\/]", path_text)
        or path_text.startswith("\\\\")
        or path_text.startswith("/")
    )


def resolve_path(path_value: str | os.PathLike[str], base_dir: Path) -> Path:
    path_text = str(path_value)
    if _is_absolute_like(path_text):
        return Path(path_text)
    return (base_dir / path_text).resolve()


def load_sampling_plan(
    path_value: str | os.PathLike[str], base_dir: Path
) -> tuple[dict[str, Any], Path]:
    resolved_plan = resolve_path(path_value, base_dir)
    payload = json.loads(resolved_plan.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("clusters"), dict):
        raise ValueError(
            f"Invalid sampling plan at {resolved_plan}: expected top-level 'clusters' mapping."
        )
    return payload, resolved_plan


def sampling_plan_entries_for_cluster(
    plan: dict[str, Any], cluster: str | None
) -> list[dict[str, Any]] | None:
    if cluster is None:
        return None
    cluster_payload = plan.get("clusters", {}).get(cluster)
    if cluster_payload is None:
        return None

    entries = cluster_payload.get("entries") if isinstance(cluster_payload, dict) else cluster_payload
    if not isinstance(entries, list):
        raise ValueError(f"Invalid sampling plan for cluster={cluster}: entries must be a list.")

    normalized: list[dict[str, Any]] = []
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or "path" not in entry
            or "row_groups" not in entry
            or not isinstance(entry["row_groups"], list)
        ):
            raise ValueError(
                f"Invalid sampling plan entry for cluster={cluster}: expected path + row_groups."
            )
        normalized.append(
            {
                "path": str(entry["path"]),
                "row_groups": [int(v) for v in entry["row_groups"]],
            }
        )
    return normalized


def sampling_plan_seed_for_cluster(plan: dict[str, Any], cluster: str | None) -> int | None:
    if cluster is None:
        return None
    cluster_payload = plan.get("clusters", {}).get(cluster)
    if not isinstance(cluster_payload, dict):
        return None
    seed = cluster_payload.get("seed")
    return int(seed) if seed is not None else None


def expand_glob_paths(pattern: str, base_dir: Path) -> list[Path]:
    pattern_text = pattern if _is_absolute_like(pattern) else str(base_dir / pattern)
    matches = sorted(Path(p) for p in glob.glob(pattern_text, recursive=True))
    return [p.resolve() for p in matches]


def load_manifest_rows_with_format(
    manifest_path: str | os.PathLike[str], base_dir: Path
) -> tuple[list[dict[str, Any]], str, Path]:
    resolved_manifest = resolve_path(manifest_path, base_dir)
    text = resolved_manifest.read_text(encoding="utf-8").strip()
    if not text:
        return [], "jsonl", resolved_manifest

    manifest_format = "jsonl"
    rows: list[dict[str, Any]]
    if text.startswith("["):
        data = json.loads(text)
        rows = list(data)
        manifest_format = "json"
    elif "\n" not in text and text.startswith("{"):
        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            rows = list(data["entries"])
        elif isinstance(data, dict) and isinstance(data.get("rows"), list):
            rows = list(data["rows"])
        elif isinstance(data, list):
            rows = list(data)
        else:
            rows = [data]
        manifest_format = "json"
    else:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        manifest_format = "jsonl"

    normalized: list[dict[str, Any]] = []
    for row in rows:
        row_copy = dict(row)
        if "path" in row_copy and row_copy["path"]:
            row_copy["path"] = str(resolve_path(row_copy["path"], resolved_manifest.parent))
        normalized.append(row_copy)
    return normalized, manifest_format, resolved_manifest


def load_manifest_rows(
    manifest_path: str | os.PathLike[str], base_dir: Path
) -> list[dict[str, Any]]:
    rows, _, _ = load_manifest_rows_with_format(manifest_path, base_dir)
    return rows


def write_manifest_rows(
    manifest_path: Path, rows: list[dict[str, Any]], manifest_format: str | None = None
) -> None:
    path = Path(manifest_path)
    fmt = manifest_format or ("jsonl" if path.suffix.lower() == ".jsonl" else "json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "jsonl":
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, sort_keys=True) + "\n")
        return
    path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")


def sample_input_specs(
    inputs: list[dict[str, Any]], repo_root: Path, seed: int
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for spec in inputs:
        cluster = spec["cluster"]
        matches = expand_glob_paths(spec["paths_glob"], repo_root)
        if not matches:
            raise FileNotFoundError(
                f"No parquet files matched for {cluster}: {spec['paths_glob']}"
            )

        sample_n = int(spec.get("sample_n_files", 0) or 0)
        if sample_n > 0 and len(matches) > sample_n:
            matches = rng.sample(matches, sample_n)

        for path in matches:
            row = {"cluster": cluster, "path": str(path)}
            if spec.get("label") is not None:
                row["label"] = spec["label"]
            rows.append(row)
    return rows


def select_manifest_rows_for_cluster(
    manifest_rows: list[dict[str, Any]], cluster: str | None
) -> list[dict[str, Any]]:
    if cluster is None:
        return [dict(row) for row in manifest_rows]

    selected: list[dict[str, Any]] = []
    for row in manifest_rows:
        row_cluster = row.get("cluster")
        if row_cluster in (None, "", cluster):
            selected.append(dict(row))
    return selected


def _raw_metric_name(column: str) -> str | None:
    for suffix in RAW_METRIC_AGG_SUFFIXES:
        if column.endswith(suffix):
            base = column[: -len(suffix)]
            if base.startswith("value_"):
                return base
    return None


def _is_raw_metric(column: str) -> bool:
    return column.startswith("value_") and _raw_metric_name(column) is None


def _is_numeric_like(column: str, series: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(series):
        return True
    if column in KNOWN_NUMERIC_COLUMNS:
        return True
    if column.endswith("_sec") or column.endswith("_fraction"):
        return True
    if _is_raw_metric(column) or _raw_metric_name(column) is not None:
        return True
    return False


def _first_non_null(series: pd.Series) -> Any:
    non_null = series.dropna()
    if non_null.empty:
        return pd.NA
    return non_null.iloc[0]


def _schema_union(candidate_rows: list[dict[str, Any]]) -> tuple[list[str], bool]:
    ordered: list[str] = []
    seen: set[str] = set()
    has_cluster_column = False
    for row in candidate_rows:
        pf = pq.ParquetFile(str(Path(row["path"])))
        names = pf.schema_arrow.names
        if "cluster" in names:
            has_cluster_column = True
        for name in names:
            if name not in seen:
                seen.add(name)
                ordered.append(name)
    return ordered, has_cluster_column


def _default_output_columns(schema_columns: list[str]) -> list[str]:
    ordered = list(schema_columns)
    raw_metrics = [col for col in schema_columns if _is_raw_metric(col)]
    for raw_metric in raw_metrics:
        ordered.extend(
            [
                f"{raw_metric}_cnt",
                f"{raw_metric}_sum",
                f"{raw_metric}_max",
            ]
        )
    if {"start_time", "end_time"}.issubset(schema_columns):
        ordered.append("runtime_sec")
    if {"submit_time", "start_time"}.issubset(schema_columns):
        ordered.append("queue_time_sec")
    if {"start_time", "end_time", "timelimit_sec"}.issubset(schema_columns):
        ordered.append("runtime_fraction")
    if "queue" in schema_columns:
        ordered.extend(
            [
                "partition",
                "node_type",
                "node_cores",
                "gpu_count_per_node",
                "gpu_model",
                "node_memory_gb",
            ]
        )
    if "value_memused" in schema_columns:
        ordered.extend(["memory_original_value", "memory_original_unit", "peak_memory_gb"])
    if {"value_memused", "nhosts", "queue"}.issubset(schema_columns):
        ordered.append("peak_memory_fraction")

    deduped: list[str] = []
    seen: set[str] = set()
    for col in ordered:
        if col not in seen:
            seen.add(col)
            deduped.append(col)
    return deduped


def _physical_columns_to_read(
    requested_columns: list[str], schema_columns: list[str], cluster: str | None
) -> list[str]:
    read_columns: list[str] = []
    seen: set[str] = set()
    available = set(schema_columns)

    def add(name: str) -> None:
        if name in available and name not in seen:
            seen.add(name)
            read_columns.append(name)

    add("jid")
    if cluster is not None:
        add("cluster")

    for column in requested_columns:
        if column == "partition":
            add("queue")
            continue
        if column in HARDWARE_METADATA_COLUMNS - {"partition"}:
            add("queue")
            continue
        if column in {"peak_memory_gb", "memory_original_value", "memory_original_unit"}:
            add("value_memused")
            continue
        if column == "peak_memory_fraction":
            add("value_memused")
            add("nhosts")
            add("queue")
            continue
        if column in available:
            add(column)
            continue
        raw_metric = _raw_metric_name(column)
        if raw_metric is not None:
            add(raw_metric)
            continue
        if column == "runtime_sec":
            add("start_time")
            add("end_time")
            continue
        if column == "queue_time_sec":
            add("submit_time")
            add("start_time")
            continue
        if column == "runtime_fraction":
            add("start_time")
            add("end_time")
            add("timelimit_sec")
            continue
        add(column)

    if "cluster" in available and "cluster" not in read_columns and "cluster" in requested_columns:
        add("cluster")
    return read_columns


def _coerce_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    for column in work.columns:
        if column in KNOWN_DATETIME_COLUMNS:
            series = pd.to_datetime(work[column], errors="coerce", utc=True)
            if pd.api.types.is_datetime64tz_dtype(series.dtype):
                series = series.dt.tz_localize(None)
            work[column] = series
        elif column in KNOWN_BOOL_COLUMNS:
            work[column] = work[column].astype("boolean")
        elif column in KNOWN_STRING_COLUMNS:
            work[column] = work[column].astype("string")
        elif _is_numeric_like(column, work[column]):
            work[column] = pd.to_numeric(work[column], errors="coerce")
        else:
            work[column] = work[column].astype("string")
    return work


def regime_required_columns(regime: str | None) -> list[str]:
    if regime in (None, "", "all"):
        return []
    if regime == "cpu_standard":
        return ["value_gpu_cnt", "value_gpu_sum", "value_gpu_max"]
    if regime in {"hardware_cpu_standard", "hardware_cpu_largemem", "hardware_gpu_standard"}:
        return ["gpu_count_per_node", "node_memory_gb", "queue"]
    raise ValueError(f"Unsupported regime: {regime}")


def describe_regime(regime: str | None) -> str:
    if regime in (None, "", "all"):
        return "No regime filter applied."
    if regime == "cpu_standard":
        return (
            "cpu_standard is defined on the aggregated job-level frame as no GPU activity "
            "(prefer value_gpu_max<=0 when available; otherwise fall back to "
            "value_gpu_cnt<=0 and value_gpu_sum<=0)."
        )
    if regime == "hardware_cpu_standard":
        return (
            "hardware_cpu_standard uses recovered hardware metadata from config/clusters.json: "
            "gpu_count_per_node<=0 and node_memory_gb<512, with partition recovered from queue."
        )
    if regime == "hardware_cpu_largemem":
        return (
            "hardware_cpu_largemem uses recovered hardware metadata from config/clusters.json: "
            "gpu_count_per_node<=0 and node_memory_gb>=512, with partition recovered from queue."
        )
    if regime == "hardware_gpu_standard":
        return (
            "hardware_gpu_standard uses recovered hardware metadata from config/clusters.json: "
            "gpu_count_per_node>0, with partition recovered from queue."
        )
    raise ValueError(f"Unsupported regime: {regime}")


def regime_mask(df: pd.DataFrame, regime: str | None) -> pd.Series:
    if regime in (None, "", "all"):
        return pd.Series([True] * len(df), index=df.index)

    if regime == "cpu_standard":
        gpu_max = df.get("value_gpu_max")
        gpu_cnt = df.get("value_gpu_cnt")
        gpu_sum = df.get("value_gpu_sum")
        if gpu_max is not None:
            gpu_max = pd.to_numeric(gpu_max, errors="coerce").fillna(0)
            return gpu_max <= 0
        if gpu_cnt is None and gpu_sum is None:
            return pd.Series([True] * len(df), index=df.index)
        gpu_cnt = pd.to_numeric(gpu_cnt, errors="coerce").fillna(0)
        gpu_sum = pd.to_numeric(gpu_sum, errors="coerce").fillna(0)
        return (gpu_cnt <= 0) & (gpu_sum <= 0)

    gpu_count = pd.to_numeric(df.get("gpu_count_per_node"), errors="coerce")
    node_memory = pd.to_numeric(df.get("node_memory_gb"), errors="coerce")
    if regime == "hardware_cpu_standard":
        return (gpu_count.fillna(0) <= 0) & node_memory.notna() & (node_memory < 512)
    if regime == "hardware_cpu_largemem":
        return (gpu_count.fillna(0) <= 0) & node_memory.notna() & (node_memory >= 512)
    if regime == "hardware_gpu_standard":
        return gpu_count.fillna(0) > 0
    raise ValueError(f"Unsupported regime: {regime}")


def _resolve_hardware_spec(cluster_name: str, partition_name: str | None) -> dict[str, Any]:
    cfg = _load_clusters_config()
    clusters_cfg = cfg.get("clusters", {})
    cluster_cfg = clusters_cfg.get(cluster_name, {})
    spec: dict[str, Any] = dict(cluster_cfg.get("default", {}))
    if partition_name:
        spec.update(cluster_cfg.get("partitions", {}).get(partition_name, {}))
    return spec


def enrich_hardware_metadata(
    df: pd.DataFrame, cluster: str | None = None, requested_columns: list[str] | None = None
) -> pd.DataFrame:
    if df.empty:
        return df

    needs_hardware = requested_columns is None or bool(
        set(requested_columns) & (HARDWARE_METADATA_COLUMNS | MEMORY_DERIVED_COLUMNS)
    )
    if not needs_hardware:
        return df

    out = df.copy()
    if "queue" in out.columns:
        out["partition"] = out["queue"].astype("string")

    cluster_series = (
        out["cluster"].astype("string")
        if "cluster" in out.columns
        else pd.Series([cluster] * len(out), index=out.index, dtype="string")
    )
    partition_series = (
        out["partition"].astype("string")
        if "partition" in out.columns
        else pd.Series([pd.NA] * len(out), index=out.index, dtype="string")
    )

    for column in HARDWARE_METADATA_COLUMNS - {"partition"}:
        if column not in out.columns:
            out[column] = pd.NA

    combos = pd.DataFrame({"cluster": cluster_series, "partition": partition_series}).drop_duplicates()
    for record in combos.to_dict(orient="records"):
        cluster_name = str(record["cluster"]) if pd.notna(record["cluster"]) else ""
        partition_name = str(record["partition"]) if pd.notna(record["partition"]) else None
        spec = _resolve_hardware_spec(cluster_name, partition_name)
        if not spec:
            continue
        mask = cluster_series.eq(cluster_name)
        if partition_name is None:
            mask &= partition_series.isna()
        else:
            mask &= partition_series.eq(partition_name)
        for column in HARDWARE_METADATA_COLUMNS - {"partition"}:
            if column in spec:
                out.loc[mask, column] = spec[column]

    memory_source = None
    if "value_memused_max" in out.columns:
        memory_source = pd.to_numeric(out["value_memused_max"], errors="coerce")
    elif "value_memused" in out.columns:
        memory_source = pd.to_numeric(out["value_memused"], errors="coerce")

    if memory_source is not None:
        out["memory_original_value"] = memory_source.astype("float64")
        original_unit = "GB"
        peak_memory_gb = memory_source.astype("float64")
        observed = peak_memory_gb.dropna()
        if not observed.empty and float(observed.quantile(0.95)) > 1e6:
            peak_memory_gb = peak_memory_gb / float(1024**3)
            original_unit = "bytes"
        out["memory_original_unit"] = pd.Series(
            np.where(memory_source.notna(), original_unit, pd.NA), index=out.index, dtype="string"
        )
        out["peak_memory_gb"] = peak_memory_gb

    if {
        "peak_memory_gb",
        "node_memory_gb",
        "nhosts",
    }.issubset(out.columns):
        peak = pd.to_numeric(out["peak_memory_gb"], errors="coerce").astype("float64")
        node_memory = pd.to_numeric(out["node_memory_gb"], errors="coerce").astype("float64")
        hosts = pd.to_numeric(out["nhosts"], errors="coerce").astype("float64")
        denom = node_memory * hosts
        out["peak_memory_fraction"] = np.where(denom > 0, peak / denom, np.nan)

    for column in {"partition", "node_type", "gpu_model", "memory_original_unit"}:
        if column in out.columns:
            out[column] = out[column].astype("string")
    for column in {"node_cores", "gpu_count_per_node"}:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce").astype("Int64")
    for column in {"node_memory_gb", "peak_memory_gb", "peak_memory_fraction", "memory_original_value"}:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce").astype("float64")
    return out


def collapse_to_job_level(
    df: pd.DataFrame,
    requested_columns: list[str] | None = None,
    cluster: str | None = None,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=requested_columns or [])
    if "jid" not in df.columns:
        out = df.copy()
        for col in requested_columns or []:
            if col not in out.columns:
                out[col] = pd.NA
        return out[requested_columns] if requested_columns else out

    work = df.copy()
    work["jid"] = work["jid"].astype("string")
    if "cluster" in work.columns:
        work["cluster"] = work["cluster"].astype("string")

    group_keys = ["jid"]
    if cluster is None and "cluster" in work.columns:
        group_keys = ["cluster", "jid"]

    work = _coerce_for_aggregation(work)

    agg_map: dict[str, str | Any] = {}
    raw_metrics: list[str] = []
    for column in work.columns:
        if column in group_keys:
            continue
        if _is_raw_metric(column):
            raw_metrics.append(column)
            agg_map[column] = "max"
        elif column in KNOWN_DATETIME_COLUMNS:
            agg_map[column] = "min" if column in {"submit_time", "start_time"} else "max"
        elif column in KNOWN_BOOL_COLUMNS:
            agg_map[column] = _first_non_null
        elif _is_numeric_like(column, work[column]):
            agg_map[column] = "max"
        else:
            agg_map[column] = _first_non_null

    out = work.groupby(group_keys, dropna=False, sort=False).agg(agg_map).reset_index()

    if raw_metrics:
        grouped = work.groupby(group_keys, dropna=False, sort=False)[raw_metrics]
        count_df = grouped.count().add_suffix("_cnt")
        sum_df = grouped.sum(min_count=1).add_suffix("_sum")
        max_df = grouped.max().add_suffix("_max")
        raw_stats = pd.concat([count_df, sum_df, max_df], axis=1).reset_index()

        duplicate_cols = [col for col in raw_stats.columns if col in out.columns and col not in group_keys]
        if duplicate_cols:
            out = out.drop(columns=duplicate_cols)
        out = out.merge(raw_stats, on=group_keys, how="left", sort=False)

    if "start_time" in out.columns and "end_time" in out.columns:
        out["runtime_sec"] = (
            pd.to_datetime(out["end_time"], errors="coerce")
            - pd.to_datetime(out["start_time"], errors="coerce")
        ).dt.total_seconds()
    if "submit_time" in out.columns and "start_time" in out.columns:
        out["queue_time_sec"] = (
            pd.to_datetime(out["start_time"], errors="coerce")
            - pd.to_datetime(out["submit_time"], errors="coerce")
        ).dt.total_seconds()
    if "runtime_sec" in out.columns and "timelimit_sec" in out.columns:
        runtime = pd.to_numeric(out["runtime_sec"], errors="coerce")
        timelimit = pd.to_numeric(out["timelimit_sec"], errors="coerce")
        out["runtime_fraction"] = np.where(timelimit > 0, runtime / timelimit, np.nan)
    if "jid_global" not in out.columns and {"cluster", "jid"}.issubset(out.columns):
        out["jid_global"] = out["cluster"].astype("string") + "_" + out["jid"].astype("string")
    out = enrich_hardware_metadata(out, cluster=cluster, requested_columns=requested_columns)

    if requested_columns is not None:
        for column in requested_columns:
            if column not in out.columns:
                out[column] = pd.NA
        return out[requested_columns]
    return out


def read_job_level_frame(
    manifest_rows: list[dict[str, Any]],
    cluster: str | None,
    columns: list[str] | None,
    max_rows: int | None,
    seed: int,
    sample_n_row_groups_per_file: int | None = None,
    row_group_plan: list[dict[str, Any]] | None = None,
    plan_seed: int | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    candidate_rows = select_manifest_rows_for_cluster(manifest_rows, cluster)
    if not candidate_rows:
        return pd.DataFrame(columns=columns or []), {
            "used_paths": [],
            "raw_rows_sampled": 0,
            "job_rows": 0,
            "row_groups_read": 0,
            "available_columns": [],
            "cluster_filter": cluster,
            "sampling_plan_entries": [],
            "sampling_seed": int(plan_seed) if plan_seed is not None else int(seed),
            "read_errors": [],
        }

    schema_columns, has_cluster_column = _schema_union(candidate_rows)
    if cluster is not None and not has_cluster_column:
        clustered_rows = [row for row in candidate_rows if row.get("cluster") == cluster]
        if not clustered_rows:
            raise ValueError(
                f"Cannot filter cluster={cluster}: manifest rows have no cluster field and parquet schema has no cluster column."
            )

    requested_columns = columns or _default_output_columns(schema_columns)
    physical_columns = _physical_columns_to_read(requested_columns, schema_columns, cluster)

    rng = random.Random(seed)
    sampling_seed = int(plan_seed) if plan_seed is not None else int(seed)
    candidate_row_lookup = {str(Path(row["path"])): dict(row) for row in candidate_rows}
    if row_group_plan is None:
        ordered_rows = [dict(row) for row in candidate_rows]
        rng.shuffle(ordered_rows)
    else:
        ordered_rows = []
        for plan_entry in row_group_plan:
            plan_path = str(Path(plan_entry["path"]))
            manifest_row = candidate_row_lookup.get(plan_path)
            if manifest_row is None:
                raise ValueError(
                    f"Sampling plan path {plan_path} is not present in the current manifest for cluster={cluster}."
                )
            manifest_row["row_groups"] = [int(v) for v in plan_entry.get("row_groups", [])]
            ordered_rows.append(manifest_row)

    frames: list[pd.DataFrame] = []
    used_paths: list[Path] = []
    raw_rows_sampled = 0
    row_groups_read = 0
    sampling_plan_entries: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []

    for row in ordered_rows:
        path = Path(row["path"])
        try:
            pf = pq.ParquetFile(str(path))
        except OSError as exc:
            if row_group_plan is not None:
                raise RuntimeError(
                    f"Failed to open planned parquet file {path} for cluster={cluster}: {exc}"
                ) from exc
            read_errors.append(
                {
                    "path": str(path),
                    "row_group": None,
                    "error": str(exc),
                }
            )
            continue
        available = set(pf.schema_arrow.names)
        read_columns = [col for col in physical_columns if col in available]
        if "jid" not in available:
            continue
        if "jid" not in read_columns:
            read_columns = ["jid"] + read_columns

        if row_group_plan is None:
            row_groups = list(range(pf.num_row_groups))
            rng.shuffle(row_groups)
        else:
            row_groups = [int(v) for v in row.get("row_groups", [])]

        file_used = False
        file_row_groups_read = 0
        file_sampled_row_groups: list[int] = []
        for row_group in row_groups:
            if max_rows is not None and raw_rows_sampled >= max_rows:
                break
            if (
                row_group_plan is None
                and sample_n_row_groups_per_file
                and sample_n_row_groups_per_file > 0
                and file_row_groups_read >= sample_n_row_groups_per_file
            ):
                break

            try:
                table = pf.read_row_group(row_group, columns=read_columns)
            except OSError as exc:
                if row_group_plan is not None:
                    raise RuntimeError(
                        f"Failed to read planned row group {row_group} from {path} for cluster={cluster}: {exc}"
                    ) from exc
                read_errors.append(
                    {
                        "path": str(path),
                        "row_group": int(row_group),
                        "error": str(exc),
                    }
                )
                continue
            chunk = table.to_pandas()

            if cluster is not None:
                if "cluster" in chunk.columns:
                    chunk = chunk.loc[
                        chunk["cluster"].astype("string").fillna("") == cluster
                    ].copy()
                elif row.get("cluster") not in (None, "", cluster):
                    chunk = chunk.iloc[0:0].copy()

            if chunk.empty:
                continue

            for column in read_columns:
                if column not in chunk.columns:
                    chunk[column] = pd.NA

            if max_rows is not None:
                remaining = max_rows - raw_rows_sampled
                if remaining <= 0:
                    break
                if len(chunk) > remaining:
                    chunk = chunk.sample(n=remaining, random_state=sampling_seed)

            frames.append(chunk[read_columns])
            raw_rows_sampled += len(chunk)
            row_groups_read += 1
            file_row_groups_read += 1
            file_used = True
            file_sampled_row_groups.append(int(row_group))

        if file_used:
            used_paths.append(path)
            sampling_plan_entries.append(
                {
                    "path": str(path),
                    "row_groups": file_sampled_row_groups,
                }
            )
        if max_rows is not None and raw_rows_sampled >= max_rows:
            break

    if not frames:
        empty = pd.DataFrame(columns=requested_columns)
        return empty, {
            "used_paths": [],
            "raw_rows_sampled": 0,
            "job_rows": 0,
            "row_groups_read": 0,
            "available_columns": requested_columns,
            "cluster_filter": cluster,
            "sampling_plan_entries": [],
            "sampling_seed": sampling_seed,
            "read_errors": read_errors,
        }

    sampled = pd.concat(frames, ignore_index=True)
    job_level = collapse_to_job_level(
        sampled,
        requested_columns=requested_columns if columns is not None else None,
        cluster=cluster,
    )

    if columns is None:
        requested_columns = list(job_level.columns)
    else:
        for column in requested_columns:
            if column not in job_level.columns:
                job_level[column] = pd.NA
        job_level = job_level[requested_columns]

    return job_level, {
        "used_paths": used_paths,
        "raw_rows_sampled": int(raw_rows_sampled),
        "job_rows": int(len(job_level)),
        "row_groups_read": int(row_groups_read),
        "available_columns": requested_columns,
        "cluster_filter": cluster,
        "sampling_plan_entries": sampling_plan_entries,
        "sampling_seed": sampling_seed,
        "read_errors": read_errors,
    }


def build_file_records(
    paths: list[Path], cluster: str, hash_cache: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    cache = hash_cache if hash_cache is not None else {}
    for path in paths:
        cache_key = str(path)
        digest = cache.get(cache_key)
        if digest is None:
            digest = sha256_file(path)
            cache[cache_key] = digest
        records.append(
            {
                "cluster": cluster,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    return records


def capture_environment_artifacts(
    validation_dir: Path,
    cwd: Path,
    include_conda_env: bool = False,
    include_host_info: bool = False,
) -> dict[str, Any]:
    validation_dir.mkdir(parents=True, exist_ok=True)

    python_version = sys.version.replace("\n", " ")
    (validation_dir / "python_version.txt").write_text(
        python_version + "\n", encoding="utf-8"
    )

    rc, out, err = run_command([sys.executable, "-m", "pip", "freeze"], cwd)
    (validation_dir / "pip_freeze.txt").write_text(
        out if rc == 0 else (out + ("\n" if out and err else "") + err),
        encoding="utf-8",
    )

    environment = {
        "python_version": python_version,
        "python_executable": sys.executable,
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
    }

    if include_conda_env:
        conda_lines: str
        conda_env = os.environ.get("CONDA_DEFAULT_ENV")
        conda_cmd = ["conda", "env", "export", "--no-builds"]
        if conda_env:
            conda_cmd.extend(["-n", conda_env])
        rc, out, err = run_command(conda_cmd, cwd)
        conda_lines = out if rc == 0 else f"# conda env export failed\n{out}\n{err}".strip() + "\n"
        (validation_dir / "conda_env.yml").write_text(conda_lines, encoding="utf-8")

    if include_host_info:
        info_lines = [
            f"captured_at={utc_now_iso()}",
            f"hostname={socket.gethostname()}",
            f"platform={platform.platform()}",
            f"python_executable={sys.executable}",
            f"cwd={cwd}",
        ]
        for env_name in [
            "USER",
            "USERNAME",
            "CONDA_DEFAULT_ENV",
            "SLURM_JOB_ID",
            "SLURM_JOB_NAME",
            "SLURM_NODELIST",
        ]:
            if os.environ.get(env_name):
                info_lines.append(f"{env_name}={os.environ[env_name]}")
        (validation_dir / "host_info.txt").write_text(
            "\n".join(info_lines) + "\n", encoding="utf-8"
        )

    return environment
