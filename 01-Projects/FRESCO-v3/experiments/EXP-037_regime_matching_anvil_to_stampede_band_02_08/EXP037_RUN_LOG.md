# EXP-037 Run Log — Anvil → Stampede overlap

**Run ID**: EXP-037_regime_matching_anvil_to_stampede_band_02_08  
**Date**: 2026-02-03  

## Objective
Single-month pair overlap diagnostics for Anvil → Stampede using band [0.2,0.8].

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`

## Code & Environment
- Script: `scripts\\regime_matching.py`
- Regime (proxy): `cpu_standard := (value_gpu_cnt<=0 and value_gpu_sum<=0)`

## Execution
Repro command:
```powershell
python scripts\regime_matching.py --config experiments\EXP-037_regime_matching_anvil_to_stampede_band_02_08\config\exp037_regime_matching_anvil_to_stampede_band_02_08.json
```

## Outputs
- Overlap report: `experiments\\EXP-037_regime_matching_anvil_to_stampede_band_02_08\\results\\overlap_report.json`

## Results Summary (proxy-only)
From `results/overlap_report.json`:
- AUC: **1.0**
- Target overlap coverage: **0.0** (n_target_overlap=0)

## Known Issues / Caveats
- Proxy-only: months are not configurable in the proxy manifest (single month per cluster).
