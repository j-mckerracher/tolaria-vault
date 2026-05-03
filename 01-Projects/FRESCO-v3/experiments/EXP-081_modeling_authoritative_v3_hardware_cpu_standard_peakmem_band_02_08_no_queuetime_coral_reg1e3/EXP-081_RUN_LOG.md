# EXP-081 Run Log -- Completed higher-regularization CORAL adaptation modeling on the first frozen no-queue universe

**Run ID**: EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3
**Date**: 2026-03-13
**Owner**: jmckerra

## Objective
Test whether increasing CORAL regularization to `1e-3` removes the outlier-like universe-1 instability seen in EXP-079 while keeping the stronger five-feature no-queue design unchanged.

## Hypothesis (if experiment)
If the catastrophic EXP-079 failure was driven mainly by an unstable or over-aggressive CORAL transform at `reg = 1e-6`, then a higher-regularization variant should preserve the positive universe-1 signal instead of blowing up a small number of target predictions.

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
- Adaptation: CORAL with `reg = 1e-3`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/config/exp081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3.json`
- Base config copied from: `EXP-079`
- Git commit (pipeline): `0ad0cb1c0c56385664347de15760b3b3c3593fb0`
- Git commit (analysis): `0ad0cb1c0c56385664347de15760b3b3c3593fb0`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp081_noqt_coral_reg1e3_model.slurm`
- Job IDs: `10408290`
- Start / end time (UTC): `2026-03-13T05:39:15Z / 2026-03-13T05:40:50Z`

## Outputs
- Output root: `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/results/`
- Manifests: `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/manifests/`
- Validation reports: `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/validation/`

## Results Summary
- `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/results/metrics.json`: source-test `R^2 = 0.2092` and target `R^2 = -59.6547`.
- `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/results/metrics.json`: bootstrap target `R^2` 95% CI = `[-91.2324, -32.5571]` with bootstrap mean `-60.2188`.
- `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/results/metrics.json`: target slope = `0.0091`, target `bias_log = 0.0613`, and target `mae_log = 0.1644`.
- `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/results/metrics.json`: this run reused the frozen overlap cohort with `6995` matched source jobs and `2455` target evaluation jobs after the positive-label filter.
- For context, the no-adaptation baseline `EXP-063` on this same frozen cohort achieved target `R^2 = +0.1070`, so `EXP-081` remained dramatically worse than doing no adaptation at all.
- Relative to EXP-079, higher regularization shrank the magnitude of the universe-1 failure dramatically (`-46520.6724 -> -59.6547`) but did not rescue the design; the target predictions still lost meaningful slope and remained unusable for transfer claims.

## Validation Summary
- Job `10408290` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, validation files, and SLURM stdout/stderr (`experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/logs/slurm-10408290.out`).
- Execution provenance was captured in `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/validation/git_commit.txt`, `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/validation/python_version.txt`, `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/validation/pip_freeze.txt`, `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/validation/conda_env.yml`, and `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/validation/host_info.txt`.
- No runtime errors were reported in `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/logs/model_transfer.log`.

## Known Issues / Caveats
- A100-80GB group quota was saturated at submission time, so this short experiment used the validated `training` partition fallback rather than the primary production partition.
- This run changes only the CORAL regularization strength relative to EXP-079; overlap cohorts, feature columns, random seed, and ridge model settings stay fixed.
- `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/manifests/run_metadata.json` still leaves git/environment fields null because the remote pipeline directory was a synced snapshot rather than a git checkout; use the validation files as the authoritative provenance record.
- The normalized label still carries the cross-cluster measurement-semantics caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede).
- Even with stronger regularization, target `R^2` stayed catastrophically negative and target slope collapsed to `0.0091`, so linear CORAL still does not preserve the previously positive universe-1 transfer.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline`
3. `python scripts/model_transfer.py --config experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/config/exp081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3.json`
