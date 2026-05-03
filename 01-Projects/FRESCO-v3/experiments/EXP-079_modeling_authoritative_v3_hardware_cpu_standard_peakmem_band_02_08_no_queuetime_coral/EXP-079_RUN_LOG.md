# EXP-079 Run Log -- Completed CORAL adaptation modeling on the first frozen no-queue universe

**Run ID**: EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral
**Date**: 2026-03-13
**Owner**: jmckerra

## Objective
Test whether explicit CORAL feature adaptation on the stronger five-feature frozen no-queue design preserves or improves the previously positive universe-1 transfer result without reverting to more feature pruning.

## Hypothesis (if experiment)
If the remaining universe-specific failure mode is unresolved source/target covariance shift inside the matched cohort, then CORAL alignment in the existing log1p-transformed five-feature space should retain the positive EXP-063 baseline while providing a more adaptation-aware comparison point for harder universes.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Frozen sampling plan: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp044_hwcpu_standard_300k_24_seed1337.json`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Cohorts: `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/matched_source_indices.parquet and experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Modeling split seed: `1337`
- Adaptation: CORAL with `reg = 1e-6`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/config/exp079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral.json`
- Base config copied from: `EXP-063`
- Git commit (pipeline): `f9e36c499794a4c84cfc3239f6c84b51e5124d9e`
- Git commit (analysis): `f9e36c499794a4c84cfc3239f6c84b51e5124d9e`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp079_noqt_coral_model.slurm`
- Job IDs: `10408222`
- Start / end time (UTC): `2026-03-13T05:11:43Z / 2026-03-13T05:13:41Z`

## Outputs
- Output root: `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/results/`
- Manifests: `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/manifests/`
- Validation reports: `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/validation/`

## Results Summary
- `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/results/metrics.json`: source-test `R^2 = 0.2081` and target `R^2 = -46520.6724`.
- `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/results/metrics.json`: bootstrap target `R^2` 95% CI = `[-71141.6891, -25470.7576]` with bootstrap mean `-46949.8472`.
- `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/results/metrics.json`: target slope = `-0.0003`, target `bias_log = -2.1325`, and target `mae_log = 2.2062`.
- `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/results/metrics.json`: this run reused the frozen overlap cohort with `6995` matched source jobs and `2455` target evaluation jobs after the positive-label filter.
- Relative to the non-adapted EXP-063 baseline, CORAL with `reg = 1e-6` destroyed the previously positive universe-1 transfer signal even though the source holdout fit remained strong, indicating severe target-side instability rather than a source-model collapse.

## Validation Summary
- Job `10408222` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, validation files, and copied SLURM stdout/stderr (`experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/logs/slurm-10408222.out`).
- Execution provenance was captured in `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/validation/git_commit.txt`, `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/validation/python_version.txt`, `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/validation/pip_freeze.txt`, `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/validation/conda_env.yml`, and `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/validation/host_info.txt`.
- No runtime errors were reported in `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/logs/model_transfer.log`.

## Known Issues / Caveats
- A100-80GB group quota was saturated at submission time, so this short experiment used the validated `training` partition fallback rather than the primary production partition.
- CORAL support already exists in scripts\model_transfer.py, but this first authoritative run shows that `reg = 1e-6` can produce catastrophic target failures even when source holdout fit remains healthy.
- `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/manifests/run_metadata.json` still leaves git/environment fields null because the remote pipeline directory was a synced snapshot rather than a git checkout; use the validation files as the authoritative provenance record.
- The normalized label still carries the cross-cluster measurement-semantics caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede).
- The target `mdae_log` remained small (`0.0816`) despite the catastrophic target `R^2`, which points to a small number of extreme target prediction failures or numerical outliers; the next sensible CORAL follow-up is a higher-regularization sensitivity rather than another feature-pruning branch.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline`
3. `python scripts/model_transfer.py --config experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/config/exp079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral.json`
