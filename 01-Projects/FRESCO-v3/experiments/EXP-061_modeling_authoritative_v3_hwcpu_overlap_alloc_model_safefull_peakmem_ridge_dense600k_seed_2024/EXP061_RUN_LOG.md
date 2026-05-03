# EXP-061 Run Log  Decoupled alloc-overlap plus safe-full Ridge diagnosis on authoritative v3 normalized peak memory transfer

**Run ID**: EXP-061_modeling_authoritative_v3_hwcpu_overlap_alloc_model_safefull_peakmem_ridge_dense600k_seed_2024  
**Date**: 2026-03-12

## Objective
Test whether the dense Anvil -> Conte normalized `peak_memory_fraction` transfer result improves when Phase 2 keeps the broader alloc-only overlap cohorts, but Phase 3 restores the richer safe-full timing feature set used by the earlier positive single-split baseline.

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
- Config: `experiments/EXP-061_modeling_authoritative_v3_hwcpu_overlap_alloc_model_safefull_peakmem_ridge_dense600k_seed_2024/config/exp061_modeling_authoritative_v3_hwcpu_overlap_alloc_model_safefull_peakmem_ridge_dense600k_seed_2024.json`
- Hardware metadata source: `config/clusters.json`
- Model: `Ridge(alpha=1.0)`
- Adaptation: `none`
- Sampling controls:
  - `max_rows_source = 600000`
  - `max_rows_target = 600000`
  - `sample_n_row_groups_per_file = 128`
- Phase 2 overlap feature set (reused from EXP-058):
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
- Phase 3 modeling feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`

## Notes
- This run is the formal decoupled-feature follow-up to the dense alloc-only diagnosis and the saved-prediction label-semantics analysis.
- The key question is whether broader alloc-only overlap can be retained while the richer timing features recover target calibration inside the matched cohorts.
- Unlike EXP-057/059, this run restores the safe-full timing features from the earlier positive baseline while keeping the denser matched alloc-only cohorts.

## Execution
Planned repro command:
```bash
python scripts/model_transfer.py --config experiments/EXP-061_modeling_authoritative_v3_hwcpu_overlap_alloc_model_safefull_peakmem_ridge_dense600k_seed_2024/config/exp061_modeling_authoritative_v3_hwcpu_overlap_alloc_model_safefull_peakmem_ridge_dense600k_seed_2024.json
```

Submitted on Gilbreth:
- Submitted job: `10406644`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=64G`

## Outputs
- Metrics: `experiments/EXP-061_modeling_authoritative_v3_hwcpu_overlap_alloc_model_safefull_peakmem_ridge_dense600k_seed_2024/results/metrics.json`
- Predictions:
  - `.../results/predictions_source_test.parquet`
  - `.../results/predictions_target.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10406644` completed successfully.
- Final evaluation sizes:
  - source overlap rows after label filter: `18,682`
  - target overlap rows after label filter: `26,131`
  - source train: `14,946`
  - source test: `3,736`
  - target eval: `26,131`
- Source holdout performance:
  - `R^2 = 0.0359`
  - `MAE(log1p) = 0.0399`
  - `SMAPE = 9.98%`
- Target transfer performance:
  - `R^2 = -0.8824`
  - `MAE(log1p) = 0.1217`
  - `SMAPE = 92.49%`
- Target bootstrap `R^2` interval:
  - mean: `-0.8812`
  - 95% CI: `[-0.9218, -0.8433]`
- Target calibration note:
  - fitted target slope on log scale: `-0.4331`
- Interpretation:
  - Restoring the richer safe-full timing features again recovered modest positive source holdout signal, but target transfer still remained decisively negative.
  - This seed improved relative to the alloc-only Huber run, but the fully negative bootstrap interval shows the decoupled design still does not support a transfer claim.
