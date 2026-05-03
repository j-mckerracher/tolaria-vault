# EXP-017 Regime Matching / Overlap Diagnostics — Run Log

**Run ID**: EXP-017_regime_matching  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 2: construct an overlap-aware matched cohort between clusters via a domain-classifier propensity model, restricted to a chosen workload regime.

## Regime
- `cpu_standard`
- Local proxy definition used (because true node_type/partition/gpu_alloc metadata is not present in job_partials):
  - `cpu_standard := (value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Inputs
- Manifest of parquet inputs (SHA256s recorded in EXP-016):
  - `experiments\EXP-016_feature_matrix\manifests\input_files.json`
- Source cluster: `anvil`
- Target cluster: `conte`

## Features used for overlap model
(from `experiments\EXP-017_regime_matching\config\exp017_regime_matching.json`)
- `ncores`, `timelimit`
- `value_block_{cnt,sum}`
- `value_cpuuser_{cnt,sum}`
- `value_memused_{cnt,sum}`
- `value_memused_minus_diskcache_{cnt,sum}`
- `value_nfs_{cnt,sum}`

## Propensity model
- Logistic regression (`class_weight=balanced`)
- Overlap band: **[0.2, 0.8]** (user-confirmed)

## Execution
```powershell
python scripts\regime_matching.py --config experiments\EXP-017_regime_matching\config\exp017_regime_matching.json
```

Logs:
- `experiments\EXP-017_regime_matching\logs\regime_matching.log`

## Outputs
- `experiments\EXP-017_regime_matching\results\overlap_report.json`
- `experiments\EXP-017_regime_matching\results\matched_indices.parquet`
- `experiments\EXP-017_regime_matching\results\matched_source_indices.parquet`
- `experiments\EXP-017_regime_matching\results\matched_target_indices.parquet`
- `experiments\EXP-017_regime_matching\manifests\input_files_used.json`
- `experiments\EXP-017_regime_matching\manifests\run_metadata.json`
- `experiments\EXP-017_regime_matching\validation\{python_version.txt,pip_freeze.txt}`

## Key results
See `results\overlap_report.json` for AUC + overlap coverage and KS diagnostics.

## Caveats
- This is a **local proxy** run (job_partials), not the authoritative v3 shards.
- Regime definition is necessarily approximate in this snapshot; Phase 2 must be re-run on full v3 where partition/node_type/gpu metadata exist.
