# EXP-083 Run Log -- Completed quantile-output adaptation modeling on the first frozen no-queue universe

**Run ID**: EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output
**Date**: 2026-03-13
**Owner**: jmckerra

## Objective
Test a zero-label post-prediction quantile-matching correction on the first frozen no-queue universe after both CORAL variants failed to preserve the previously positive result.

## Hypothesis (if experiment)
If the universe-1 adaptation failures are driven mainly by a small number of extreme target prediction errors rather than by a globally wrong median, then a monotone quantile-output correction should clip those outliers while preserving the otherwise good central fit seen in EXP-063.

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
- Adaptation: quantile-output matching with `n_quantiles = 100`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/config/exp083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output.json`
- Base config copied from: `EXP-063`
- Git commit (pipeline): `f02c78dad1c3e1d71f3ee5f9dc50e060fdc69d09`
- Git commit (analysis): `f02c78dad1c3e1d71f3ee5f9dc50e060fdc69d09`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch /home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/run_exp083_quantile.slurm`
- Job IDs: `10408738`
- Start / end time (UTC): `2026-03-13T06:26:42Z / 2026-03-13T06:28:11Z`

## Outputs
- Output root: `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/results/`
- Manifests: `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/manifests/`
- Validation reports: `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/`

## Results Summary
- `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/results/metrics.json`: source-test `R^2 = 0.2091` and target `R^2 = -0.1026`.
- `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/results/metrics.json`: bootstrap target `R^2` 95% CI = `[-0.1380, -0.0722]` with bootstrap mean `-0.1039`.
- `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/results/metrics.json`: target slope = `0.8099`, target `bias_log = -0.0402`, and target `mae_log = 0.1106`.
- `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/results/metrics.json`: this run reused the frozen overlap cohort with `6995` matched source jobs and `2455` target evaluation jobs after the positive-label filter.
- For context, the no-adaptation baseline `EXP-063` on this same frozen cohort achieved target `R^2 = +0.1070`, so `EXP-083` flipped the previously positive universe-1 result negative even though it was far less harmful than the CORAL failures (`EXP-079 = -46520.6724`, `EXP-081 = -59.6547`).
- `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/results/metrics.json`: the adaptation record shows `n_quantiles_requested = 100` and `n_quantiles_used = 100`.

## Validation Summary
- Job `10408738` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, validation files, and SLURM stdout/stderr (`experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/logs/slurm_10408738.out` and `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/logs/slurm_10408738.err`).
- Execution provenance was captured in `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/git_commit.txt`, `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/git_status.txt`, `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/source_sync_note.txt`, `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/python_version.txt`, `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/pip_freeze.txt`, `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/conda_env.yml`, and `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/validation/host_info.txt`.
- No runtime errors were reported in `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/logs/model_transfer.log` or `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/logs/slurm_10408738.err`.

## Known Issues / Caveats
- A100-80GB group quota was saturated at submission time, so this short experiment used the validated `training` partition fallback rather than the primary production partition.
- This run changes only the output-space adaptation relative to `EXP-063`; overlap cohorts, feature columns, random seed, and ridge model settings stayed fixed.
- `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/manifests/run_metadata.json` still leaves git fields null because the remote pipeline directory was a synced snapshot rather than a git checkout; use the validation files as the authoritative provenance record.
- The normalized label still carries the cross-cluster measurement-semantics caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede).
- `quantile_output` uses the source-train prediction distribution as the reference distribution; on universe 1 that preserved a nonzero slope but still underperformed the unadapted baseline badly, so it does not rescue the previously positive frozen-universe result.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline`
3. `python scripts/model_transfer.py --config experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/config/exp083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output.json`
