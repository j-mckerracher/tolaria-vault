# EXP-015 Baseline Replay — Run Log

**Run ID**: EXP-015_baseline_replay  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Provide a Phase-0, provenance-rich **single-command** regeneration of the EXP-015 baseline artifacts from the frozen snapshot.

## Inputs
- Baseline snapshot:
  - `experiments/EXP-015_baseline/source/EXP015_FINAL_REPORT.md`
  - `experiments/EXP-015_baseline/source/results/exp015_results.csv`
  - `experiments/EXP-015_baseline/source/results/exp015_covariate_shift.json`

## Code & Environment (captured by reproducer)
- `experiments/EXP-015_baseline/validation/python_version.txt`
- `experiments/EXP-015_baseline/validation/pip_freeze.txt`
- Git metadata: `experiments/EXP-015_baseline/manifests/run_metadata.json`

## Execution
Command:
- `python scripts\\reproduce_exp015_baseline.py --config experiments\\EXP-015_baseline\\config\\reproduce_exp015_baseline.json`

Log:
- `experiments/EXP-015_baseline/logs/reproduce_exp015_baseline.log`

## Outputs
Results:
- `experiments/EXP-015_baseline/results/exp015_results.csv`
- `experiments/EXP-015_baseline/results/exp015_covariate_shift.json`
- `experiments/EXP-015_baseline/results/EXP015_FINAL_REPORT.md`
- `experiments/EXP-015_baseline/results/exp015_baseline_summary.md`

Manifests:
- `experiments/EXP-015_baseline/manifests/baseline_manifest.json`
- `experiments/EXP-015_baseline/manifests/run_metadata.json`

Validation:
- `experiments/EXP-015_baseline/validation/replay_validation.json`

## Validation Summary
See: `experiments/EXP-015_baseline/validation/replay_validation.json`

## Known Issues / Caveats
- This replay does **not** recompute EXP-015 from raw shards; it only regenerates the baseline artifacts from the frozen snapshot.
