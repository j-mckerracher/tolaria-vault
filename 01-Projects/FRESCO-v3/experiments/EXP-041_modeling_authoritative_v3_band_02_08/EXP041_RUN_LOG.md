# EXP-041 Run Log  Modeling on authoritative v3 overlap cohorts

**Run ID**: EXP-041_modeling_authoritative_v3_band_02_08  
**Date**: 2026-03-11

## Objective
Train and evaluate the Anvil -> Conte transfer model on authoritative v3 data using the EXP-040 overlap cohorts.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-040):
  - `experiments/EXP-040_regime_matching_authoritative_v3_band_02_08/results/matched_source_indices.parquet`
  - `experiments/EXP-040_regime_matching_authoritative_v3_band_02_08/results/matched_target_indices.parquet`
- Label: `value_memused_max` with `log1p` transform (`label_proxy=false`)

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-041_modeling_authoritative_v3_band_02_08/config/exp041_modeling_authoritative_v3_band_02_08.json`
- Model: Ridge(alpha=1.0)
- Adaptation: none

## Execution
Planned repro command:
```powershell
python scripts\model_transfer.py --config experiments\EXP-041_modeling_authoritative_v3_band_02_08\config\exp041_modeling_authoritative_v3_band_02_08.json
```

Submitted on Gilbreth:
- Initial SLURM job: `10404579` on `a100-80gb` (`blocked behind EXP-040`, later cancelled)
- First training retry: `10404590` (`COMPLETED`, but invalid due pre-fix undersampling)
- Final successful retry: `10404598`
- Dependency: `afterok:10404597`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=4 --mem=32G`

## Outputs
- Metrics: `experiments/EXP-041_modeling_authoritative_v3_band_02_08/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10404590` completed but inherited the undersampled overlap cohorts from the pre-fix `EXP-040` run (`2` source overlap jobs, `33` target overlap jobs), so no usable metrics were produced.
- After fixing `scripts/fresco_data_loader.py` and rerunning `EXP-040`, job `10404598` completed successfully.
- Final evaluation sizes:
  - source train: `3,786`
  - source test: `946`
  - target eval: `1,915`
- Source holdout performance:
  - `R^2 = 0.3103`
  - `MAE(log1p) = 0.2118`
  - `SMAPE = 14.93%`
- Target transfer performance:
  - `R^2 = -11.8921`
  - `MAE(log1p) = 2.4287`
  - `SMAPE = 176.39%`
- Interpretation: even with the larger authoritative overlap cohorts, direct Anvil -> Conte transfer on raw `value_memused_max` remains very poor in the current activity-based regime definition.

## Known Issues / Caveats
- The label is authoritative in the sense that it is derived from the production v3 parquet, but it is still raw peak `value_memused_max`, not the planned normalized `peak_memory_fraction` target.
- Cross-cluster memory semantics still differ (`memory_includes_cache` is true on anvil and false on conte/stampede).
