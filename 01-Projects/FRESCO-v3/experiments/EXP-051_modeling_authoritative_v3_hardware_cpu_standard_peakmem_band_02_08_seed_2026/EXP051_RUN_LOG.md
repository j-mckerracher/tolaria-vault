# EXP-051 Run Log  Modeling on authoritative v3 hardware CPU-standard overlap cohorts with normalized peak memory (repeat seed 2026)

**Run ID**: EXP-051_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2026  
**Date**: 2026-03-12

## Objective
Repeat the authoritative Anvil -> Conte transfer model under alternate random seed `2026` to test whether the positive `peak_memory_fraction` result persists.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-050):
  - `experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/results/matched_source_indices.parquet`
  - `experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Random seed: `2026`

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-051_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2026/config/exp051_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2026.json`
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
python scripts/model_transfer.py --config experiments/EXP-051_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2026/config/exp051_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2026.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405143`
- Dependency: `afterok:10405142`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Metrics: `experiments/EXP-051_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2026/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405143` completed successfully.
- Final evaluation sizes:
  - source overlap rows after label filter: `1,885`
  - target overlap rows after label filter: `2,441`
  - source train: `1,508`
  - source test: `377`
  - target eval: `2,441`
- Source holdout performance:
  - `R^2 = 0.2886`
  - `MAE(log1p) = 0.0612`
  - `SMAPE = 33.50%`
- Target transfer performance:
  - `R^2 = -0.2882`
  - `MAE(log1p) = 0.0944`
  - `SMAPE = 62.11%`
- Target bootstrap `R^2` interval:
  - mean: `-0.2866`
  - 95% CI: `[-0.3788, -0.2020]`
- Interpretation:
  - Source holdout performance improved sharply on this seed, yet target transfer was still negative with a fully negative bootstrap interval.
  - Across repeated seeds so far, the normalized matched-regime baseline is not yet stable enough for a publication claim.
