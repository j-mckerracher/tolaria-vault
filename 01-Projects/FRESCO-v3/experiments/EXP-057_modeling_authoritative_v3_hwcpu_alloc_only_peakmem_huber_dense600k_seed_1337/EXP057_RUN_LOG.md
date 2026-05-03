# EXP-057 Run Log  Dense alloc-only Huber diagnosis on authoritative v3 normalized peak memory transfer

**Run ID**: EXP-057_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_1337  
**Date**: 2026-03-12

## Objective
Test whether alloc-only overlap plus a Huber regressor improves the dense-sampled Anvil -> Conte normalized `peak_memory_fraction` transfer result.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Cohorts (from EXP-056):
  - `experiments/EXP-056_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_1337/results/matched_source_indices.parquet`
  - `experiments/EXP-056_regime_matching_authoritative_v3_hwcpu_alloc_only_dense600k_seed_1337/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Random seed: `1337`

## Code & Environment
- Script: `scripts/model_transfer.py`
- Config: `experiments/EXP-057_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_1337/config/exp057_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_1337.json`
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
python scripts/model_transfer.py --config experiments/EXP-057_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_1337/config/exp057_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_1337.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10406150`
- Dependency: `afterok:10406149`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=64G`

## Outputs
- Metrics: `experiments/EXP-057_modeling_authoritative_v3_hwcpu_alloc_only_peakmem_huber_dense600k_seed_1337/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10406150` completed successfully.
- Final evaluation sizes:
  - source overlap rows after label filter: `19,121`
  - target overlap rows after label filter: `25,939`
  - source train: `15,297`
  - source test: `3,824`
  - target eval: `25,939`
- Source holdout performance:
  - `R^2 = -0.0046`
  - `MAE(log1p) = 0.0411`
  - `SMAPE = 11.51%`
- Target transfer performance:
  - `R^2 = -0.6492`
  - `MAE(log1p) = 0.1190`
  - `SMAPE = 93.00%`
- Target bootstrap `R^2` interval:
  - mean: `-0.6491`
  - 95% CI: `[-0.6831, -0.6182]`
- Target calibration note:
  - fitted target slope on log scale: `-3.6942`
- Interpretation:
  - Dropping the timing/performance features and switching to Huber did not rescue transfer; instead, source holdout performance collapsed to ~0 and target transfer stayed strongly negative.
  - The negative target slope indicates the cross-cluster response relationship is still badly misspecified even after simplifying the feature set.
