# EXP-049 Run Log  Modeling on authoritative v3 hardware CPU-standard overlap cohorts with normalized peak memory (repeat seed 2025)

**Run ID**: EXP-049_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2025  
**Date**: 2026-03-12

## Objective
Repeat the authoritative Anvil -> Conte transfer model under alternate random seed `2025` to test whether the positive `peak_memory_fraction` result persists.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-048):
  - `experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/results/matched_source_indices.parquet`
  - `experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Random seed: `2025`

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-049_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2025/config/exp049_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2025.json`
- Hardware metadata source: `config/clusters.json`
- Model: `Ridge(alpha=1.0)`
- Adaptation: `none`
- Overlap feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`

## Notes
- `peak_memory_fraction` is derived at analysis time as `peak_memory_gb / (node_memory_gb * nhosts)`.
- `peak_memory_gb` is inferred from `value_memused_max`; in the current authoritative parquet, that series is already GB-scale.
- The normalized label does not remove the cross-cluster measurement-semantic caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede).

## Execution
Planned repro command:
```bash
python scripts/model_transfer.py --config experiments/EXP-049_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2025/config/exp049_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2025.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405141`
- Dependency: `afterok:10405140`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Metrics: `experiments/EXP-049_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2025/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405141` completed successfully.
- Final evaluation sizes:
  - source overlap rows after label filter: `6,241`
  - target overlap rows after label filter: `3,271`
  - source train: `4,993`
  - source test: `1,248`
  - target eval: `3,271`
- Source holdout performance:
  - `R^2 = 0.0866`
  - `MAE(log1p) = 0.0726`
  - `SMAPE = 40.11%`
- Target transfer performance:
  - `R^2 = -2.1030`
  - `MAE(log1p) = 0.1727`
  - `SMAPE = 109.05%`
- Target bootstrap `R^2` interval:
  - mean: `-2.1049`
  - 95% CI: `[-2.3111, -1.9280]`
- Interpretation:
  - More overlap coverage did not help: despite a larger matched target cohort, target transfer collapsed badly and the bootstrap interval stayed far below zero.
  - Across repeated seeds so far, the normalized matched-regime baseline is not yet stable enough for a publication claim.
