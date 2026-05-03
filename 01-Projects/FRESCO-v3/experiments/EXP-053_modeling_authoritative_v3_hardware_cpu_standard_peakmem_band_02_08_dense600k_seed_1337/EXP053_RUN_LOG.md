# EXP-053 Run Log  Dense-sampled modeling on authoritative v3 hardware CPU-standard overlap cohorts with normalized peak memory

**Run ID**: EXP-053_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_1337  
**Date**: 2026-03-12

## Objective
Test whether increasing authoritative sampling depth (`max_rows_source=max_rows_target=600000`, `sample_n_row_groups_per_file=128`) stabilizes the Anvil -> Conte normalized `peak_memory_fraction` transfer result.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-052):
  - `experiments/EXP-052_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_1337/results/matched_source_indices.parquet`
  - `experiments/EXP-052_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_dense600k_seed_1337/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Random seed: `1337`

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-053_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_1337/config/exp053_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_1337.json`
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
python scripts/model_transfer.py --config experiments/EXP-053_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_1337/config/exp053_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_1337.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405519`
- Dependency: `afterok:10405518`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=64G`

## Outputs
- Metrics: `experiments/EXP-053_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_dense600k_seed_1337/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405519` completed successfully.
- Final evaluation sizes:
  - source overlap rows after label filter: `17,499`
  - target overlap rows after label filter: `11,714`
  - source train: `13,999`
  - source test: `3,500`
  - target eval: `11,714`
- Source holdout performance:
  - `R^2 = 0.1521`
  - `MAE(log1p) = 0.0522`
  - `SMAPE = 29.66%`
- Target transfer performance:
  - `R^2 = -0.8817`
  - `MAE(log1p) = 0.1366`
  - `SMAPE = 91.48%`
- Target bootstrap `R^2` interval:
  - mean: `-0.8807`
  - 95% CI: `[-0.9372, -0.8255]`
- Interpretation:
  - The original positive EXP-045 split did not survive denser sampling: on the same seed, target transfer became clearly negative with a tightly negative bootstrap interval.
  - The current evidence now suggests that row-group sampling variance is not the only reason the normalized Anvil -> Conte baseline fails to reproduce.
