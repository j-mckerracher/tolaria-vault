# EXP-043 Run Log  Modeling on authoritative v3 safe-feature overlap cohorts

**Run ID**: EXP-043_modeling_authoritative_v3_safe_features_band_02_08  
**Date**: 2026-03-12

## Objective
Train and evaluate the authoritative Anvil -> Conte transfer model on overlap cohorts defined only by the strict safe features from Phase 1.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-042):
  - `experiments/EXP-042_regime_matching_authoritative_v3_safe_features_band_02_08/results/matched_source_indices.parquet`
  - `experiments/EXP-042_regime_matching_authoritative_v3_safe_features_band_02_08/results/matched_target_indices.parquet`
- Label: `value_memused_max` with `log1p` transform (`label_proxy=false`)

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-043_modeling_authoritative_v3_safe_features_band_02_08/config/exp043_modeling_authoritative_v3_safe_features_band_02_08.json`
- Model: Ridge(alpha=1.0)
- Adaptation: none
- Safe feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`

## Execution
Planned repro command:
```powershell
python scripts\model_transfer.py --config experiments\EXP-043_modeling_authoritative_v3_safe_features_band_02_08\config\exp043_modeling_authoritative_v3_safe_features_band_02_08.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10404962`
- Dependency: `afterok:10404961`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Metrics: `experiments/EXP-043_modeling_authoritative_v3_safe_features_band_02_08/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10404962` completed successfully.
- Final evaluation sizes:
  - source train: `5,751`
  - source test: `1,438`
  - target eval: `2,450`
- Source holdout performance:
  - `R^2 = 0.2282`
  - `MAE(log1p) = 0.2541`
  - `SMAPE = 19.24%`
- Target transfer performance:
  - `R^2 = -4.2053`
  - `MAE(log1p) = 1.6822`
  - `SMAPE = 151.91%`
- Target bootstrap `R^2` interval:
  - mean: `-4.2113`
  - 95% CI: `[-4.5736, -3.8881]`
- Interpretation:
  - Switching the overlap cohorts to the strict safe-feature set materially improved target transfer relative to EXP-041 (`R^2 -11.8921 -> -4.2053`), but the target `R^2` remains decisively negative.
  - Safe-feature overlap alone is therefore not enough to support a defensible Anvil -> Conte transfer claim on raw `value_memused_max`.

## Known Issues / Caveats
- The label remains raw peak `value_memused_max`, not normalized `peak_memory_fraction`.
- This run isolates the effect of switching to the strict safe overlap features; it does not solve the missing hardware metadata problem.
