# EXP-059 Run Log  Dense alloc-only Huber diagnosis on authoritative v3 normalized peak memory transfer

**Run ID**: EXP-059_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_2024  
**Date**: 2026-03-12

## Objective
Test whether alloc-only overlap plus a Huber regressor improves the dense-sampled Anvil -> Conte normalized `peak_memory_fraction` transfer result.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-058):
  - `experiments/EXP-058_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_2024/results/matched_source_indices.parquet`
  - `experiments/EXP-058_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_2024/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Random seed: `2024`

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-059_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_2024/config/exp059_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_2024.json`
- Hardware metadata source: `config/clusters.json`
- Model: `HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=500)`
- Adaptation: `none`
- Sampling controls:
  - `max_rows_source = 600000`
  - `max_rows_target = 600000`
  - `sample_n_row_groups_per_file = 128`
- Modeling feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`

## Notes
- This run operationalizes the best-performing ad hoc dense diagnostic found so far.
- The goal is not to make a publication claim yet, but to determine whether feature-set simplification plus a more robust linear model can recover a non-negative target R^2.

## Execution
Planned repro command:
```bash
python scripts/model_transfer.py --config experiments/EXP-059_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_2024/config/exp059_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_2024.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10406152`
- Dependency: `afterok:10406151`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=64G`

## Outputs
- Metrics: `experiments/EXP-059_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_2024/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10406152` completed successfully.
- Final evaluation sizes:
  - source overlap rows after label filter: `18,682`
  - target overlap rows after label filter: `26,131`
  - source train: `14,946`
  - source test: `3,736`
  - target eval: `26,131`
- Source holdout performance:
  - `R^2 = -0.0030`
  - `MAE(log1p) = 0.0412`
  - `SMAPE = 11.07%`
- Target transfer performance:
  - `R^2 = -1.4949`
  - `MAE(log1p) = 0.1416`
  - `SMAPE = 97.76%`
- Target bootstrap `R^2` interval:
  - mean: `-1.4933`
  - 95% CI: `[-1.5563, -1.4371]`
- Target calibration note:
  - fitted target slope on log scale: `-0.7696`
- Interpretation:
  - The tracked alloc-only Huber run reproduced the same failure mode: broad overlap with nearly zero source signal and strongly negative target transfer.
  - The negative target slope indicates the cross-cluster response relationship is still badly misspecified even after simplifying the feature set.
