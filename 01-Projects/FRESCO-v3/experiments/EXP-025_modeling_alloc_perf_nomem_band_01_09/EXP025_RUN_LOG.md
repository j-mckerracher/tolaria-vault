# EXP-025 Phase 3 Modeling (Alloc + Perf, no memused, overlap band [0.1, 0.9]) — Run Log

**Run ID**: EXP-025_modeling_alloc_perf_nomem_band_01_09  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 3 ablation: evaluate whether widening the overlap band to **[0.1, 0.9]** improves zero-shot transfer for Anvil → Conte on the alloc+perf-no-mem feature set, operating at **job-level**.

## Inputs
- Parquet input manifest: `experiments\EXP-016_feature_matrix\manifests\input_files.json`
- Overlap cohorts (from EXP-024):
  - `experiments\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\results\matched_source_indices.parquet`
  - `experiments\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\results\matched_target_indices.parquet`

## Regime
- `cpu_standard` (local proxy): `(value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Label (proxy)
- `value_memused_max` (transform: `log1p`)

## Features
- `ncores`, `timelimit`, `value_block_{cnt,sum}`, `value_cpuuser_{cnt,sum}`, `value_gpu_{cnt,sum}`, `value_nfs_{cnt,sum}`

## Model
- Ridge regression (median impute + standardize)

## Execution
```powershell
python scripts\model_transfer.py --config experiments\EXP-025_modeling_alloc_perf_nomem_band_01_09\config\exp025_modeling_alloc_perf_nomem_band_01_09.json
```

## Outputs
- Metrics: `results\metrics.json`
- Predictions:
  - `results\predictions_source_test.parquet`
  - `results\predictions_target.parquet`
- Provenance: `manifests\run_metadata.json`, `manifests\input_files_used.json`, `validation\{python_version.txt,pip_freeze.txt}`

## Headline results (proxy)
(from `results\metrics.json`)
- Target R²: **-129418.84** (bootstrap mean ≈ -129832.22)

## Note on unit of analysis
The local `job_partials` snapshot contains multiple rows per `jid` (partials/time slices). This run collapses to **job-level** by aggregating numeric columns per `jid` using `max()`.

## Interpretation / Caveats
- Widening the overlap band increases coverage (EXP-024), but transfer remains catastrophic on the proxy label, suggesting strong conditional/label shift and/or instability from very small source cohort.
- Local proxy only; rerun on true v3 shards + true label is required for publication-grade conclusions.
