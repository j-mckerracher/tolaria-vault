# EXP-074 Run Log -- Completed second frozen-universe no-queue modeling (seed 2026)

**Run ID**: EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026  
**Date**: 2026-03-12  
**Owner**: jmckerra

## Objective
Evaluate whether the stable positive target transfer from EXP-063/065/067/069 persists when the no-queue feature recipe is applied to a different frozen sampled universe.

## Hypothesis (if experiment)
If the stable positive result is genuinely robust to sampled-universe choice, then this run should retain target `R^2 > 0` on the second frozen plan while reusing the same no-queue feature set and modeling recipe.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Frozen sampling plan: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp070_hwcpu_standard_300k_24_seed2024.json`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31
- Cohorts: `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/matched_source_indices.parquet` and `experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/matched_target_indices.parquet`
- Label: `peak_memory_fraction` with `log1p` transform (`label_proxy=false`)
- Modeling split seed: `2026`

## Code & Environment
- Script: `scripts\model_transfer.py`
- Config: `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/config/exp074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026.json`
- Git commit (pipeline): `167f2da5940b63c34d862cfbc6bfb4189121c443`
- Git commit (analysis): `167f2da5940b63c34d862cfbc6bfb4189121c443`
- Conda env: `fresco_v2`
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]`
- Package lock: `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch exp074_plan2024_model.slurm`
- Job IDs: `10407342`
- Start / end time (UTC): `2026-03-12T21:54:28Z / 2026-03-12T21:56:34Z`

## Outputs
- Output root: `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/results/`
- Manifests: `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/manifests/`
- Validation reports: `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/validation/`

## Results Summary
- `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/results/metrics.json`: source-test `R^2 = 0.0895` and target `R^2 = -0.0060`.
- `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/results/metrics.json`: bootstrap target `R^2` 95% CI = `[-0.0452, 0.0346]` with bootstrap mean `-0.0064`.
- `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/results/metrics.json`: target slope = `0.5185`, target `bias_log = 0.0123`, and target `mae_log = 0.0839`.
- `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/results/metrics.json`: this repeat reused the EXP-070 overlap cohort with `11133` matched source jobs and `1686` target evaluation jobs.

## Validation Summary
- Job `10407342` completed with exit code `0` and wrote the expected metrics, prediction parquet files, manifests, and validation files (`experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/logs/slurm-10407342.out`).
- Execution provenance was captured in `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/validation/git_commit.txt`, `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/validation/python_version.txt`, `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/validation/pip_freeze.txt`, and `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/validation/conda_env.yml`.
- No runtime errors were reported in `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/logs/model_transfer.log`.

## Known Issues / Caveats
- These repeats show that the positive no-queue result from EXP-063/065/067/069 does not generalize across frozen sampled universes: this second universe moved target performance back to zero or negative.
- `experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/manifests/run_metadata.json` still leaves git/environment fields null because the remote pipeline directory was a synced snapshot, not a git checkout; use the validation files as the authoritative provenance record.
- The normalized label still carries the cross-cluster measurement-semantics caveat (`memory_includes_cache=true` on anvil and `false` on conte/stampede), but the immediate failure mode here is already visible in the weaker source holdout fit and much lower target slope.

## Repro Steps
1. `source ~/anaconda3/bin/activate fresco_v2`
2. `cd /home/jmckerra/Code/FRESCO-Pipeline && sbatch exp074_plan2024_model.slurm`
3. `python scripts/model_transfer.py --config experiments/EXP-074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026/config/exp074_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_plan2024_seed_2026.json`
