# EXP-047 Run Log  Modeling on authoritative v3 hardware CPU-standard overlap cohorts with normalized peak memory (repeat seed 2024)

**Run ID**: EXP-047_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2024  
**Date**: 2026-03-12

## Objective
Repeat the authoritative Anvil -> Conte transfer model under alternate random seed `2024` to test whether the positive `peak_memory_fraction` result persists.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-046):
  - `experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/results/matched_source_indices.parquet`
  - `experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Random seed: `2024`

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-047_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2024/config/exp047_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2024.json`
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
python scripts/model_transfer.py --config experiments/EXP-047_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2024/config/exp047_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2024.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405113`
- Dependency: `afterok:10405112`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Metrics: `experiments/EXP-047_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2024/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405113` completed successfully.
- Final evaluation sizes:
  - source overlap rows after label filter: `2,486`
  - target overlap rows after label filter: `1,640`
  - source train: `1,989`
  - source test: `497`
  - target eval: `1,640`
- Source holdout performance:
  - `R^2 = 0.0613`
  - `MAE(log1p) = 0.0411`
  - `SMAPE = 12.38%`
- Target transfer performance:
  - `R^2 = -0.0346`
  - `MAE(log1p) = 0.0943`
  - `SMAPE = 56.42%`
- Target bootstrap `R^2` interval:
  - mean: `-0.0399`
  - 95% CI: `[-0.0741, -0.0063]`
- Interpretation:
  - The previously positive EXP-045 signal did not reproduce on this seed; target transfer turned slightly negative with a fully negative bootstrap interval.
  - Across repeated seeds so far, the normalized matched-regime baseline is not yet stable enough for a publication claim.
