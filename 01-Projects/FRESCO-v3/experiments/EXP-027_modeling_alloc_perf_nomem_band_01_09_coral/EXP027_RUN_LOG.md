# EXP-027 Run Log — CORAL adaptation (Phase 4)

**Run ID**: EXP-027_modeling_alloc_perf_nomem_band_01_09_coral  
**Date**: 2026-02-03  

## Objective
Apply CORAL covariance alignment (unlabeled target) on the EXP-024 matched cohorts and evaluate transfer performance.

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`
- Cohorts (from EXP-024):
  - `experiments\\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\\results\\matched_source_indices.parquet`
  - `experiments\\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\\results\\matched_target_indices.parquet`

## Code & Environment
- Script: `scripts\\model_transfer.py`
- Adaptation: CORAL on log1p-transformed features, reg=1e-6
- Model: Ridge(alpha=1.0)
- Notes:
  - Label is proxy `value_memused_max` with `log1p` transform.
  - job_partials rows are collapsed to job-level via `groupby(jid).max()` inside `model_transfer.py`.

## Execution
Repro command:
```powershell
python scripts\model_transfer.py --config experiments\EXP-027_modeling_alloc_perf_nomem_band_01_09_coral\config\exp027_modeling_alloc_perf_nomem_band_01_09_coral.json
```

## Outputs
- Metrics: `experiments\\EXP-027_modeling_alloc_perf_nomem_band_01_09_coral\\results\\metrics.json`
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
- Target R² (Conte): **-706,600,418.16** (bootstrap mean -707,619,857.49)
- Source-test R² (Anvil): **-223,060,454.96**
- `overflow_pred=true` in target metrics (numerical instability flagged).

## Known Issues / Caveats
- Proxy-only: the label is not the authoritative v3 target; do not treat as publication-grade.
- CORAL caused severe numerical instability (overflow in expm1), indicating poor alignment under this proxy setup.
