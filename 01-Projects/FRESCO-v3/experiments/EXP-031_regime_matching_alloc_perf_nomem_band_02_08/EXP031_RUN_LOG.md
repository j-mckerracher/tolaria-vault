# EXP-031 Run Log — Overlap band [0.2,0.8]

**Run ID**: EXP-031_regime_matching_alloc_perf_nomem_band_02_08  
**Date**: 2026-02-03  

## Objective
Overlap diagnostics for alloc+perf-no-mem features using propensity band [0.2,0.8].

## Inputs
- Dataset label: `local_job_partials_snapshot` (proxy-only)
- Input manifest: `experiments\\EXP-016_feature_matrix\\manifests\\input_files.json`

## Code & Environment
- Script: `scripts\\regime_matching.py`
- Regime (proxy): `cpu_standard := (value_gpu_cnt<=0 and value_gpu_sum<=0)`

## Execution
Repro command:
```powershell
python scripts\regime_matching.py --config experiments\EXP-031_regime_matching_alloc_perf_nomem_band_02_08\config\exp031_regime_matching_alloc_perf_nomem_band_02_08.json
```

## Outputs
- Overlap report: `experiments\\EXP-031_regime_matching_alloc_perf_nomem_band_02_08\\results\\overlap_report.json`
- Matched indices:
  - `...\\results\\matched_source_indices.parquet`
  - `...\\results\\matched_target_indices.parquet`
- Provenance:
  - `...\\manifests\\run_metadata.json`
  - `...\\manifests\\input_files_used.json`
  - `...\\validation\\python_version.txt`
  - `...\\validation\\pip_freeze.txt`

## Results Summary (proxy-only)
From `results/overlap_report.json`:
- AUC: **0.9895**
- Target overlap coverage: **0.3213** (n_target_overlap=544)

## Known Issues / Caveats
- Proxy-only: regime definition uses GPU counters due to missing partition metadata.
