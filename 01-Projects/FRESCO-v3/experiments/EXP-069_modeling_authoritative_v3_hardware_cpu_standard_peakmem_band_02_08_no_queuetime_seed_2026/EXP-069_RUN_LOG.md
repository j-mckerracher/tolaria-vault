# EXP-069 Run Log -- Completed modeling repeat on the frozen authoritative no-queue cohort (seed 2026)

**Run ID**: EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026  
**Date**: 2026-03-12  
**Owner**: jmckerra

## Objective
Evaluate the authoritative Anvil -> Conte normalized peak-memory transfer baseline on the frozen EXP-062 overlap cohort using modeling split seed `2026` after removing `queue_time_sec` from both the overlap and modeling feature sets.

## Hypothesis (if experiment)
If the earlier instability was driven mainly by queue-time-induced overlap drift plus raw sampling drift, then freezing the EXP-062 cohort and removing `queue_time_sec` should yield a repeatable positive target `R^2` across modeling split seeds.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Frozen sampling plan: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp044_hwcpu_standard_300k_24_seed1337.json`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31
- Cohorts: `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/matched_source_indices.parquet` and `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Modeling split seed: `2026`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/config/exp069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026.json`
- Git commit (pipeline): `aa2457958db8ec9a0735da5f64129d00155a62d1`
- Git commit (analysis): `aa2457958db8ec9a0735da5f64129d00155a62d1`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp069_noqt_model.slurm`
- Job IDs: `10407081`
- Start / end time (UTC): `2026-03-12T20:51:32Z / 2026-03-12T20:53:22Z`

## Outputs
- Output root: `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/results/`
- Manifests: `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/manifests/`
- Validation reports: `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/validation/`

## Results Summary
- `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/results/metrics.json`: source-test `R^2 = 0.1075` and target `R^2 = 0.1108`.
- `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/results/metrics.json`: bootstrap target `R^2` 95% CI = `[0.0804, 0.1365]` with bootstrap mean `0.1103`.
- `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/results/metrics.json`: target slope = `1.0227`, target `bias_log = -0.0135`, and target `mae_log = 0.0880`.
- `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/results/metrics.json`: this repeat reused the frozen EXP-062 overlap cohort with `6995` matched source jobs and `2455` target evaluation jobs.

## Validation Summary
- Job `10407081` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, and validation files (`experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/logs/slurm-10407081.out`).
- Execution provenance was captured in `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/validation/git_commit.txt`, `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/validation/python_version.txt`, and `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/validation/pip_freeze.txt`.
- No runtime errors were reported in `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/logs/model_transfer.log`.

## Known Issues / Caveats
- `experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/manifests/run_metadata.json` leaves git/environment fields null because `/home/jmckerra/Code/FRESCO-Pipeline` on Gilbreth was a synced snapshot rather than a git checkout; use the files under `validation/` as the authoritative provenance record.
- These repeats quantify stability across modeling split seeds on a frozen overlap cohort; they do not by themselves measure sensitivity to alternative frozen sampling universes.
- The normalized label still carries the cross-cluster measurement-semantics caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede), so broader generalization still requires care.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline && sbatch exp069_noqt_model.slurm`
3. `python scripts/model_transfer.py --config experiments/EXP-069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026/config/exp069_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_seed_2026.json`
