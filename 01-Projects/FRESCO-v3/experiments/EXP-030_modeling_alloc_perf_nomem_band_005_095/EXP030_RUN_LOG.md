# EXP-030 Run Log — Modeling on band [0.05,0.95]

**Run ID**: EXP-030_modeling_alloc_perf_nomem_band_005_095  
**Date**: 2026-02-03  

## Objective
Phase 5 overlap-band sensitivity: model transfer on EXP-029 cohorts (band [0.05,0.95]).

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`
- Cohorts (from EXP-029):
  - `experiments\\EXP-029_regime_matching_alloc_perf_nomem_band_005_095\\results\\matched_source_indices.parquet`
  - `experiments\\EXP-029_regime_matching_alloc_perf_nomem_band_005_095\\results\\matched_target_indices.parquet`

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
python scripts\model_transfer.py --config experiments\EXP-030_modeling_alloc_perf_nomem_band_005_095\config\exp030_modeling_alloc_perf_nomem_band_005_095.json
```

## Outputs
- Metrics: `experiments\\EXP-030_modeling_alloc_perf_nomem_band_005_095\\results\\metrics.json`
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
- Target R² (Conte): **-949.52** (bootstrap mean -940.78)
- Source-test R² (Anvil): **0.64**

## Known Issues / Caveats
- Proxy-only: the label is not the authoritative v3 target; do not treat as publication-grade.
