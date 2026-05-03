# EXP-020 Regime Matching (Alloc + Perf, no memused) — Run Log

**Run ID**: EXP-020_regime_matching_alloc_perf_nomem  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 2 ablation: build overlap-aware matched cohorts for **Anvil → Conte** using Phase-1-safe allocation + performance aggregate features, explicitly excluding all `*memused*` counters to avoid label leakage in downstream Phase 3.

## Regime
- `cpu_standard` (local proxy): `(value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Inputs
- Parquet input manifest (SHA256s recorded in EXP-016):
  - `experiments\EXP-016_feature_matrix\manifests\input_files.json`

## Feature set (no memused)
(from `config\exp020_regime_matching_alloc_perf_nomem.json`)
- allocations: `ncores`, `timelimit`
- perf aggregates: `value_block_{cnt,sum}`, `value_cpuuser_{cnt,sum}`, `value_gpu_{cnt,sum}`, `value_nfs_{cnt,sum}`

## Propensity / overlap method
- Logistic regression (`class_weight=balanced`)
- Overlap band: **[0.2, 0.8]** (user-confirmed)

## Execution
```powershell
python scripts\regime_matching.py --config experiments\EXP-020_regime_matching_alloc_perf_nomem\config\exp020_regime_matching_alloc_perf_nomem.json
```

## Outputs
- `results\overlap_report.json`
- `results\matched_indices.parquet`
- `results\matched_source_indices.parquet`
- `results\matched_target_indices.parquet`
- Provenance:
  - `manifests\run_metadata.json`
  - `manifests\input_files_used.json`
  - `validation\{python_version.txt,pip_freeze.txt}`

## Headline results
(from `results\overlap_report.json`)
- Domain classifier AUC: **0.9895**
- Target overlap coverage (Conte in overlap band): **0.3213**

## Note on unit of analysis
The local `job_partials` snapshot contains multiple rows per `jid` (partials/time slices). This run collapses to **job-level** by aggregating numeric columns per `jid` using `max()` before fitting the propensity model.

## Caveats
- Local proxy only (job_partials), not authoritative v3 shards.
- Regime definition is a proxy; must be replaced with taxonomy rules when running on `/depot/.../chunks-v3/`.
