# EXP-036 Run Log — Stampede → Anvil modeling

**Run ID**: EXP-036_modeling_stampede_to_anvil_band_02_08  
**Date**: 2026-02-03  

## Objective
Single-month pair modeling for Stampede → Anvil using EXP-035 cohorts.

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`
- Cohorts (from EXP-035):
  - `experiments\\EXP-035_regime_matching_stampede_to_anvil_band_02_08\\results\\matched_source_indices.parquet`
  - `experiments\\EXP-035_regime_matching_stampede_to_anvil_band_02_08\\results\\matched_target_indices.parquet`

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
python scripts\model_transfer.py --config experiments\EXP-036_modeling_stampede_to_anvil_band_02_08\config\exp036_modeling_stampede_to_anvil_band_02_08.json
```

## Outputs
- Metrics: `experiments\\EXP-036_modeling_stampede_to_anvil_band_02_08\\results\\metrics.json`

## Results Summary (proxy-only)
From `results/metrics.json`:
- No overlap rows after filters; metrics not computed (see limitations).

## Known Issues / Caveats
- Proxy-only: months are not configurable in the proxy manifest (single month per cluster).
- Zero overlap -> modeling skipped with explicit limitation.
