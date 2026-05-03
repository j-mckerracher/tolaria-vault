# EXP-056 Run Log  Dense alloc-only overlap diagnosis on authoritative v3 hardware CPU-standard cohorts

**Run ID**: EXP-056_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_1337  
**Date**: 2026-03-12

## Objective
Test whether removing scheduler/performance timing features from overlap matching reduces cross-cluster separability on the dense-sampled Anvil -> Conte hardware CPU-standard comparison.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Random seed: `1337`

## Code & Environment
- Script: `scripts/regime_matching.py`
- Config: `experiments/EXP-056_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_1337/config/exp056_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_1337.json`
- Hardware metadata source: `config/clusters.json`
- Sampling controls:
  - `max_rows_per_cluster = 600000`
  - `sample_n_row_groups_per_file = 128`
- Overlap feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`

## Notes
- This run follows the dense-sampling diagnosis, which suggested `queue_time_sec` and `runtime_fraction` remain major mismatch drivers.
- `partition` is recovered from the raw `queue` field at analysis time.

## Execution
Planned repro command:
```bash
python scripts/regime_matching.py --config experiments/EXP-056_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_1337/config/exp056_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_1337.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10406149`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=64G`

## Outputs
- Overlap report: `experiments/EXP-056_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_1337/results/overlap_report.json`
- Matched indices:
  - `.../results/matched_source_indices.parquet`
  - `.../results/matched_target_indices.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10406149` completed successfully.
- Final cohort sizes:
  - source jobs: `29,601`
  - target jobs: `31,781`
  - source overlap jobs: `20,025`
  - target overlap jobs: `26,227`
- Overlap diagnostics:
  - domain classifier AUC: `0.8571`
  - target overlap coverage: `82.52%`
- KS statistics on the full sampled cohorts:
  - `ncores`: `0.4061`
  - `nhosts`: `0.1260`
  - `timelimit_sec`: `0.4127`
- KS statistics within the overlap band:
  - `ncores`: `0.1221`
  - `nhosts`: `0.0000`
  - `timelimit_sec`: `0.6006`
- Interpretation:
  - Alloc-only matching greatly broadened overlap coverage, but `timelimit_sec` still remained badly mismatched inside the overlap band.
  - Broader overlap alone did not imply a more transferable target regime.
