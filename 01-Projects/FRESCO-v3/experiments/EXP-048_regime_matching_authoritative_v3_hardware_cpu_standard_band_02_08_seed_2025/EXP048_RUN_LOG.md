# EXP-048 Run Log  Regime matching on authoritative v3 with recovered hardware CPU-standard regime (repeat seed 2025)

**Run ID**: EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025  
**Date**: 2026-03-12

## Objective
Repeat the authoritative Anvil -> Conte overlap analysis under alternate random seed `2025` to test whether the hardware-aware overlap cohort is stable.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Random seed: `2025`

## Code & Environment
- Script: `scripts/regime_matching.py`
- Config: `experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/config/exp048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025.json`
- Hardware metadata source: `config/clusters.json`
- Overlap feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`

## Notes
- `partition` is recovered from the raw `queue` field at analysis time.
- `node_memory_gb`, `node_cores`, `gpu_count_per_node`, and `node_type` are recovered from `config/clusters.json`.
- Conte queue identifiers remain anonymized, so recovered hardware metadata uses cluster-wide defaults there.

## Execution
Planned repro command:
```bash
python scripts/regime_matching.py --config experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/config/exp048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405140`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Overlap report: `experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/results/overlap_report.json`
- Matched indices:
  - `.../results/matched_source_indices.parquet`
  - `.../results/matched_target_indices.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405140` completed successfully.
- Final cohort sizes:
  - source jobs: `11,696`
  - target jobs: `5,624`
  - source overlap jobs: `7,888`
  - target overlap jobs: `3,312`
- Overlap diagnostics:
  - domain classifier AUC: `0.9073`
  - target overlap coverage: `58.89%`
- KS statistics on the full sampled cohorts:
  - `ncores`: `0.4162`
  - `nhosts`: `0.1433`
  - `timelimit_sec`: `0.3677`
  - `runtime_sec`: `0.3235`
  - `queue_time_sec`: `0.6561`
  - `runtime_fraction`: `0.4088`
- KS statistics within the overlap band:
  - `ncores`: `0.1658`
  - `nhosts`: `0.0000`
  - `timelimit_sec`: `0.5861`
  - `runtime_sec`: `0.5375`
  - `queue_time_sec`: `0.7045`
  - `runtime_fraction`: `0.5495`
- Interpretation:
  - This seed widened the overlap region substantially, but the within-overlap timing KS values remained very high.
  - The recovered hardware regime remains more defensible than the older proxy regime, but these repeated seeds still show large within-overlap timing mismatch.
