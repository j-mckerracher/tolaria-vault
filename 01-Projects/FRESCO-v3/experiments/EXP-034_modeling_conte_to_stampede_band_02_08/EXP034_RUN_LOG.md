# EXP-034 Run Log — Conte → Stampede modeling

**Run ID**: EXP-034_modeling_conte_to_stampede_band_02_08  
**Date**: 2026-02-03  

## Objective
Single-month pair modeling for Conte → Stampede using EXP-033 cohorts.

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`
- Cohorts (from EXP-033):
  - `experiments\\EXP-033_regime_matching_conte_to_stampede_band_02_08\\results\\matched_source_indices.parquet`
  - `experiments\\EXP-033_regime_matching_conte_to_stampede_band_02_08\\results\\matched_target_indices.parquet`

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
python scripts\model_transfer.py --config experiments\EXP-034_modeling_conte_to_stampede_band_02_08\config\exp034_modeling_conte_to_stampede_band_02_08.json
```

## Outputs
- Metrics: `experiments\\EXP-034_modeling_conte_to_stampede_band_02_08\\results\\metrics.json`

## Results Summary (proxy-only)
From `results/metrics.json`:
- Target overlap count: 1 (R² undefined; NaN)

## Known Issues / Caveats
- Proxy-only: months are not configurable in the proxy manifest (single month per cluster).
- Extremely small target overlap makes metrics non-informative.
