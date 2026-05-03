# Phase 2 — Workload Taxonomy + Regime Matching (EXP-017 / EXP-020 / EXP-022)

## Goal
Construct defensible cross-cluster cohorts by:
1) defining a shared workload regime, and
2) restricting evaluation to an **overlap region** where source and target feature support is comparable.

## Evidence artifacts
Run folders:
- `experiments\EXP-017_regime_matching\`
- `experiments\EXP-020_regime_matching_alloc_perf_nomem\` (ablation: alloc+perf, exclude memused; job-level aggregation)
- `experiments\EXP-022_regime_matching_alloc_only_joblevel\` (rerun: allocations-only; job-level aggregation)
- `experiments\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\` (ablation: alloc+perf, no memused; overlap band [0.1,0.9])

Reproduce:
```powershell
python scripts\regime_matching.py --config experiments\EXP-017_regime_matching\config\exp017_regime_matching.json
python scripts\regime_matching.py --config experiments\EXP-020_regime_matching_alloc_perf_nomem\config\exp020_regime_matching_alloc_perf_nomem.json
python scripts\regime_matching.py --config experiments\EXP-022_regime_matching_alloc_only_joblevel\config\exp022_regime_matching_alloc_only_joblevel.json
python scripts\regime_matching.py --config experiments\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\config\exp024_regime_matching_alloc_perf_nomem_band_01_09.json
```

Key outputs:
- Overlap report: `experiments\EXP-017_regime_matching\results\overlap_report.json`
- Matched cohort indices:
  - `...\results\matched_source_indices.parquet`
  - `...\results\matched_target_indices.parquet`
- Provenance:
  - `...\manifests\run_metadata.json`
  - `...\manifests\input_files_used.json`
  - `...\validation\python_version.txt`, `...\validation\pip_freeze.txt`

## Regime definition used (local proxy)
Because the local job_partials snapshot does not include authoritative `partition`, `node_type`, `gpu_count_per_node`, etc., this run uses a conservative proxy:
- `cpu_standard := (value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`

This must be replaced by the real taxonomy rules when running on full v3 shards.

## Overlap method
- Train a domain classifier (logistic regression) to predict domain (source vs target) from the Phase-1-safe features.
- Define overlap as samples with propensity:
  - **P(domain = source | x) in [0.2, 0.8]**

## Results (from `overlap_report.json`)
### EXP-017 (alloc+perf including memused)
- Domain separability (AUC): **1.0**
- Target overlap coverage (Conte covered by Anvil support under this proxy): **~6.8%**

### EXP-020 (alloc+perf excluding memused; job-level)
- Domain separability (AUC): **~0.9895**
- Target overlap coverage: **~0.321**

### EXP-022 (allocations-only; job-level)
- Domain separability (AUC): **~0.8025**
- Target overlap coverage: **1.0**

### EXP-024 (alloc+perf excluding memused; job-level; overlap band [0.1,0.9])
- Domain separability (AUC): **~0.9895**
- Target overlap coverage: **~0.416**

Observed KS distances are large for several features (see JSON), indicating severe shift.

## Implications / limitations
- With AUC≈1 and only ~6.8% overlap coverage (EXP-017), any “global” Anvil→Conte transfer claim is not defensible on this snapshot.
- Even when excluding memused counters and aggregating to job-level (EXP-020), the domain classifier remains highly separable (AUC≈0.99) and overlap coverage is still limited (~32%).
- Allocations-only features (EXP-022) can yield full target overlap coverage, but this does **not** imply feasible transfer for memory outcomes (see job-level Phase 3 rerun: `experiments\EXP-023_modeling_alloc_only_joblevel\`).
- These Phase 2 results are **proxy-only** and should be rerun on the true `/depot/.../chunks-v3/` shards where regime can be defined using `partition/node_type/gpu metadata`.

