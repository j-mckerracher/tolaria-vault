# EXP-070 Run Log -- Completed second frozen-universe regime matching for authoritative v3 hardware CPU-standard cohorts without queue_time_sec

**Run ID**: EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024  
**Date**: 2026-03-12  
**Owner**: jmckerra

## Objective
Test whether the stable no-queue Anvil -> Conte overlap geometry from EXP-062 holds on a second frozen `300k / 24` sampled universe built from a different sampling seed.

## Hypothesis (if experiment)
If the EXP-062 success is not specific to a single frozen universe, then a second frozen plan should still produce comparable overlap coverage and a similarly usable matched cohort after dropping `queue_time_sec`.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Frozen sampling plan: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp070_hwcpu_standard_300k_24_seed2024.json`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`

## Code & Environment
- Script: `scripts\regime_matching.py`
- Config: `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/config/exp070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024.json`
- Git commit (pipeline): `167f2da5940b63c34d862cfbc6bfb4189121c443`
- Git commit (analysis): `167f2da5940b63c34d862cfbc6bfb4189121c443`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp070_noqt_plan2024.slurm`
- Job IDs: `10407310` (superseded broken wrapper attempt), `10407316` (successful execution)
- Start / end time (UTC): `2026-03-12T21:42:23Z / 2026-03-12T21:44:10Z` for the successful run

## Outputs
- Output root: `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/`
- Manifests: `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/manifests/`
- Validation reports: `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/validation/`

## Results Summary
- `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/overlap_report.json`: domain classifier AUC = `0.9294` and target overlap coverage = `27.66%`.
- `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/overlap_report.json`: source overlap = `11898 / 16680` jobs and target overlap = `1697 / 6136` jobs.
- `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/overlap_report.json`: the remaining within-overlap KS values worsened relative to EXP-062, especially `runtime_fraction = 0.6093`, `runtime_sec = 0.5492`, and `timelimit_sec = 0.5416`.
- `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/logs/slurm-10407316.out`: the second frozen universe replayed `241,089` Anvil raw rows (`17,346` jobs) and `101,776` Conte raw rows (`6,136` jobs), producing a materially different cohort from EXP-062.

## Validation Summary
- Job `10407310` was canceled before meaningful execution because the first generated wrapper captured local shell interpolation incorrectly.
- Job `10407316` completed with exit code `0` and wrote the expected overlap artifacts, manifests, and validation files (`experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/logs/slurm-10407316.out`).
- Execution provenance was captured in `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/validation/git_commit.txt`, `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/validation/python_version.txt`, `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/validation/pip_freeze.txt`, and `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/validation/conda_env.yml`.

## Known Issues / Caveats
- This second frozen universe produced a markedly different target cohort from EXP-062, so the stability question became a genuine sampled-universe robustness test rather than a trivial replay.
- `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/manifests/run_metadata.json` still leaves git/environment fields null because the remote pipeline directory was a synced snapshot, not a git checkout; use the validation files as the authoritative provenance record.
- The remaining time-derived features still show large within-overlap mismatch, which likely explains why the downstream transfer runs became unstable again on this universe.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline && sbatch exp070_noqt_plan2024.slurm`
3. `python scripts/regime_matching.py --config experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/config/exp070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024.json`
