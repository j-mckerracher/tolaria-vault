# EXP-038 Run Log — Anvil → Stampede modeling

**Run ID**: EXP-038_modeling_anvil_to_stampede_band_02_08  
**Date**: 2026-02-03  

## Objective
Single-month pair modeling for Anvil → Stampede using EXP-037 cohorts.

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`
- Cohorts (from EXP-037):
  - `experiments\\EXP-037_regime_matching_anvil_to_stampede_band_02_08\\results\\matched_source_indices.parquet`
  - `experiments\\EXP-037_regime_matching_anvil_to_stampede_band_02_08\\results\\matched_target_indices.parquet`

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
python scripts\model_transfer.py --config experiments\EXP-038_modeling_anvil_to_stampede_band_02_08\config\exp038_modeling_anvil_to_stampede_band_02_08.json
```

## Outputs
- Metrics: `experiments\\EXP-038_modeling_anvil_to_stampede_band_02_08\\results\\metrics.json`

## Results Summary (proxy-only)
From `results/metrics.json`:
- No overlap rows after filters; metrics not computed (see limitations).

## Known Issues / Caveats
- Proxy-only: months are not configurable in the proxy manifest (single month per cluster).
- Zero overlap -> modeling skipped with explicit limitation.
