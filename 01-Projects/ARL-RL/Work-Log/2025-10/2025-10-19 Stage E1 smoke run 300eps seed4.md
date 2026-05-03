---
project: ARL RL
tags: [project/arl-rl, work-log, slurm, e1]
created: 2025-10-19
---

# Stage E1 smoke run — 1h standby, 32×32, seed 4 — 2025-10-19

## Summary
- Canceled long-pending job; submitted a short, backfill-friendly Stage E1 smoke run (episodes override via CLI).
- Completed 300 training episodes at 32×32 for seed 4; appended results to `e1_results.csv`.
- Result (5 test episodes): win_rate 80.0%, avg_reward 2.0.

## Submission
```bash
sbatch --account sbagchi --partition a30 --qos standby --time 01:00:00 \
  --ntasks=1 --cpus-per-task=2 --mem=20G --gres=gpu:1 \
  --export=ALL,RL_NUM_TEST_EPISODES=5,RL_STEP_MUL=32,RL_BATCH_SIZE=2 \
  /home/jmckerra/Code/ARL-RL/scripts/run_e1.sh --res 32 --episodes 300 --seeds "4"
```

## Job completion summary
```
====== JOB COMPLETION SUMMARY ======
Job ID: 9765383
Completion time: 2025-10-19 03:48:11 UTC
Seeds processed: 4
Episodes per seed: 300
Resolution: 32x32
Results CSV: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/e1_results.csv
CSV entries: 1
Latest results:
timestamp_utc                run_id                    seed  lr       eps_decay  target_update  win_rate  avg_reward  artifacts_path
2025-10-19T03:48:11.460274Z  20251019_033706_E1_seed4  4     0.00005  100000     300            80.0      2.0         /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_033706_E1_seed4
=====================================
Job completed successfully!
```

## Artifacts
- Run ID: `20251019_033706_E1_seed4`
- Artifacts path: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_033706_E1_seed4`
- Aggregation: appended to `e1_results.csv` (same directory as above)

## Notes
- Stage E1 recipe defaults (Double DQN + LR scheduler), 32×32, small batch and larger `step_mul` for fast smoke validation.

## Links
- [[20251019_033706_E1_seed4]]
- [[01 Projects/ARL-RL/Work Completed/Index]]

## Next
- Repeat smoke for seeds 6 and 8 (1h chunks) and/or extend to longer normal QoS runs; update `e1_results.csv` and Experiments notes accordingly.
