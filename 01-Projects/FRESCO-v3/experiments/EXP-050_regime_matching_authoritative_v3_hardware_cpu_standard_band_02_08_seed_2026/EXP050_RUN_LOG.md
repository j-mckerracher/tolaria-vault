# EXP-050 Run Log  Regime matching on authoritative v3 with recovered hardware CPU-standard regime (repeat seed 2026)

**Run ID**: EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026  
**Date**: 2026-03-12

## Objective
Repeat the authoritative Anvil -> Conte overlap analysis under alternate random seed `2026` to test whether the hardware-aware overlap cohort is stable.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Random seed: `2026`

## Code & Environment
- Script: `scripts/regime_matching.py`
- Config: `experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/config/exp050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026.json`
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
python scripts/regime_matching.py --config experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/config/exp050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405142`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Overlap report: `experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/results/overlap_report.json`
- Matched indices:
  - `.../results/matched_source_indices.parquet`
  - `.../results/matched_target_indices.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405142` completed successfully.
- Final cohort sizes:
  - source jobs: `7,263`
  - target jobs: `6,096`
  - source overlap jobs: `3,433`
  - target overlap jobs: `2,461`
- Overlap diagnostics:
  - domain classifier AUC: `0.9271`
  - target overlap coverage: `40.37%`
- KS statistics on the full sampled cohorts:
  - `ncores`: `0.6188`
  - `nhosts`: `0.1218`
  - `timelimit_sec`: `0.3610`
  - `runtime_sec`: `0.2758`
  - `queue_time_sec`: `0.6381`
  - `runtime_fraction`: `0.3066`
- KS statistics within the overlap band:
  - `ncores`: `0.2511`
  - `nhosts`: `0.0106`
  - `timelimit_sec`: `0.4170`
  - `runtime_sec`: `0.3701`
  - `queue_time_sec`: `0.6912`
  - `runtime_fraction`: `0.3758`
- Interpretation:
  - This seed landed between EXP-046 and EXP-048 on both separability and overlap coverage, but queue-time mismatch still dominated inside the overlap band.
  - The recovered hardware regime remains more defensible than the older proxy regime, but these repeated seeds still show large within-overlap timing mismatch.
