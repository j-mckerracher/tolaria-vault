# EXP-080 Run Log -- Completed CORAL adaptation modeling on the second frozen no-queue universe

**Run ID**: EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024
**Date**: 2026-03-13
**Owner**: jmckerra

## Objective
Test whether CORAL adaptation can rescue the harder second frozen-universe failure on the stronger five-feature no-queue design before we broaden scope or prune features again.

## Hypothesis (if experiment)
If the second-universe failure is primarily unresolved covariance shift inside the matched no-queue cohort, then CORAL alignment in the existing log1p-transformed five-feature space should materially improve the negative EXP-071 baseline without sacrificing frozen-universe comparability.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Frozen sampling plan: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp070_hwcpu_standard_300k_24_seed2024.json`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Cohorts: `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/matched_source_indices.parquet and experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Modeling split seed: `1337`
- Adaptation: CORAL with `reg = 1e-6`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/config/exp080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024.json`
- Base config copied from: `EXP-071`
- Git commit (pipeline): `f9e36c499794a4c84cfc3239f6c84b51e5124d9e`
- Git commit (analysis): `f9e36c499794a4c84cfc3239f6c84b51e5124d9e`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp080_noqt_coral_u2_model.slurm`
- Job IDs: `10408223`
- Start / end time (UTC): `2026-03-13T05:11:43Z / 2026-03-13T05:13:41Z`

## Outputs
- Output root: `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/results/`
- Manifests: `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/manifests/`
- Validation reports: `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/validation/`

## Results Summary
- `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/results/metrics.json`: source-test `R^2 = 0.0842` and target `R^2 = -0.0613`.
- `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/results/metrics.json`: bootstrap target `R^2` 95% CI = `[-0.1066, -0.0139]` with bootstrap mean `-0.0617`.
- `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/results/metrics.json`: target slope = `0.4473`, target `bias_log = 0.0190`, and target `mae_log = 0.0887`.
- `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/results/metrics.json`: this run reused the frozen overlap cohort with `11133` matched source jobs and `1686` target evaluation jobs after the positive-label filter.
- Relative to the non-adapted EXP-071 baseline, CORAL with `reg = 1e-6` changed the second-universe target score only trivially (`-0.0639 -> -0.0613`), so it did not provide a meaningful rescue.

## Validation Summary
- Job `10408223` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, validation files, and copied SLURM stdout/stderr (`experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/logs/slurm-10408223.out`).
- Execution provenance was captured in `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/validation/git_commit.txt`, `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/validation/python_version.txt`, `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/validation/pip_freeze.txt`, `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/validation/conda_env.yml`, and `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/validation/host_info.txt`.
- No runtime errors were reported in `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/logs/model_transfer.log`.

## Known Issues / Caveats
- A100-80GB group quota was saturated at submission time, so this short experiment used the validated `training` partition fallback rather than the primary production partition.
- CORAL support already exists in scripts\model_transfer.py, but this run shows that the naive `reg = 1e-6` setting does not materially improve the harder second frozen universe relative to the non-adapted baseline.
- `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/manifests/run_metadata.json` still leaves git/environment fields null because the remote pipeline directory was a synced snapshot rather than a git checkout; use the validation files as the authoritative provenance record.
- The normalized label still carries the cross-cluster measurement-semantics caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede).
- Because the bootstrap interval remained fully below zero, this result does not support a claim that naive CORAL rescues the harder second frozen universe; the next sensible follow-up is a higher-regularization sensitivity rather than treating adaptation as solved.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline`
3. `python scripts/model_transfer.py --config experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/config/exp080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024.json`
