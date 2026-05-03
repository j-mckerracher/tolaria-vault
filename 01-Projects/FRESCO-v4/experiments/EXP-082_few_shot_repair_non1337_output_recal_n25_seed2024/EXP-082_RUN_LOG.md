# EXP-082 Run Log - repaired non-1337 output recalibration N=25 seed 2024 rerun

**Run ID**: EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024
**Date**: 2026-03-16

## Objective
Re-run the original non-1337 output recalibration with N=25 anvil -> conte hardware_cpu_standard cell on the frozen 1337 data/split universe so this point reflects only label-sampling variation.

## Hypothesis (if experiment)
Freezing `data_seed`/`split.seed` at 1337 should remove the original seed confound, and setting `few_shot.min_target_eval_rows=50` should prevent the original zero-eval failure mode while keeping this rerun on the same frozen overlap cohort as the valid 1337 cells.

## Repair Context
- Original main cell: `EXP-010_few_shot_main_output_recal_n25_seed2024`.
- Original issue: Original main cell `EXP-010_few_shot_main_output_recal_n25_seed2024` completed, but it was still confounded because its config used `split.seed=2024`, `random_seed=2024`, and `data_seed=unset` (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-010_few_shot_main_output_recal_n25_seed2024/config/EXP-010_few_shot_main_output_recal_n25_seed2024.json`), so the non-1337 point changed the sampled universe instead of isolating `few_shot.target_label_seed`; see `results\exp003_main_few_shot_summary.csv` and logs `/home/jmckerra/Code/FRESCO-v4/experiments/sweep_logs/exp003_main_10409707_8.out` / `/home/jmckerra/Code/FRESCO-v4/experiments/sweep_logs/exp003_main_10409707_8.err`.
- Repair applied: Repair rerun `EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024` froze `data_seed=1337` and `split.seed=1337` and set `few_shot.min_target_eval_rows=50` in `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`; parent array job is `10410106` and this run corresponds to task `10410106_5` via `/home/jmckerra/Code/FRESCO-v4/config/exp078_repair_non1337_config_paths.txt` and `/home/jmckerra/Code/FRESCO-v4/scripts/exp078_repair_non1337.slurm`.

## Inputs
- Dataset label: `chunks-v3-authoritative` (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`)
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl` (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`)
- Clusters: `anvil` -> `conte` (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`)
- Date range: not recorded in run-specific artifacts; this rerun uses the authoritative chunks-v3 snapshot referenced by `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl` (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`)

## Code & Environment
- Script: `/home/jmckerra/Code/FRESCO-v4/scripts/few_shot_transfer.py` (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/manifests/run_metadata.json`)
- Config: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`
- Git commit (pipeline): not recorded (`git_commit=null` in `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/manifests/run_metadata.json`)
- Git commit (analysis): not separately recorded; same caveat as pipeline (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/manifests/run_metadata.json`)
- Conda env: `fresco_v2` (`/home/jmckerra/Code/FRESCO-v4/scripts/exp078_repair_non1337.slurm`)
- Python: `3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]` (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/validation/python_version.txt`)
- Package lock: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/validation/pip_freeze.txt`

## Execution
- Cluster: Gilbreth
- Submission command: `sbatch /home/jmckerra/Code/FRESCO-v4/scripts/exp078_repair_non1337.slurm` (`/home/jmckerra/Code/FRESCO-v4/scripts/exp078_repair_non1337.slurm`)
- Job IDs: parent array `10410106`; task `10410106_5` with `state=COMPLETED` (`/home/jmckerra/Code/FRESCO-v4/config/exp078_repair_non1337_config_paths.txt`; `/home/jmckerra/Code/FRESCO-v4/experiments/sweep_logs/exp078_repair_10410106_5.out`)
- Start / end time (UTC): `2026-03-16T22:16:08Z` / `2026-03-16T22:17:43Z` (`/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/logs/few_shot_transfer.log`)

## Outputs
- Output root: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/`
- Manifests: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/manifests/`
- Validation reports: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/validation/`
- Predictions artifact: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/predictions_target.parquet`
- Metrics artifact: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/metrics.json`
- Relevant logs: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/logs/few_shot_transfer.log`; `/home/jmckerra/Code/FRESCO-v4/experiments/sweep_logs/exp078_repair_10410106_5.out`; `/home/jmckerra/Code/FRESCO-v4/experiments/sweep_logs/exp078_repair_10410106_5.err`

## Results Summary
- Source-test R-squared: `0.2091`; Target R-squared: `-0.0641`; Target bootstrap 95% CI: `[-0.1240, -0.0249]`; Target MAE(log): `0.0914`; Target MdAE(log): `0.0623`; Target SMAPE: `50.33`; Target bias(log): `0.0050`; Target calibration slope: `-0.8280`. Source: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/metrics.json`.
- Calibration / evaluation counts: `actual_cal_n=25`, `actual_eval_n=198`, `matched_source_n=6995`, `matched_target_n=223`, `overflow_pred=false`. Source: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/metrics.json`.

## Validation Summary
- Runtime completed with `state=COMPLETED` / `exit_code=0:0` and materialized `results/metrics.json`, `predictions_target.parquet`, and `predictions_source_test.parquet`. Sources: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/metrics.json`; `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/predictions_target.parquet`; `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/predictions_source_test.parquet`.
- Recorded split sizes: `actual_cal_n=25`, `actual_eval_n=198`, `min_target_eval_rows=50`, `min_target_eval_rows_satisfied=true`, `calibration_n_capped=false`. Sources: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/metrics.json`; `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/logs/few_shot_transfer.log`.
- No standalone Level 0/1 validation report was emitted beyond environment capture files in `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/validation/python_version.txt` and `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/validation/pip_freeze.txt`, so treat this as runtime/metrics validation rather than a full archived validation sign-off.

## Known Issues / Caveats
- This is a repair rerun for original main cell `EXP-010_few_shot_main_output_recal_n25_seed2024`, not a net-new experiment. Sources: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-010_few_shot_main_output_recal_n25_seed2024/config/EXP-010_few_shot_main_output_recal_n25_seed2024.json`; `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`.
- Provenance caveat: `manifests/run_metadata.json` records `git_commit=null`, so the exact pipeline commit was not captured for this run. Source: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/manifests/run_metadata.json`.
- Repair design caveat: the repaired config froze `data_seed=1337` / `split.seed=1337` and set `few_shot.min_target_eval_rows=50`. Source: `/home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`.

## Repro Steps
1. `ssh jmckerra@gilbreth.rcac.purdue.edu && cd /home/jmckerra/Code/FRESCO-v4`
2. `source /home/jmckerra/anaconda3/etc/profile.d/conda.sh && conda activate fresco_v2`
3. `python /home/jmckerra/Code/FRESCO-v4/scripts/few_shot_transfer.py --config /home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/config/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024.json`
4. `sed -n "5p" /home/jmckerra/Code/FRESCO-v4/config/exp078_repair_non1337_config_paths.txt && cat /home/jmckerra/Code/FRESCO-v4/experiments/EXP-082_few_shot_repair_non1337_output_recal_n25_seed2024/results/metrics.json`
