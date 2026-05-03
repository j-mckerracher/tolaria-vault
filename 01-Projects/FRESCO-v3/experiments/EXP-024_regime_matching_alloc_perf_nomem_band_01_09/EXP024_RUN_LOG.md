# EXP-024 Regime Matching (Alloc + Perf, no memused, overlap band [0.1, 0.9]) — Run Log

**Run ID**: EXP-024_regime_matching_alloc_perf_nomem_band_01_09  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 2 ablation: widen overlap band to **[0.1, 0.9]** for Anvil → Conte using alloc+perf aggregate features (excluding all `*memused*` counters), operating at **job-level** (collapse `job_partials` to one row per `jid`).

## Regime
- `cpu_standard` (local proxy): `(value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Feature set (no memused)
- allocations: `ncores`, `timelimit`
- perf aggregates: `value_block_{cnt,sum}`, `value_cpuuser_{cnt,sum}`, `value_gpu_{cnt,sum}`, `value_nfs_{cnt,sum}`

## Overlap method
- Logistic regression propensity model (`class_weight=balanced`)
- Overlap band: **[0.1, 0.9]**

## Execution
```powershell
python scripts\regime_matching.py --config experiments\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\config\exp024_regime_matching_alloc_perf_nomem_band_01_09.json
```

## Outputs
- `results\overlap_report.json`
- `results\matched_source_indices.parquet`
- `results\matched_target_indices.parquet`
- Provenance: `manifests\run_metadata.json`, `manifests\input_files_used.json`, `validation\{python_version.txt,pip_freeze.txt}`

## Headline results
(from `results\overlap_report.json`)
- Domain classifier AUC: **0.9895**
- Target overlap coverage: **0.4158**
- n_source=94, n_source_overlap=70; n_target=1693, n_target_overlap=704

## Note on unit of analysis
The local `job_partials` snapshot contains multiple rows per `jid` (partials/time slices). This run collapses to **job-level** by aggregating numeric columns per `jid` using `max()`.

## Caveats
- Local proxy only (job_partials), not authoritative v3 shards.
- Regime definition is a proxy; must be replaced with taxonomy rules when running on `/depot/.../chunks-v3/`.
