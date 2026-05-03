# EXP-075 Run Log -- Completed runtime-sec-only regime matching on the first frozen universe

**Run ID**: EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only
**Date**: 2026-03-12
**Owner**: jmckerra

## Objective
Test whether collapsing the remaining timing block to `runtime_sec` yields a cleaner authoritative Anvil -> Conte overlap on the first frozen universe.

## Hypothesis (if experiment)
If the residual instability comes from the redundant timing trio rather than `runtime_sec` alone, then keeping only `runtime_sec` alongside `ncores` and `nhosts` should preserve usable overlap while reducing within-overlap timing mismatch relative to EXP-062.

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
- Config: `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/config/exp075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only.json`
- Git commit (pipeline): `b85eea66f15f91024af7f660f4025b5b2a9e5f85`
- Git commit (analysis): `b85eea66f15f91024af7f660f4025b5b2a9e5f85`
- Conda env: `fresco_v2`
- Python: `Python 3.10.19`
- Package lock: `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp075_runtime_sec_u1.slurm`
- Job IDs: `10407595` (failed first wrapper attempt), `10407607` (successful execution)
- Start / end time (UTC): `2026-03-12T23:19:45Z / 2026-03-12T23:21:27Z`

## Outputs
- Output root: `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/results/`
- Manifests: `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/manifests/`
- Validation reports: `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/validation/`

## Results Summary
- `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/results/overlap_report.json`: domain classifier AUC = `0.8990` and target overlap coverage = `81.69%`.
- `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/results/overlap_report.json`: source overlap = `7504 / 12649` jobs and target overlap = `6031 / 7383` jobs.
- `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/results/overlap_report.json`: within-overlap KS is `runtime_sec = 0.4610`, with `ncores = 0.1940` and `nhosts = 0.0000`.
- `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/logs/slurm-10407607.out`: frozen-plan replay read `286,843` Anvil raw rows (`13,260` jobs) and `131,122` Conte raw rows (`7,383` jobs).

## Validation Summary
- Job `10407595` failed immediately because the first generated wrapper omitted the explicit `PYTHON_BIN`, `PIP_BIN`, and `CONDA_BIN` definitions; job `10407607` is the successful superseding execution.
- Job `10407607` completed with exit code `0` and wrote the expected overlap artifacts, manifests, and validation files (`experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/logs/slurm-10407607.out`).
- Execution provenance was captured in `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/validation/git_commit.txt`, `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/validation/python_version.txt`, `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/validation/pip_freeze.txt`, and `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/validation/conda_env.yml`.
- No runtime validation or schema errors were reported in `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/logs/regime_matching.log`.

## Known Issues / Caveats
- The runtime-sec-only design widens overlap substantially on the first frozen universe, but this by itself does not establish robustness because the paired second-universe check in EXP-077/078 is the real generalization test.
- `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/manifests/run_metadata.json` still leaves git/environment fields null because `/home/jmckerra/Code/FRESCO-Pipeline` on Gilbreth was a synced snapshot rather than a git checkout; use the files under `validation/` as the authoritative provenance record.
- Even after pruning to a single timing feature, `runtime_sec` still shows moderate within-overlap mismatch (`KS = 0.4610`).

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline && sbatch exp075_runtime_sec_u1.slurm`
3. `python scripts/regime_matching.py --config experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/config/exp075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only.json`
