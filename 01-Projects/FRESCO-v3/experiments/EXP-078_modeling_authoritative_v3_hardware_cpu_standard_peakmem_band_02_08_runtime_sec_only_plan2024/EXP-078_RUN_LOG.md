# EXP-078 Run Log -- Completed runtime-sec-only modeling on the second frozen universe

**Run ID**: EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024
**Date**: 2026-03-12
**Owner**: jmckerra

## Objective
Measure whether the runtime-sec-only feature recipe recovers positive or at least non-catastrophic target transfer on the second frozen universe where EXP-071 failed.

## Hypothesis (if experiment)
If the second-universe failure was mostly driven by `runtime_fraction` and `timelimit_sec`, then this reduced feature set should improve calibration relative to EXP-071 even if it does not fully restore the first-universe score.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Frozen sampling plan: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp070_hwcpu_standard_300k_24_seed2024.json`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Cohorts: `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/results/matched_source_indices.parquet` and `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Modeling split seed: `1337`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/config/exp078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024.json`
- Git commit (pipeline): `b85eea66f15f91024af7f660f4025b5b2a9e5f85`
- Git commit (analysis): `b85eea66f15f91024af7f660f4025b5b2a9e5f85`
- Conda env: `fresco_v2`
- Python: `Python 3.10.19`
- Package lock: `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp078_runtime_sec_u2_model.slurm`
- Job IDs: `10407627`
- Start / end time (UTC): `2026-03-12T23:30:45Z / 2026-03-12T23:32:23Z`

## Outputs
- Output root: `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/results/`
- Manifests: `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/manifests/`
- Validation reports: `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/validation/`

## Results Summary
- `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/results/metrics.json`: source-test `R^2 = 0.0479` and target `R^2 = -1.6086`.
- `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/results/metrics.json`: bootstrap target `R^2` 95% CI = `[-1.7662, -1.4565]` with bootstrap mean `-1.6110`.
- `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/results/metrics.json`: target slope = `-0.9409`, target `bias_log = -0.1017`, and target `mae_log = 0.1250`.
- `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/results/metrics.json`: this run reused the EXP-077 overlap cohort with `11761` matched source jobs and `4575` target evaluation jobs after the positive-label filter, down from `12526` source and `4626` target jobs in `EXP-077/results/overlap_report.json`.

## Validation Summary
- Job `10407627` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, and validation files (`experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/logs/slurm-10407627.out`).
- Execution provenance was captured in `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/validation/git_commit.txt`, `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/validation/python_version.txt`, `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/validation/pip_freeze.txt`, and `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/validation/conda_env.yml`.
- No runtime errors were reported in `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/logs/model_transfer.log`.

## Known Issues / Caveats
- The runtime-sec-only pruning did not rescue the second frozen universe; target transfer became dramatically worse than the already-negative EXP-071 baseline and the fitted target slope flipped negative.
- `scripts\model_transfer.py` filters `peak_memory_fraction` to non-null positive values before training; on this universe that removed `765 / 12526` source overlap jobs (`6.1%`) and `51 / 4626` target overlap jobs (`1.1%`). EXP-076 had no analogous source-side dropout (`7504 -> 7504`), so the cross-universe comparison carries a label-availability caveat if those dropped source jobs are not missing completely at random.
- `experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/manifests/run_metadata.json` still leaves git/environment fields null because the remote pipeline directory was a synced snapshot rather than a git checkout; use the validation files as the authoritative provenance record.
- This result strongly suggests that further feature pruning alone is unlikely to be enough; the next corrective branch should shift toward explicit adaptation rather than another timing-only ablation.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline && sbatch exp078_runtime_sec_u2_model.slurm`
3. `python scripts/model_transfer.py --config experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/config/exp078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024.json`
