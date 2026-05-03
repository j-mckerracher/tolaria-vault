# EXP-062 Run Log -- Completed regime matching on authoritative v3 hardware CPU-standard cohorts without queue_time_sec

**Run ID**: EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime  
**Date**: 2026-03-12  
**Owner**: jmckerra

## Objective
Test whether removing `queue_time_sec` from the authoritative hardware CPU-standard overlap feature set reduces scheduler-specific mismatch while preserving the EXP-044 baseline geometry on a frozen sampled universe.

## Hypothesis (if experiment)
Dropping `queue_time_sec` while freezing the raw sampled row-group universe will preserve the EXP-044 overlap coverage but remove the largest scheduler-specific within-overlap mismatch, creating a cleaner cohort for repeated Phase 3 transfer tests.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Frozen sampling plan: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp044_hwcpu_standard_300k_24_seed1337.json`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`

## Code & Environment
- Script: `scripts\regime_matching.py`
- Config: `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/config/exp062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime.json`
- Git commit (pipeline): `aa2457958db8ec9a0735da5f64129d00155a62d1`
- Git commit (analysis): `aa2457958db8ec9a0735da5f64129d00155a62d1`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp062_noqt.slurm`
- Job IDs: `10407050`
- Start / end time (UTC): `2026-03-12T20:34:32Z / 2026-03-12T20:36:33Z`

## Outputs
- Output root: `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/`
- Manifests: `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/manifests/`
- Validation reports: `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/validation/`

## Results Summary
- `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/overlap_report.json`: domain classifier AUC = `0.9366` and target overlap coverage = `33.31%`.
- `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/overlap_report.json`: source overlap = `6995 / 12649` jobs and target overlap = `2459 / 7383` jobs.
- `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/overlap_report.json`: the largest remaining within-overlap KS values are `runtime_fraction = 0.4903`, `runtime_sec = 0.4091`, and `timelimit_sec = 0.4066`; `queue_time_sec` is no longer part of the overlap geometry.
- `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/logs/slurm-10407050.out`: frozen-plan replay read `286,843` Anvil raw rows (`13,260` jobs) and `131,122` Conte raw rows (`7,383` jobs).

## Validation Summary
- Job `10407050` completed with exit code `0` and wrote the expected overlap artifacts, manifests, and validation files (`experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/logs/slurm-10407050.out`).
- Execution provenance was captured in `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/validation/git_commit.txt`, `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/validation/python_version.txt`, and `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/validation/pip_freeze.txt`.
- No runtime validation or schema errors were reported in `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/logs/regime_matching.log`.

## Known Issues / Caveats
- `experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/manifests/run_metadata.json` leaves git/environment fields null because `/home/jmckerra/Code/FRESCO-Pipeline` on Gilbreth was a synced snapshot rather than a git checkout; use the files under `validation/` as the authoritative provenance record.
- This run freezes the EXP-044-equivalent raw row-group universe by design, so it stabilizes the cohort used for comparison but does not by itself quantify sensitivity to alternate frozen universes.
- Even after removing `queue_time_sec`, the remaining time-derived features still show moderate within-overlap mismatch.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline && sbatch exp062_noqt.slurm`
3. `python scripts/regime_matching.py --config experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/config/exp062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime.json`
