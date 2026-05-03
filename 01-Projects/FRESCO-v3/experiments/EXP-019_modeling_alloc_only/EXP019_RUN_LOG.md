# EXP-019 Phase 3 Modeling (Allocations-only Baseline) — Run Log

**Run ID**: EXP-019_modeling_alloc_only  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Phase 3 baseline: train a simple model on the *matched overlap cohort* (Phase 2) and evaluate zero-shot transfer from **Anvil → Conte**.

This run is explicitly **proxy-only** because it uses job_partials and a proxy label.

## Inputs
- Parquet input manifest: `experiments\EXP-016_feature_matrix\manifests\input_files.json`
- Overlap cohorts (from Phase 2 allocations-only run):
  - `experiments\EXP-018_regime_matching_alloc_only\results\matched_source_indices.parquet`
  - `experiments\EXP-018_regime_matching_alloc_only\results\matched_target_indices.parquet`

## Regime
- `cpu_standard` (local proxy): `(value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

## Label (proxy)
- `value_memused_max`
- transform: `log1p`

## Features (allocations-only)
- `ncores`, `timelimit` (log1p applied)

## Model
- Ridge regression (median impute + standardize)

## Execution
```powershell
python scripts\model_transfer.py --config experiments\EXP-019_modeling_alloc_only\config\exp019_modeling_alloc_only.json
```

## Outputs
- Metrics: `experiments\EXP-019_modeling_alloc_only\results\metrics.json`
- Predictions:
  - `...\results\predictions_source_test.parquet`
  - `...\results\predictions_target.parquet`
- Provenance:
  - `...\manifests\run_metadata.json`
  - `...\manifests\input_files_used.json`
  - `...\validation\python_version.txt`, `...\validation\pip_freeze.txt`

## Headline results (proxy)
From `results\metrics.json`:
- Source heldout R² (within Anvil overlap cohort): **-0.041**
- Target R² (Conte overlap cohort): **-5.51** (bootstrap CI ~[-5.86, -5.16])

## Interpretation / Caveats
- Even with high feature overlap under the allocations-only propensity model (EXP-018), transfer performance is extremely poor on this proxy label.
- This is consistent with the overall v3 thesis: regime matching + overlap are necessary but may not be sufficient; label/conditional shift likely dominates.
- This result is not publication-grade because the label is a proxy and the dataset is a local snapshot; rerun on true v3 shards is required.
