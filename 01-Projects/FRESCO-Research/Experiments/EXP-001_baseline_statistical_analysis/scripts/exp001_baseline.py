"""EXP-001 Baseline statistical analysis pipeline.

Designed for full-dataset execution on HPC where input parquet shards live at:
  /depot/sbagchi/data/josh/FRESCO/chunks

Pipeline stages:
  stage1: scan raw shards -> write per-file *job partials* (tmp parquet)
  stage2: reduce partials -> write final per-job rollup (parquet, partitioned)
  stage3: aggregate per-job rollups -> write monthly summary tables (parquet + csv)

Notes:
- Uses DuckDB when available for out-of-core reductions (recommended for full scale).
- Stage1 supports sharding work via --rank/--stride for SLURM job arrays.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

import numpy as np
import pandas as pd

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except Exception as e:  # pragma: no cover
    raise RuntimeError("pyarrow is required (pip install pyarrow)") from e

try:
    import duckdb  # type: ignore

    HAS_DUCKDB = True
except Exception:
    HAS_DUCKDB = False


METRIC_COLS = [
    "value_cpuuser",
    "value_gpu",
    "value_memused",
    "value_memused_minus_diskcache",
    "value_nfs",
    "value_block",
]

ATTR_COLS = [
    "time",
    "submit_time",
    "start_time",
    "end_time",
    "timelimit",
    "nhosts",
    "ncores",
    "account",
    "queue",
    "host",
    "jid",
    "unit",
    "jobname",
    "exitcode",
    "host_list",
    "username",
]


@dataclass(frozen=True)
class Paths:
    input_root: Path
    tmp_root: Path
    out_root: Path


def _iter_parquet_files(root: Path) -> Iterator[Path]:
    # Using os.walk (fast enough; on HPC consider precomputed manifests for millions of files).
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".parquet"):
                yield Path(dirpath) / fn


_TOKEN_RE = re.compile(r"^(?P<hour>\d{2})(?P<suffix>_[A-Za-z0-9]+)?\.parquet$")


def _source_token_from_filename(name: str) -> str:
    m = _TOKEN_RE.match(name)
    if not m:
        return "UNKNOWN"
    suf = m.group("suffix")
    if not suf:
        return "NONE"
    return suf.lstrip("_")


def _ensure_cols(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df


def _to_utc_datetime(s: pd.Series) -> pd.Series:
    # Handles mixed tz-naive/tz-aware by coercing everything to UTC.
    out = pd.to_datetime(s, errors="coerce", utc=True)
    return out


def _first_nonnull(x: pd.Series):
    x = x.dropna()
    if len(x) == 0:
        return pd.NA
    return x.iloc[0]


def _read_parquet_to_pandas(path: Path, columns: Optional[list[str]] = None) -> pd.DataFrame:
    # Some shards may drift in schema; only request columns that actually exist.
    if columns is not None:
        try:
            pf = pq.ParquetFile(path)
            present = set(pf.schema_arrow.names)
            columns = [c for c in columns if c in present]
        except Exception:
            # Fall back to letting pyarrow raise a useful error.
            pass
    table = pq.read_table(path, columns=columns)
    return table.to_pandas()


def stage1_write_job_partials(
    paths: Paths,
    *,
    rank: int,
    stride: int,
    max_files: Optional[int],
    verbose_every: int,
) -> None:
    """Scan raw shards and write per-file job partials to tmp_root/job_partials/.

    Partitioning is by (start_year, start_month, source_token) so each job is assigned
    to exactly one partition based on *start_time*.
    """

    in_root = paths.input_root
    out_base = paths.tmp_root / "job_partials"
    out_base.mkdir(parents=True, exist_ok=True)

    cols = list(dict.fromkeys(["jid"] + ATTR_COLS + METRIC_COLS))

    file_iter = _iter_parquet_files(in_root)

    processed = 0
    selected = 0

    for i, f in enumerate(file_iter):
        if stride > 1 and (i % stride) != rank:
            continue
        selected += 1
        if max_files is not None and selected > max_files:
            break

        token = _source_token_from_filename(f.name)

        try:
            df = _read_parquet_to_pandas(f, columns=cols)
        except Exception as e:
            print(f"[stage1] ERROR reading {f}: {e}", file=sys.stderr)
            continue

        if df.empty:
            continue

        df = _ensure_cols(df, cols)

        # Normalize timestamps
        for tcol in ["time", "submit_time", "start_time", "end_time"]:
            if tcol in df.columns:
                df[tcol] = _to_utc_datetime(df[tcol])

        # Ensure jid is string-like
        df["jid"] = df["jid"].astype("string")

        # Coerce metrics to numeric to survive era-to-era dtype drift.
        for m in METRIC_COLS:
            df[m] = pd.to_numeric(df[m], errors="coerce")

        gb = df.groupby("jid", sort=False)

        agg_kwargs = {
            "submit_time": ("submit_time", _first_nonnull),
            "start_time": ("start_time", _first_nonnull),
            "end_time": ("end_time", _first_nonnull),
            "timelimit": ("timelimit", _first_nonnull),
            "nhosts": ("nhosts", _first_nonnull),
            "ncores": ("ncores", _first_nonnull),
            "account": ("account", _first_nonnull),
            "queue": ("queue", _first_nonnull),
            "host": ("host", _first_nonnull),
            "unit": ("unit", _first_nonnull),
            "jobname": ("jobname", _first_nonnull),
            "exitcode": ("exitcode", _first_nonnull),
            "host_list": ("host_list", _first_nonnull),
            "username": ("username", _first_nonnull),
            "sample_time_min": ("time", "min"),
            "sample_time_max": ("time", "max"),
            "partial_rows": ("jid", "size"),
        }

        for m in METRIC_COLS:
            agg_kwargs[f"{m}_sum"] = (m, "sum")
            agg_kwargs[f"{m}_cnt"] = (m, "count")
            agg_kwargs[f"{m}_max"] = (m, "max")

        part = gb.agg(**agg_kwargs).reset_index()
        part["source_token"] = token

        st = _to_utc_datetime(part["start_time"])
        part["start_year"] = st.dt.year.fillna(0).astype("int32")
        part["start_month"] = st.dt.month.fillna(0).astype("int8")

        # Use start_time-derived partitions so each job maps consistently.
        # Hive-style directories help DuckDB partitioning.
        # NOTE: month is 0 if unknown.
        sy = int(part["start_year"].iloc[0]) if len(part) else 0
        sm = int(part["start_month"].iloc[0]) if len(part) else 0

        # However, within one shard file, jobs can have different start months.
        # So we must write by grouping on (start_year,start_month) first.
        for (y, m), sub in part.groupby(["start_year", "start_month"], sort=False):
            out_dir = (
                out_base
                / f"start_year={int(y):04d}"
                / f"start_month={int(m):02d}"
                / f"source_token={token}"
            )
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"part-r{rank:03d}-{uuid.uuid4().hex}.parquet"
            table = pa.Table.from_pandas(sub, preserve_index=False)
            pq.write_table(table, out_path, compression="zstd")

        processed += 1
        if verbose_every > 0 and processed % verbose_every == 0:
            print(f"[stage1] processed_files={processed} selected_files={selected} last={f}")

    print(f"[stage1] DONE processed_files={processed} selected_files={selected} rank={rank} stride={stride}")


def _require_duckdb():
    if not HAS_DUCKDB:
        raise RuntimeError(
            "DuckDB is required for stage2/stage3 at full scale. Install with: pip install duckdb"
        )


def stage2_reduce_to_job_rollup(paths: Paths, *, threads: int) -> None:
    """Reduce job partials into a per-job rollup table partitioned by start_year/start_month/source_token."""

    _require_duckdb()

    in_glob = str((paths.tmp_root / "job_partials" / "**" / "*.parquet").as_posix())
    out_dir = paths.out_root / "job_rollup"
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(database=":memory:")
    con.execute(f"PRAGMA threads={int(threads)}")

    # DuckDB will include hive partitions as columns if hive_partitioning=1.
    # union_by_name handles schema drift (e.g., account=NULL in some partials vs VARCHAR in others)
    rel = f"read_parquet('{in_glob}', hive_partitioning=1, union_by_name=true)"

    # Important: do NOT group by start_year/start_month from stage1 partitions.
    # Some shard files may have missing start_time for a job, which would otherwise create
    # duplicate rows for the same jid across (start_year,start_month)=0 vs the true month.
    sql = f"""
    COPY (
      WITH agg AS (
        SELECT
          jid,
          source_token,

          min(submit_time) AS submit_time,
          min(start_time) AS start_time,
          max(end_time) AS end_time,

          any_value(timelimit) AS timelimit,
          any_value(nhosts) AS nhosts,
          any_value(ncores) AS ncores,
          any_value(account) AS account,
          any_value(queue) AS queue,
          any_value(host) AS host,
          any_value(unit) AS unit,
          any_value(jobname) AS jobname,
          any_value(exitcode) AS exitcode,
          any_value(host_list) AS host_list,
          any_value(username) AS username,

          min(sample_time_min) AS sample_time_min,
          max(sample_time_max) AS sample_time_max,
          sum(partial_rows) AS snapshot_rows,

          {', '.join([f'sum({m}_sum) AS {m}_sum' for m in METRIC_COLS])},
          {', '.join([f'sum({m}_cnt) AS {m}_cnt' for m in METRIC_COLS])},
          {', '.join([f'max({m}_max) AS {m}_max' for m in METRIC_COLS])}

        FROM {rel}
        GROUP BY jid, source_token
      )
      SELECT
        jid,
        source_token,
        coalesce(year(start_time), 0) AS start_year,
        coalesce(month(start_time), 0) AS start_month,

        submit_time,
        start_time,
        end_time,
        timelimit,
        nhosts,
        ncores,
        account,
        queue,
        host,
        unit,
        jobname,
        exitcode,
        host_list,
        username,

        sample_time_min,
        sample_time_max,
        snapshot_rows,

        -- Derived timing features (useful for downstream anomaly models)
        date_diff('second', submit_time, start_time) AS wait_sec,
        date_diff('second', start_time, end_time) AS runtime_sec,

        {', '.join([f'{m}_sum' for m in METRIC_COLS])},
        {', '.join([f'{m}_cnt' for m in METRIC_COLS])},
        {', '.join([f'{m}_max' for m in METRIC_COLS])},

        -- Derived means (sum/count) for convenience
        {', '.join([f'CASE WHEN {m}_cnt > 0 THEN ({m}_sum::DOUBLE / {m}_cnt) ELSE NULL END AS {m}_mean' for m in METRIC_COLS])}

      FROM agg
    ) TO '{out_dir.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (start_year, start_month, source_token));
    """

    con.execute(sql)
    con.close()

    print(f"[stage2] Wrote job rollups to: {out_dir}")


def stage3_write_monthly_summary(paths: Paths, *, threads: int) -> None:
    """Create monthly summary table(s) from the per-job rollup table."""

    _require_duckdb()

    job_glob = str((paths.out_root / "job_rollup" / "**" / "*.parquet").as_posix())
    out_parquet = paths.out_root / "monthly_summary.parquet"
    out_csv = paths.out_root / "monthly_summary.csv"

    con = duckdb.connect(database=":memory:")
    con.execute(f"PRAGMA threads={int(threads)}")

    base = f"read_parquet('{job_glob}', hive_partitioning=1, union_by_name=true)"

    # Derive per-job numeric features in a subquery for cleaner aggregation.
    # date_diff returns BIGINT seconds.
    sql = f"""
    COPY (
      WITH job AS (
        SELECT
          start_year,
          start_month,
          source_token,
          jid,
          wait_sec,
          runtime_sec,
          try_cast(nhosts AS DOUBLE) AS nhosts,
          try_cast(ncores AS DOUBLE) AS ncores,
          value_cpuuser_mean AS cpuuser_mean,
          value_memused_max AS peak_memused,
          CASE WHEN value_gpu_cnt > 0 THEN 1 ELSE 0 END AS has_gpu_samples,
          CASE WHEN value_memused_cnt > 0 THEN 1 ELSE 0 END AS has_mem_samples
        FROM {base}
      )
      SELECT
        start_year,
        start_month,
        source_token,

        count(*) AS jobs,

        avg(runtime_sec) AS runtime_mean_sec,
        approx_quantile(runtime_sec, 0.5) AS runtime_median_sec,
        approx_quantile(runtime_sec, 0.9) AS runtime_p90_sec,
        approx_quantile(runtime_sec, 0.99) AS runtime_p99_sec,

        avg(wait_sec) AS wait_mean_sec,
        approx_quantile(wait_sec, 0.5) AS wait_median_sec,
        approx_quantile(wait_sec, 0.9) AS wait_p90_sec,

        avg(ncores) AS ncores_mean,
        approx_quantile(ncores, 0.9) AS ncores_p90,

        avg(peak_memused) AS peak_memused_mean,
        approx_quantile(peak_memused, 0.9) AS peak_memused_p90,
        approx_quantile(peak_memused, 0.99) AS peak_memused_p99,

        avg(cpuuser_mean) AS cpuuser_mean_of_mean,

        avg(has_gpu_samples) AS frac_jobs_with_gpu_samples,
        avg(has_mem_samples) AS frac_jobs_with_mem_samples

      FROM job
      GROUP BY start_year, start_month, source_token
      ORDER BY start_year, start_month, source_token
    ) TO '{out_parquet.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD);
    """

    con.execute(sql)

    # Also write CSV for convenience.
    con.execute(
        f"COPY (SELECT * FROM read_parquet('{out_parquet.as_posix()}')) TO '{out_csv.as_posix()}' (HEADER, DELIMITER ',');"
    )

    con.close()

    print(f"[stage3] Wrote monthly summary to: {out_parquet} and {out_csv}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common_io(sp: argparse.ArgumentParser):
        sp.add_argument(
            "--input-root",
            type=Path,
            default=Path("/depot/sbagchi/data/josh/FRESCO/chunks"),
            help="Root of FRESCO parquet shards (chunks/)",
        )
        sp.add_argument(
            "--tmp-root",
            type=Path,
            default=Path("results") / "tmp",
            help="Temporary output root (job partials)",
        )
        sp.add_argument(
            "--out-root",
            type=Path,
            default=Path("results"),
            help="Final output root (job_rollup, monthly_summary)",
        )

    s1 = sub.add_parser("stage1", help="Scan raw shards and write per-file job partials")
    add_common_io(s1)
    s1.add_argument("--rank", type=int, default=0, help="Shard rank for job arrays")
    s1.add_argument("--stride", type=int, default=1, help="Shard stride for job arrays")
    s1.add_argument("--max-files", type=int, default=None, help="Process only first N selected files")
    s1.add_argument("--verbose-every", type=int, default=5000, help="Progress print frequency")

    s2 = sub.add_parser("stage2", help="Reduce job partials to per-job rollups (DuckDB)")
    add_common_io(s2)
    s2.add_argument("--threads", type=int, default=8)

    s3 = sub.add_parser("stage3", help="Aggregate job rollups to monthly summary (DuckDB)")
    add_common_io(s3)
    s3.add_argument("--threads", type=int, default=8)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    paths = Paths(input_root=args.input_root, tmp_root=args.tmp_root, out_root=args.out_root)

    if args.cmd == "stage1":
        stage1_write_job_partials(
            paths,
            rank=args.rank,
            stride=args.stride,
            max_files=args.max_files,
            verbose_every=args.verbose_every,
        )
        return 0

    if args.cmd == "stage2":
        stage2_reduce_to_job_rollup(paths, threads=args.threads)
        return 0

    if args.cmd == "stage3":
        stage3_write_monthly_summary(paths, threads=args.threads)
        return 0

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
