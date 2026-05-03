# EXP-022 Regime Matching (Allocations Only, job-level) — Run Log

**Run ID**: EXP-022_regime_matching_alloc_only_joblevel  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 2 rerun of allocations-only overlap diagnostics **at job granularity** (collapse `job_partials` to one row per `jid` before fitting propensity model), for Anvil → Conte.

## Regime
- `cpu_standard` (local proxy): `(value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Feature set
- `ncores`, `timelimit`

## Overlap method
- Logistic regression propensity model (`class_weight=balanced`)
- Overlap band: **[0.2, 0.8]**

## Execution
```powershell
python scripts\regime_matching.py --config experiments\EXP-022_regime_matching_alloc_only_joblevel\config\exp022_regime_matching_alloc_only_joblevel.json
```

## Outputs
- `results\overlap_report.json`
- `results\matched_source_indices.parquet`
- `results\matched_target_indices.parquet`
- Provenance: `manifests\run_metadata.json`, `manifests\input_files_used.json`, `validation\{python_version.txt,pip_freeze.txt}`

## Headline results
(from `results\overlap_report.json`)
- Domain classifier AUC: **0.8025**
- Target overlap coverage: **1.0000**
- n_source=94, n_source_overlap=75; n_target=1693, n_target_overlap=1693

## Note on unit of analysis
The local `job_partials` snapshot contains multiple rows per `jid` (partials/time slices). This run collapses to **job-level** by aggregating numeric columns per `jid` using `max()`.

## Caveats
- Local proxy only (job_partials), not authoritative v3 shards.
- Regime definition is a proxy; must be replaced with taxonomy rules when running on `/depot/.../chunks-v3/`.
