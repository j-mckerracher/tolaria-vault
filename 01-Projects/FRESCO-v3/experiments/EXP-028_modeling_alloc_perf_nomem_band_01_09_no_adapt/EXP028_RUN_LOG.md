# EXP-028 Run Log — No adaptation baseline (Phase 5)

**Run ID**: EXP-028_modeling_alloc_perf_nomem_band_01_09_no_adapt  
**Date**: 2026-02-03  

## Objective
Provide the explicit "no adaptation" baseline on EXP-024 matched cohorts for Phase 5 comparison against CORAL.

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`
- Cohorts (from EXP-024):
  - `experiments\\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\\results\\matched_source_indices.parquet`
  - `experiments\\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\\results\\matched_target_indices.parquet`

## Code & Environment
- Script: `scripts\\model_transfer.py`
- Model: Ridge(alpha=1.0)
- Adaptation: none
- Notes:
  - Label is proxy `value_memused_max` with `log1p` transform.
  - job_partials rows are collapsed to job-level via `groupby(jid).max()` inside `model_transfer.py`.

## Execution
Repro command:
```powershell
python scripts\model_transfer.py --config experiments\EXP-028_modeling_alloc_perf_nomem_band_01_09_no_adapt\config\exp028_modeling_alloc_perf_nomem_band_01_09_no_adapt.json
```

## Outputs
- Metrics: `experiments\\EXP-028_modeling_alloc_perf_nomem_band_01_09_no_adapt\\results\\metrics.json`
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
- Target R² (Conte): **-129,418.84** (bootstrap mean -129,832.22)
- Source-test R² (Anvil): **-3,074.76**

## Known Issues / Caveats
- Proxy-only: the label is not the authoritative v3 target; do not treat as publication-grade.
