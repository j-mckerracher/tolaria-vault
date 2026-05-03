# EXP-082 Run Log -- Completed higher-regularization CORAL adaptation modeling on the second frozen no-queue universe

**Run ID**: EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024
**Date**: 2026-03-13
**Owner**: jmckerra

## Objective
Test whether increasing CORAL regularization to `1e-3` yields a cleaner second-universe comparison after EXP-080 showed that the naive `1e-6` setting barely changed the harder baseline.

## Hypothesis (if experiment)
If the second-universe CORAL result was damped by an unstable or poorly conditioned transform at `reg = 1e-6`, then a higher-regularization variant should provide a clearer signal about whether linear covariance adaptation can help at all on the harder frozen universe.

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
- Adaptation: CORAL with `reg = 1e-3`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/config/exp082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024.json`
- Base config copied from: `EXP-080`
- Git commit (pipeline): `0ad0cb1c0c56385664347de15760b3b3c3593fb0`
- Git commit (analysis): `0ad0cb1c0c56385664347de15760b3b3c3593fb0`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp082_noqt_coral_reg1e3_u2_model.slurm`
- Job IDs: `10408291`
- Start / end time (UTC): `2026-03-13T05:39:15Z / 2026-03-13T05:40:50Z`

## Outputs
- Output root: `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/results/`
- Manifests: `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/manifests/`
- Validation reports: `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/validation/`

## Results Summary
- `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/results/metrics.json`: source-test `R^2 = 0.0842` and target `R^2 = -0.0633`.
- `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/results/metrics.json`: bootstrap target `R^2` 95% CI = `[-0.1090, -0.0156]` with bootstrap mean `-0.0636`.
- `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/results/metrics.json`: target slope = `0.4460`, target `bias_log = 0.0192`, and target `mae_log = 0.0888`.
- `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/results/metrics.json`: this run reused the frozen overlap cohort with `11133` matched source jobs and `1686` target evaluation jobs after the positive-label filter.
- Relative to EXP-080, the higher-regularization retry was effectively unchanged (`-0.0613 -> -0.0633`), so increasing `adaptation.reg` does not rescue the second frozen universe either.

## Validation Summary
- Job `10408291` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, validation files, and SLURM stdout/stderr (`experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/logs/slurm-10408291.out`).
- Execution provenance was captured in `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/validation/git_commit.txt`, `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/validation/python_version.txt`, `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/validation/pip_freeze.txt`, `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/validation/conda_env.yml`, and `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/validation/host_info.txt`.
- No runtime errors were reported in `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/logs/model_transfer.log`.

## Known Issues / Caveats
- A100-80GB group quota was saturated at submission time, so this short experiment used the validated `training` partition fallback rather than the primary production partition.
- This run changes only the CORAL regularization strength relative to EXP-080; overlap cohorts, feature columns, random seed, and ridge model settings stay fixed.
- `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/manifests/run_metadata.json` still leaves git/environment fields null because the remote pipeline directory was a synced snapshot rather than a git checkout; use the validation files as the authoritative provenance record.
- The normalized label still carries the cross-cluster measurement-semantics caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede).
- Higher regularization did not improve the harder universe at all; the target score remained fully negative with essentially unchanged slope and bootstrap interval.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline`
3. `python scripts/model_transfer.py --config experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/config/exp082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024.json`
