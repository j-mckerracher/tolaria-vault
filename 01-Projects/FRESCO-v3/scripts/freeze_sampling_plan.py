#!/usr/bin/env python3
"""Capture a reusable row-group sampling plan for reproducible cohort studies."""

from __future__ import annotations

import argparse
from pathlib import Path

from fresco_data_loader import (
    build_file_records,
    git_info,
    load_manifest_rows,
    read_job_level_frame,
    resolve_path,
    utc_now_iso,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-manifest", required=True, help="Input manifest for parquet shards.")
    parser.add_argument("--output", required=True, help="Output JSON path for the frozen sampling plan.")
    parser.add_argument("--source-cluster", required=True, help="Source cluster name.")
    parser.add_argument("--target-cluster", required=True, help="Target cluster name.")
    parser.add_argument(
        "--max-rows-per-cluster",
        required=True,
        type=int,
        help="Sampling cap per cluster before job-level collapse.",
    )
    parser.add_argument(
        "--sample-n-row-groups-per-file",
        default=0,
        type=int,
        help="Maximum non-empty row groups to sample per file (0 disables the cap).",
    )
    parser.add_argument("--seed", required=True, type=int, help="Base seed; target uses seed+1.")
    parser.add_argument("--dataset-label", default=None, help="Optional dataset label to record.")
    parser.add_argument(
        "--reference-config",
        default=None,
        help="Optional config path whose sampling settings this plan is freezing.",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Optional free-text note to include in the plan metadata (repeatable).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = resolve_path(args.inputs_manifest, repo_root)
    output_path = resolve_path(args.output, repo_root)
    reference_config = (
        resolve_path(args.reference_config, repo_root) if args.reference_config else None
    )

    manifest_rows = load_manifest_rows(manifest_path, repo_root)
    sample_n_row_groups = int(args.sample_n_row_groups_per_file or 0) or None

    hash_cache: dict[str, str] = {}
    plan = {
        "created_utc": utc_now_iso(),
        "dataset_label": args.dataset_label,
        "inputs_manifest": str(manifest_path),
        "reference_config": str(reference_config) if reference_config is not None else None,
        "sampling": {
            "max_rows_per_cluster": int(args.max_rows_per_cluster),
            "sample_n_row_groups_per_file": sample_n_row_groups,
            "base_seed": int(args.seed),
        },
        "git": git_info(repo_root),
        "input_files_used": build_file_records([manifest_path], "manifest", hash_cache=hash_cache),
        "notes": list(args.note),
        "clusters": {},
    }

    for cluster, cluster_seed in (
        (args.source_cluster, int(args.seed)),
        (args.target_cluster, int(args.seed) + 1),
    ):
        _, meta = read_job_level_frame(
            manifest_rows=manifest_rows,
            cluster=cluster,
            columns=["jid"],
            max_rows=int(args.max_rows_per_cluster),
            seed=cluster_seed,
            sample_n_row_groups_per_file=sample_n_row_groups,
        )
        if meta["read_errors"]:
            first_error = meta["read_errors"][0]
            raise RuntimeError(
                f"Sampling plan capture for cluster={cluster} encountered "
                f"{len(meta['read_errors'])} read errors; first error: {first_error}"
            )
        if int(meta["row_groups_read"]) <= 0:
            raise RuntimeError(
                f"Sampling plan capture for cluster={cluster} read zero row groups."
            )
        plan["clusters"][cluster] = {
            "seed": int(cluster_seed),
            "raw_rows_sampled": int(meta["raw_rows_sampled"]),
            "job_rows": int(meta["job_rows"]),
            "row_groups_read": int(meta["row_groups_read"]),
            "entries": meta["sampling_plan_entries"],
            "read_errors": meta["read_errors"],
        }

    write_json(output_path, plan)
    print(f"Wrote sampling plan to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
