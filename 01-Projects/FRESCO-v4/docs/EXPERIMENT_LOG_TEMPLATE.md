# Experiment / Production Run Log Template (v4)

**Last Updated**: 2026-03-13

---

**Run ID**: <EXP-XXX>
**Date**: YYYY-MM-DD
**Owner**: <name>

## Objective

## Hypothesis (if experiment)

## Inputs
- dataset_version:
- dataset_root: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/`
- source_cluster:
- target_cluster:
- regime:
- overlap_run (Phase 2 reference):
- sampling_plan_path:

## Code & Environment
- git commit (pipeline):
- git commit (analysis):
- conda env:
- python:
- package lock artifact path:

## Few-Shot Configuration
- **N** (n_target_labels):
- **Strategy**: <zero_shot | output_recal | fine_tune | stacked | target_only>
- **Target label seed** (target_label_seed):
- **Target weight** (fine_tune only):
- **Recalibration prior** (output_recal only):

## Calibration Details
- Which N jobs were sampled (manifest path): `manifests/calibration_job_ids.json`
- Sampling method: stratified by `peak_memory_fraction` quartiles within overlap cohort
- Calibration parameters learned:
  - (output_recal) a = ___, b = ___
  - (fine_tune) effective target weight = ___
  - (stacked) second-stage model coefficients: ___
  - (target_only) N/A (no calibration, direct training)

## Baselines Referenced
- Zero-shot (N=0): EXP-___
- Target-only (same N): EXP-___
- Full-target upper bound: EXP-___

## Execution
- cluster: Gilbreth
- submission command:
- job IDs:
- start/end time (UTC):

## Outputs
- output_root:
- manifests:
- validation reports:
- predictions artifact:

## Results Summary
- Source-test R-squared:
- Target R-squared:
- Target bootstrap 95% CI:
- Target MAE(log):
- Target MdAE(log):
- Target SMAPE:
- Target bias:
- Target calibration slope:

## Validation Summary
- Split integrity (zero cal/eval overlap): PASS / FAIL
- N jobs successfully sampled:
- Evaluation set size:

## Known Issues / Caveats

## Repro Steps
1.
2.
3.
