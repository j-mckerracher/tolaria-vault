# EXP-045 Run Log  Modeling on authoritative v3 hardware CPU-standard overlap cohorts with normalized peak memory

**Run ID**: EXP-045_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08  
**Date**: 2026-03-12

## Objective
Train and evaluate the authoritative Anvil -> Conte transfer model on hardware CPU-standard overlap cohorts using the normalized `peak_memory_fraction` label.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-044):
  - `experiments/EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08/results/matched_source_indices.parquet`
  - `experiments/EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-045_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08/config/exp045_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08.json`
- Hardware metadata source: `config/clusters.json`
- Model: Ridge(alpha=1.0)
- Adaptation: none
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
```powershell
python scripts\model_transfer.py --config experiments\EXP-045_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08\config\exp045_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405059`
- Dependency: `afterok:10405058`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Metrics: `experiments/EXP-045_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405059` completed successfully.
- Final evaluation sizes:
  - source train: `5,609`
  - source test: `1,402`
  - target eval: `2,435`
- Source holdout performance:
  - `R^2 = 0.1414`
  - `MAE(log1p) = 0.0367`
  - `SMAPE = 17.98%`
- Target transfer performance:
  - `R^2 = 0.0878`
  - `MAE(log1p) = 0.0886`
  - `SMAPE = 80.19%`
- Target bootstrap `R^2` interval:
  - mean: `0.0864`
  - 95% CI: `[0.0556, 0.1132]`
- Interpretation:
  - This is the first positive authoritative Anvil -> Conte transfer result in the current workstream.
  - Switching from raw `value_memused_max` to normalized `peak_memory_fraction`, together with the recovered `hardware_cpu_standard` regime, changed target transfer from clearly negative to modestly positive.
  - The result is promising rather than final: it still needs repeated-split confirmation and careful discussion of the remaining measurement-semantics mismatch.
