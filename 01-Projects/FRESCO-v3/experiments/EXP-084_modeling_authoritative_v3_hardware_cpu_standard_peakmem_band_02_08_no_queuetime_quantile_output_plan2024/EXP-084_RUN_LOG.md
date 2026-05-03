# EXP-084 Run Log -- Completed quantile-output adaptation modeling on the second frozen no-queue universe

**Run ID**: EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024
**Date**: 2026-03-13
**Owner**: jmckerra

## Objective
Test the same zero-label post-prediction quantile-matching correction on the second frozen no-queue universe after both CORAL variants failed to improve the harder baseline.

## Hypothesis (if experiment)
If the remaining universe-2 error is mostly a prediction-distribution shape mismatch rather than an input-covariance problem, then a monotone quantile-output correction should give a more informative second-universe result than any of the CORAL runs.

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
- Adaptation: quantile-output matching with `n_quantiles = 100`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/config/exp084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024.json`
- Base config copied from: `EXP-071`
- Git commit (pipeline): `f02c78dad1c3e1d71f3ee5f9dc50e060fdc69d09`
- Git commit (analysis): `f02c78dad1c3e1d71f3ee5f9dc50e060fdc69d09`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch /home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/run_exp084_quantile.slurm`
- Job IDs: `10408739`
- Start / end time (UTC): `2026-03-13T06:26:41Z / 2026-03-13T06:28:11Z`

## Outputs
- Output root: `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/results/`
- Manifests: `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/manifests/`
- Validation reports: `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/`

## Results Summary
- `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/results/metrics.json`: source-test `R^2 = 0.0842` and target `R^2 = -0.0285`.
- `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/results/metrics.json`: bootstrap target `R^2` 95% CI = `[-0.0572, -0.0096]` with bootstrap mean `-0.0310`.
- `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/results/metrics.json`: target slope = `0.6150`, target `bias_log = -0.0199`, and target `mae_log = 0.0891`.
- `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/results/metrics.json`: this run reused the frozen overlap cohort with `11133` matched source jobs and `1686` target evaluation jobs after the positive-label filter.
- Relative to the no-adaptation baseline `EXP-071 = -0.0639` and the CORAL retries `EXP-080 = -0.0613` and `EXP-082 = -0.0633`, quantile-output matching improved the harder universe materially but still remained fully below zero, so it does not rescue the transfer claim.
- `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/results/metrics.json`: the adaptation record shows `n_quantiles_requested = 100` and `n_quantiles_used = 100`.

## Validation Summary
- Job `10408739` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, validation files, and SLURM stdout/stderr (`experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/logs/slurm_10408739.out` and `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/logs/slurm_10408739.err`).
- Execution provenance was captured in `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/git_commit.txt`, `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/git_status.txt`, `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/source_sync_note.txt`, `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/python_version.txt`, `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/pip_freeze.txt`, `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/conda_env.yml`, and `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/validation/host_info.txt`.
- No runtime errors were reported in `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/logs/model_transfer.log` or `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/logs/slurm_10408739.err`.

## Known Issues / Caveats
- A100-80GB group quota was saturated at submission time, so this short experiment used the validated `training` partition fallback rather than the primary production partition.
- This run changes only the output-space adaptation relative to `EXP-071`; overlap cohorts, feature columns, random seed, and ridge model settings stayed fixed.
- `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/manifests/run_metadata.json` still leaves git fields null because the remote pipeline directory was a synced snapshot rather than a git checkout; use the validation files as the authoritative provenance record.
- The normalized label still carries the cross-cluster measurement-semantics caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede).
- `quantile_output` uses the source-train prediction distribution as the reference distribution; on universe 2 this partially corrected the slope mismatch, but target `R^2` remained fully negative and therefore still below the acceptance bar for a transferable zero-label adaptation.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline`
3. `python scripts/model_transfer.py --config experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/config/exp084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024.json`
