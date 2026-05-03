# EXP-018 Regime Matching (Allocations Only) — Run Log

**Run ID**: EXP-018_regime_matching_alloc_only  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 2 sensitivity check: compute overlap coverage using only allocation-like features (`ncores`, `timelimit`) to see if overlap improves relative to using perf metrics.

## Regime
- `cpu_standard` (same local proxy as EXP-017):
  - `cpu_standard := (value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Execution
```powershell
python scripts\regime_matching.py --config experiments\EXP-018_regime_matching_alloc_only\config\exp018_regime_matching_alloc_only.json
```

## Key outputs
- `experiments\EXP-018_regime_matching_alloc_only\results\overlap_report.json`
- `...\results\matched_source_indices.parquet`
- `...\results\matched_target_indices.parquet`
- `...\manifests\input_files_used.json`
- `...\logs\regime_matching.log`

## Headline results
(see `results\overlap_report.json`)
- Domain classifier AUC: ~0.613
- Target overlap coverage (Conte within overlap band [0.2,0.8]): ~0.972

## Interpretation
- Using only allocations yields very high apparent overlap, but this may be misleading for transfer of memory outcomes (it ignores strong performance/behavioral signals).
- This supports Phase 3 doing ablations: allocations-only vs allocations+perf, always reporting overlap coverage and shift diagnostics.
