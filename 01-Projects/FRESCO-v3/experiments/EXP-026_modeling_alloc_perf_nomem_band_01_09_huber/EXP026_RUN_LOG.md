# EXP-026 Run Log — HuberRegressor on EXP-024 cohorts (alloc+perf-no-mem)

**Run ID**: EXP-026_modeling_alloc_perf_nomem_band_01_09_huber  
**Date**: 2026-02-03  

## Objective
Rerun Phase 3 modeling on the existing EXP-024 matched cohorts (overlap band [0.1, 0.9]) using a robust regression model (HuberRegressor) instead of Ridge.

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`
- Cohorts (from EXP-024):
  - `experiments\\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\\results\\matched_source_indices.parquet`
  - `experiments\\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\\results\\matched_target_indices.parquet`

## Code & Environment
- Script: `scripts\\model_transfer.py`
- Model config: HuberRegressor (epsilon=1.35, alpha=1e-4, max_iter=500)
- Notes:
  - Label is proxy `value_memused_max` with `log1p` transform.
  - job_partials rows are collapsed to job-level via `groupby(jid).max()` inside `model_transfer.py`.

## Execution
Repro command:
```powershell
python scripts\model_transfer.py --config experiments\EXP-026_modeling_alloc_perf_nomem_band_01_09_huber\config\exp026_modeling_alloc_perf_nomem_band_01_09_huber.json
```

## Outputs
- Metrics: `experiments\\EXP-026_modeling_alloc_perf_nomem_band_01_09_huber\\results\\metrics.json`
- Predictions:
  - `...\\results\\predictions_source_test.parquet`
  - `...\\results\\predictions_target.parquet`
- Provenance:
  - `...\\manifests\\run_metadata.json`
  - `...\\manifests\\input_files_used.json`
  - `...\\validation\\python_version.txt`
  - `...\\validation\\pip_freeze.txt`

## Results Summary (proxy-only)
From `results/metrics.json`:
- Target R² (Conte): **-867.12** (bootstrap mean -867.79; CI [-1062.02, -742.38])
- Source-test R² (Anvil): **0.42**

## Known Issues / Caveats
- Proxy-only: the label is not the authoritative v3 target; do not treat as publication-grade.
- Matched source size is small after filters (source_rows_after_filters=70; train=42/test=11), so results are high-variance.
