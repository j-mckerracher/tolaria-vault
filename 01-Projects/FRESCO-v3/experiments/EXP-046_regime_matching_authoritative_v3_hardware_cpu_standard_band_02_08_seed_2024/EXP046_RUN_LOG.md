# EXP-046 Run Log  Regime matching on authoritative v3 with recovered hardware CPU-standard regime (repeat seed 2024)

**Run ID**: EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024  
**Date**: 2026-03-12

## Objective
Repeat the authoritative Anvil -> Conte overlap analysis under alternate random seed `2024` to test whether the hardware-aware overlap cohort is stable.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Random seed: `2024`

## Code & Environment
- Script: `scripts/regime_matching.py`
- Config: `experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/config/exp046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024.json`
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
python scripts/regime_matching.py --config experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/config/exp046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405112`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Overlap report: `experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/results/overlap_report.json`
- Matched indices:
  - `.../results/matched_source_indices.parquet`
  - `.../results/matched_target_indices.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405112` completed successfully.
- Final cohort sizes:
  - source jobs: `16,680`
  - target jobs: `6,136`
  - source overlap jobs: `2,516`
  - target overlap jobs: `1,652`
- Overlap diagnostics:
  - domain classifier AUC: `0.9394`
  - target overlap coverage: `26.92%`
- KS statistics on the full sampled cohorts:
  - `ncores`: `0.3027`
  - `nhosts`: `0.1338`
  - `timelimit_sec`: `0.5087`
  - `runtime_sec`: `0.5589`
  - `queue_time_sec`: `0.6794`
  - `runtime_fraction`: `0.5538`
- KS statistics within the overlap band:
  - `ncores`: `0.1483`
  - `nhosts`: `0.0024`
  - `timelimit_sec`: `0.5573`
  - `runtime_sec`: `0.5316`
  - `queue_time_sec`: `0.6299`
  - `runtime_fraction`: `0.4068`
- Interpretation:
  - This repeat seed produced nearly the same AUC as EXP-044 but a smaller overlap cohort and lower Conte coverage.
  - The recovered hardware regime remains more defensible than the older proxy regime, but these repeated seeds still show large within-overlap timing mismatch.
