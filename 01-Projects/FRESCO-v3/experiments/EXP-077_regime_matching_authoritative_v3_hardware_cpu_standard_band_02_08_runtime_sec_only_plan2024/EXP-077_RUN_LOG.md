# EXP-077 Run Log -- Completed runtime-sec-only regime matching on the second frozen universe

**Run ID**: EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024
**Date**: 2026-03-12
**Owner**: jmckerra

## Objective
Repeat the runtime-sec-only overlap test on the second frozen universe immediately, so the design is judged on cross-universe robustness rather than a single favorable cohort.

## Hypothesis (if experiment)
If the timing-trio redundancy was the main universe-sensitivity driver, the runtime-sec-only design should reduce the overlap mismatch spike seen in EXP-070 on the alternate frozen plan.

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
- Config: `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/config/exp077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024.json`
- Git commit (pipeline): `b85eea66f15f91024af7f660f4025b5b2a9e5f85`
- Git commit (analysis): `b85eea66f15f91024af7f660f4025b5b2a9e5f85`
- Conda env: `fresco_v2`
- Python: `Python 3.10.19`
- Package lock: `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp077_runtime_sec_u2.slurm`
- Job IDs: `10407596` (failed first wrapper attempt), `10407608` (successful execution)
- Start / end time (UTC): `2026-03-12T23:19:45Z / 2026-03-12T23:21:27Z`

## Outputs
- Output root: `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/results/`
- Manifests: `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/manifests/`
- Validation reports: `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/validation/`

## Results Summary
- `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/results/overlap_report.json`: domain classifier AUC = `0.8987` and target overlap coverage = `75.39%`.
- `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/results/overlap_report.json`: source overlap = `12526 / 16680` jobs and target overlap = `4626 / 6136` jobs.
- `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/results/overlap_report.json`: within-overlap KS is `runtime_sec = 0.8092`, with `ncores = 0.0715` and `nhosts = 0.0000`.
- `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/logs/slurm-10407608.out`: frozen-plan replay read `241,089` Anvil raw rows (`17,346` jobs) and `101,776` Conte raw rows (`6,136` jobs).

## Validation Summary
- Job `10407596` failed immediately because the first generated wrapper omitted the explicit `PYTHON_BIN`, `PIP_BIN`, and `CONDA_BIN` definitions; job `10407608` is the successful superseding execution.
- Job `10407608` completed with exit code `0` and wrote the expected overlap artifacts, manifests, and validation files (`experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/logs/slurm-10407608.out`).
- Execution provenance was captured in `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/validation/git_commit.txt`, `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/validation/python_version.txt`, `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/validation/pip_freeze.txt`, and `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/validation/conda_env.yml`.
- No runtime validation or schema errors were reported in `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/logs/regime_matching.log`.

## Known Issues / Caveats
- The runtime-sec-only design widened overlap dramatically on the second frozen universe, but the remaining single timing feature became severely mismatched inside the overlap band (`runtime_sec KS = 0.8092`).
- `experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/manifests/run_metadata.json` still leaves git/environment fields null because `/home/jmckerra/Code/FRESCO-Pipeline` on Gilbreth was a synced snapshot rather than a git checkout; use the validation files under `validation/` as the authoritative provenance record.
- This broad overlap should not be interpreted as a success unless the paired model run (EXP-078) also transfers cleanly.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline && sbatch exp077_runtime_sec_u2.slurm`
3. `python scripts/regime_matching.py --config experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/config/exp077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024.json`
