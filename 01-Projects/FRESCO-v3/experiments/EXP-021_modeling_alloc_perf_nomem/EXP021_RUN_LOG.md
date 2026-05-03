# EXP-021 Phase 3 Modeling (Alloc + Perf, no memused) — Run Log

**Run ID**: EXP-021_modeling_alloc_perf_nomem  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 3 ablation: train a simple zero-shot transfer model on the **matched overlap cohort** from EXP-020 and evaluate transfer from **Anvil → Conte**.

This run is explicitly **proxy-only** because it uses job_partials and a proxy label.

## Inputs
- Parquet input manifest: `experiments\EXP-016_feature_matrix\manifests\input_files.json`
- Overlap cohorts (from EXP-020):
  - `experiments\EXP-020_regime_matching_alloc_perf_nomem\results\matched_source_indices.parquet`
  - `experiments\EXP-020_regime_matching_alloc_perf_nomem\results\matched_target_indices.parquet`

## Regime
- `cpu_standard` (local proxy): `(value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Label (proxy)
- `value_memused_max`
- transform: `log1p`

## Features (no memused)
- `ncores`, `timelimit`
- `value_block_{cnt,sum}`
- `value_cpuuser_{cnt,sum}`
- `value_gpu_{cnt,sum}`
- `value_nfs_{cnt,sum}`

## Model
- Ridge regression (median impute + standardize)

## Execution
```powershell
python scripts\model_transfer.py --config experiments\EXP-021_modeling_alloc_perf_nomem\config\exp021_modeling_alloc_perf_nomem.json
```

## Outputs
- Metrics: `results\metrics.json`
- Predictions:
  - `results\predictions_source_test.parquet`
  - `results\predictions_target.parquet`
- Provenance:
  - `manifests\run_metadata.json`
  - `manifests\input_files_used.json` (includes overlap index artifacts)
  - `validation\{python_version.txt,pip_freeze.txt}`

## Cohort sizes
(from logs/metrics)
- Matched source jobs used: 53
- Matched target jobs used: 544

## Note on unit of analysis
The local `job_partials` snapshot contains multiple rows per `jid` (partials/time slices). This run collapses to **job-level** by aggregating numeric columns per `jid` using `max()` before training/evaluation.

## Caveats
- Label is a local proxy (value_memused_max) from job_partials, not the authoritative v3 `peak_memory_fraction` target.
- Feature overlap was limited by strong shift even after restricting to Phase-1-safe perf aggregates.
