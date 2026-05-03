# EXP-076 Run Log -- Completed runtime-sec-only modeling on the first frozen universe

**Run ID**: EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only
**Date**: 2026-03-12
**Owner**: jmckerra

## Objective
Measure whether the runtime-sec-only feature recipe can retain positive Anvil -> Conte `peak_memory_fraction` transfer on the first frozen universe.

## Hypothesis (if experiment)
If the first frozen-universe success only needed one duration-control variable, this reduced feature set should keep target transfer near or above zero without relying on the full timing trio.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Frozen sampling plan: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp044_hwcpu_standard_300k_24_seed1337.json`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`
- Cohorts: `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/results/matched_source_indices.parquet` and `experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Modeling split seed: `1337`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/config/exp076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only.json`
- Git commit (pipeline): `b85eea66f15f91024af7f660f4025b5b2a9e5f85`
- Git commit (analysis): `b85eea66f15f91024af7f660f4025b5b2a9e5f85`
- Conda env: `fresco_v2`
- Python: `Python 3.10.19`
- Package lock: `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp076_runtime_sec_u1_model.slurm`
- Job IDs: `10407626`
- Start / end time (UTC): `2026-03-12T23:30:46Z / 2026-03-12T23:32:23Z`

## Outputs
- Output root: `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/results/`
- Manifests: `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/manifests/`
- Validation reports: `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/validation/`

## Results Summary
- `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/results/metrics.json`: source-test `R^2 = 0.0401` and target `R^2 = 0.0502`.
- `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/results/metrics.json`: bootstrap target `R^2` 95% CI = `[0.0260, 0.0708]` with bootstrap mean `0.0495`.
- `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/results/metrics.json`: target slope = `1.7892`, target `bias_log = -0.0336`, and target `mae_log = 0.0904`.
- `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/results/metrics.json`: this run reused the EXP-075 overlap cohort with `7504` matched source jobs and `5997` target evaluation jobs after the positive-label filter.

## Validation Summary
- Job `10407626` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, and validation files (`experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/logs/slurm-10407626.out`).
- Execution provenance was captured in `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/validation/git_commit.txt`, `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/validation/python_version.txt`, `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/validation/pip_freeze.txt`, and `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/validation/conda_env.yml`.
- No runtime errors were reported in `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/logs/model_transfer.log`.

## Known Issues / Caveats
- Although target `R^2` stayed positive on the first frozen universe, it weakened relative to the earlier no-queue baseline (`EXP-063` target `R^2 = 0.1070`), so pruning to `runtime_sec` alone did not improve the favorable universe.
- `experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/manifests/run_metadata.json` still leaves git/environment fields null because the remote pipeline directory was a synced snapshot, not a git checkout; use the validation files as the authoritative provenance record.
- This run must be interpreted jointly with EXP-078; the design is not robust if it only works on the first frozen universe.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline && sbatch exp076_runtime_sec_u1_model.slurm`
3. `python scripts/model_transfer.py --config experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/config/exp076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only.json`
