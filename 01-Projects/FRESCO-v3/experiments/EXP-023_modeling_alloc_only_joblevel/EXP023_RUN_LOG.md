# EXP-023 Phase 3 Modeling (Allocations-only, job-level) — Run Log

**Run ID**: EXP-023_modeling_alloc_only_joblevel  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 3 rerun of the allocations-only baseline **at job granularity**, training on Anvil overlap cohort and evaluating zero-shot transfer to Conte.

## Inputs
- Parquet input manifest: `experiments\EXP-016_feature_matrix\manifests\input_files.json`
- Overlap cohorts (from EXP-022):
  - `experiments\EXP-022_regime_matching_alloc_only_joblevel\results\matched_source_indices.parquet`
  - `experiments\EXP-022_regime_matching_alloc_only_joblevel\results\matched_target_indices.parquet`

## Regime
- `cpu_standard` (local proxy): `(value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Label (proxy)
- `value_memused_max` (transform: `log1p`)

## Features
- `ncores`, `timelimit` (log1p applied)

## Model
- Ridge regression (median impute + standardize)

## Execution
```powershell
python scripts\model_transfer.py --config experiments\EXP-023_modeling_alloc_only_joblevel\config\exp023_modeling_alloc_only_joblevel.json
```

## Outputs
- Metrics: `results\metrics.json`
- Predictions:
  - `results\predictions_source_test.parquet`
  - `results\predictions_target.parquet`
- Provenance: `manifests\run_metadata.json`, `manifests\input_files_used.json`, `validation\{python_version.txt,pip_freeze.txt}`

## Headline results (proxy)
(from `results\metrics.json`)
- Target R²: **-30.21** (bootstrap CI ~[-33.03, -28.15])

## Note on unit of analysis
The local `job_partials` snapshot contains multiple rows per `jid` (partials/time slices). This run collapses to **job-level** by aggregating numeric columns per `jid` using `max()`.

## Interpretation / Caveats
- Despite full target overlap coverage under allocations-only propensity (EXP-022), transfer remains strongly negative on the proxy label, consistent with conditional/label shift.
- Local proxy only; rerun on true v3 shards + true label is required for publication-grade conclusions.
