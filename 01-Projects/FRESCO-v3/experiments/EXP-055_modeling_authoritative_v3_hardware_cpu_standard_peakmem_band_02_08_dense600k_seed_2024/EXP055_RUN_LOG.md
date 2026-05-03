# EXP-055 Run Log  Dense-sampled modeling on authoritative v3 hardware CPU-standard overlap cohorts with normalized peak memory

**Run ID**: EXP-055_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_2024  
**Date**: 2026-03-12

## Objective
Test whether increasing authoritative sampling depth (`max_rows_source=max_rows_target=600000`, `sample_n_row_groups_per_file=128`) stabilizes the Anvil -> Conte normalized `peak_memory_fraction` transfer result.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-054):
  - `experiments/EXP-054_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_2024/results/matched_source_indices.parquet`
  - `experiments/EXP-054_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_2024/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Random seed: `2024`

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-055_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_2024/config/exp055_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_2024.json`
- Hardware metadata source: `config/clusters.json`
- Model: `Ridge(alpha=1.0)`
- Adaptation: `none`
- Sampling controls:
  - `max_rows_source = 600000`
  - `max_rows_target = 600000`
  - `sample_n_row_groups_per_file = 128`
- Overlap feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`

## Notes
- This run tests whether the positive EXP-045 result survives after reducing row-group sampling variance.
- `peak_memory_fraction` is derived at analysis time as `peak_memory_gb / (node_memory_gb * nhosts)`.
- `peak_memory_gb` is inferred from `value_memused_max`; in the current authoritative parquet, that series is already GB-scale.

## Execution
Planned repro command:
```bash
python scripts/model_transfer.py --config experiments/EXP-055_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_2024/config/exp055_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_2024.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405521`
- Dependency: `afterok:10405520`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=64G`

## Outputs
- Metrics: `experiments/EXP-055_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_2024/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405521` completed successfully.
- Final evaluation sizes:
  - source overlap rows after label filter: `5,904`
  - target overlap rows after label filter: `7,671`
  - source train: `4,723`
  - source test: `1,181`
  - target eval: `7,671`
- Source holdout performance:
  - `R^2 = 0.0694`
  - `MAE(log1p) = 0.0516`
  - `SMAPE = 24.11%`
- Target transfer performance:
  - `R^2 = -0.1047`
  - `MAE(log1p) = 0.0949`
  - `SMAPE = 66.71%`
- Target bootstrap `R^2` interval:
  - mean: `-0.1055`
  - 95% CI: `[-0.1272, -0.0881]`
- Interpretation:
  - Denser sampling improved the repeat-seed target error relative to EXP-047, but target transfer still remained definitively negative with a fully negative bootstrap interval.
  - The current evidence now suggests that row-group sampling variance is not the only reason the normalized Anvil -> Conte baseline fails to reproduce.
