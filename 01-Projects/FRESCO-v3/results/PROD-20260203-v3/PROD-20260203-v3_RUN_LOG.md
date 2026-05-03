# PROD-20260203-v3 Run Log — FRESCO v3 Production Dataset Build

**Run ID**: PROD-20260203-v3  
**Date**: 2026-02-03 (submitted) / 2026-03-09 (executed) / 2026-03-11 (verified + finalized) / 2026-03-11 (archived)

## Objective

Build the authoritative FRESCO v3 unified parquet dataset from raw FRESCO shards across all three clusters (anvil, conte, stampede) and write validation, manifest, and provenance artifacts required for publication.

## Inputs

- Dataset label: raw FRESCO shards
- Input root: `/depot/sbagchi/data/josh/FRESCO/chunks/`
- Clusters: **anvil**, **conte**, **stampede**
- Date range: 2013–2023 (full available range)
- Config: `config/production_v3.json` (local), `/home/jmckerra/Code/FRESCO-Pipeline/config/production_v3.json` (Gilbreth)

## Code & Environment

- Script: `scripts/build_production_v3.py`
- Config: `config/production_v3.json`
- Remote execution path: `/home/jmckerra/Code/FRESCO-Pipeline`
- Finalization script: `scripts/finalize_production_v3.py`
- Git commit (pipeline): `fc750e678863efacf098e8d83a8840d3aad97ea9` (captured in `manifests/run_metadata.json` during finalizer job `10404611`)
- Conda env: `fresco_v2`
- SLURM job script: `scripts/production_v3.slurm`

## Execution

- Cluster: Gilbreth (Purdue RCAC)
- Partition: `a100-80gb` (only valid partition for `sbagchi` account)
- SLURM job IDs:
  - ~~10323059~~ — CANCELLED (wrong partition: `a10`)
  - **10387798** — COMPLETED ✅
  - **10404611** — COMPLETED ✅ (`finalize_v3` backfill on `training`)
- Job 10387798 start: 2026-03-09T10:47:11 EDT
- Job 10387798 end:   2026-03-09T13:20:23 EDT
- Elapsed: 2h 33m 12s

## Outputs

- Output file: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/PROD-20260203-v3_v3.parquet`
- Row groups: 62,668
- Total rows: **655,327,086**
- Input manifest: `manifests/input_manifest.jsonl` (**62,668** entries, now with `sha256`)
- Output manifest: `manifests/output_manifest.jsonl` (**1** entry, now with `sha256`)
- Run metadata: `manifests/run_metadata.json`
- Validation present:
  - `validation/schema_report.json`
  - `validation/dtype_report.json`
  - `validation/missingness_report.json`
  - `validation/sanity_checks.json`
  - `validation/python_version.txt`
  - `validation/pip_freeze.txt`
  - `validation/conda_env.yml`
  - `validation/host_info.txt`
- Archive root: `/depot/sbagchi/data/josh/FRESCO-Research/runs/PROD-20260203-v3`

## Results Summary

### Cluster distribution (from verify job 10393102)

| Cluster   | Rows         | Pct    |
|-----------|-------------|--------|
| anvil     | 63,220,257  | 9.65%  |
| conte     | 86,521,057  | 13.20% |
| stampede  | 505,585,772 | 77.15% |
| **Total** | **655,327,086** | 100% |

### Schema

All three clusters present. Timestamp fields (`time`, `submit_time`, `start_time`, `end_time`) confirmed as `timestamp[us]`. See `docs/SCHEMA_AND_PROVENANCE.md` for full column list.

**Note**: Actual output schema uses raw FRESCO column naming (`value_memused`, `value_cpuuser`, etc.), not the aspirational canonical names in the schema docs. See Known Issues.

## Validation Summary

- Level 0 (schema): ✅ All clusters present, required columns present
- Basic verification: ✅ `verify_v3_output.py` completed successfully in job **10393102**
- Validation artifacts actually present:
  - ✅ `validation/schema_report.json`
  - ✅ `validation/missingness_report.json`
  - ✅ `validation/dtype_report.json`
  - ✅ `validation/sanity_checks.json`
- Finalizer backfill: ✅ job **10404611** wrote validation/env/manifests from committed code `fc750e678863efacf098e8d83a8840d3aad97ea9`
- Quantified sanity exceptions remain:
  - `42` rows with negative `queue_time_sec` / `submit_after_start`
  - `402,365` rows with `runtime_fraction > 1.05`
- Level 1/2/3 status: **partially satisfied** — the artifacts now exist and exceptions are quantified, but the run is not a full clean pass

## Verification Status

| Job ID   | Status               | Notes |
|----------|----------------------|-------|
| 10387799 | **FAILED** (exit 1)  | `AttributeError: ParquetSchema has no .field()` — PyArrow API bug in script. Fixed in `scripts/verify_v3_output.py` (commit `af32734`). |
| **10393102** | **COMPLETED** (exit 0) | Resubmitted after fix; verified cluster counts and timestamp field types successfully. |

## Archive Status

- Archive completed: ✅
- Archive location: `/depot/sbagchi/data/josh/FRESCO-Research/runs/PROD-20260203-v3`
- Archived bundle includes:
  - `config/production_v3.json`
  - `manifests/input_manifest.jsonl`
  - `manifests/output_manifest.jsonl`
  - `manifests/run_metadata.json`
  - full `validation/` artifact bundle
  - SLURM logs for production (`10387798`), failed verify (`10387799`), successful verify (`10393102`), and finalizer (`10404611`)
- Archive verification: required records were checked after copy and all expected files were present.

## Known Issues / Caveats

1. **Schema implementation gap**: The actual v3 parquet output uses raw FRESCO column names (`value_memused`, `value_gpu`, `value_cpuuser`, `value_nfs`, `value_block`, `queue`) rather than the normalized fields described in `docs/SCHEMA_AND_PROVENANCE.md` (`peak_memory_gb`, `partition`, etc.). Derived columns (`runtime_sec`, `queue_time_sec`, `runtime_fraction`, `peak_memory_fraction`) are not stored, so downstream analysis must either derive them post hoc or the production pipeline must be extended and rerun.

2. **Sanity exceptions remain**: `validation/sanity_checks.json` reports `42` rows with negative queue time / submit-after-start and `402,365` rows with `runtime_fraction > 1.05`. These are now quantified, but still need interpretation as scheduler/accounting quirks vs. true data defects.

3. **Research status**: Authoritative reruns now exist for `EXP-039` / `EXP-040` / `EXP-041`, but direct Anvil -> Conte transfer on raw `value_memused_max` still performs very poorly (`target R^2 = -11.8921`) even after overlap filtering.

## Next Actions

1. Decide whether publication will rely on post hoc derived runtime/memory fields or on a rebuilt parquet that materializes the target canonical schema directly.
2. Revisit the Phase 2/3 regime/label design, because the current authoritative activity-based overlap slice still leaves severe cross-cluster shift.

## Repro Steps

```bash
# On Gilbreth:
conda activate fresco_v2
cd /home/jmckerra/Code/FRESCO-Pipeline
sbatch --partition=a100-80gb --account=sbagchi production_v3.slurm
```
