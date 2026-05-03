# EXP-052 Run Log  Dense-sampled regime matching on authoritative v3 hardware CPU-standard cohorts

**Run ID**: EXP-052_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_1337  
**Date**: 2026-03-12

## Objective
Increase authoritative sampling depth (`max_rows_per_cluster=600000`, `sample_n_row_groups_per_file=128`) and rerun the Anvil -> Conte hardware CPU-standard overlap analysis to reduce row-group sampling variance.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Random seed: `1337`

## Code & Environment
- Script: `scripts/regime_matching.py`
- Config: `experiments/EXP-052_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_1337/config/exp052_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_1337.json`
- Hardware metadata source: `config/clusters.json`
- Sampling controls:
  - `max_rows_per_cluster = 600000`
  - `sample_n_row_groups_per_file = 128`
- Overlap feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`

## Notes
- This run is the first stabilization attempt after EXP-046 to EXP-051 showed that the 300k / 24-row-group baseline was not stable across seeds.
- `partition` is recovered from the raw `queue` field at analysis time.
- `node_memory_gb`, `node_cores`, `gpu_count_per_node`, and `node_type` are recovered from `config/clusters.json`.

## Execution
Planned repro command:
```bash
python scripts/regime_matching.py --config experiments/EXP-052_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_1337/config/exp052_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_1337.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405518`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=64G`

## Outputs
- Overlap report: `experiments/EXP-052_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_1337/results/overlap_report.json`
- Matched indices:
  - `.../results/matched_source_indices.parquet`
  - `.../results/matched_target_indices.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405518` completed successfully.
- Final cohort sizes:
  - source jobs: `29,601`
  - target jobs: `31,781`
  - source overlap jobs: `18,403`
  - target overlap jobs: `11,874`
- Overlap diagnostics:
  - domain classifier AUC: `0.9378`
  - target overlap coverage: `37.36%`
- Interpretation:
  - Denser sampling greatly expanded both cohorts and widened the overlap region relative to EXP-044, but it did not reduce separability enough to make the overlap geometry convincingly stable.
  - Denser sampling alone did not make the overlap geometry obviously more transferable.
