# EXP-068 Run Log  Planned regime matching repeat on authoritative v3 without queue_time_sec (seed 2026)

**Run ID**: EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026  
**Date**: 2026-03-12
**Owner**: jmckerra

## Objective
Repeat the tightened regime-matching baseline with seed 2026 while dropping only queue_time_sec from the overlap feature set.

## Hypothesis (if experiment)
If queue_time_sec is contributing disproportionately to domain separability, the seed-2026 repeat should remain closer to the matched-workload geometry than EXP-050 did.

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
- Config: `experiments/EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026/config/exp068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026.json`
- Git commit (pipeline): `TBD at execution time; current local changes add sampling_plan_path support`
- Git commit (analysis): `TBD at execution time`
- Conda env: `TBD at execution time`
- Python: `TBD at execution time`
- Package lock: `experiments/EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026/validation/pip_freeze.txt`

## Notes
- Workstream B scaffolding only: this run has **not** been submitted yet.
- This repeat regime scaffold now reuses the same frozen row-group plan as EXP-062, so it is expected to reproduce EXP-062 exactly and is retained only for provenance.
- This config preserves the EXP-044/046/048/050 regime-matching design except for removing `queue_time_sec` from `feature_columns`.
- Renumbering rationale: the originally requested EXP-052..059 identifiers are already occupied by committed dense-sampling and alloc-only diagnosis runs, so this planned family is staged as EXP-062..069 instead.
- Rationale for the feature change: `queue_time_sec` appears to encode scheduler/cluster behavior more than workload similarity, and it remained one of the worst-matched features inside the EXP-044 overlap region.

## Execution
- Cluster: Gilbreth
- Submission command: `Not submitted in Workstream B. Planned repro command: python scripts\regime_matching.py --config experiments\EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026\config\exp068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026.json`
- Job IDs: `Not assigned (job submission intentionally deferred)`
- Start / end time (UTC): `N/A / N/A`

## Outputs
- Output root: `experiments/EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026/results/`
- Manifests: `experiments/EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026/manifests/`
- Validation reports: `experiments/EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026/validation/`

## Results Summary
- Planned run only; no job has been submitted in Workstream B, so no metrics or overlap artifacts exist yet.
- Expected result artifacts, once executed, will be written under `experiments/EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026/results/` and should be cited there before making any claim.

## Validation Summary
- Not run yet. Validation artifacts will be produced under `experiments/EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026/validation/` after execution.

## Known Issues / Caveats
- This log records a **planned** run only; nothing in this folder should be interpreted as executed evidence.
- The experiment numbering was renumbered from the user-requested EXP-052..059 to EXP-062..069 because EXP-052..059 are already occupied by immutable committed historical runs.
- Final submission and any design adjustments should wait for Workstream A analysis of the current instability diagnosis.

## Repro Steps
1. Only submit this redundant regime rerun if exact pairwise provenance is explicitly desired under the frozen sampling plan.
2. Capture the final execution environment into `experiments/EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026/validation/` before submission.
3. Run `python scripts\regime_matching.py --config experiments\EXP-068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026\config\exp068_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_seed_2026.json`.
