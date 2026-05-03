---
project: ARL RL
tags: [project/arl-rl, work-log, slurm, e1]
created: 2025-10-19
---

# Stage E1 smoke runs — seeds 6 and 8 — 2025-10-19

## Summary
- Continued Stage E1 smoke validations (1h standby) at 32×32 with 300 episodes per seed.
- Results appended to `e1_results.csv`; added per-run experiment notes.

## Submissions
```bash
# Seed 6
sbatch --account sbagchi --partition a30 --qos standby --time 01:00:00 \
  --ntasks=1 --cpus-per-task=2 --mem=20G --gres=gpu:1 \
  --export=ALL,RL_NUM_TEST_EPISODES=5,RL_STEP_MUL=32,RL_BATCH_SIZE=2 \
  /home/jmckerra/Code/ARL-RL/scripts/run_e1.sh --res 32 --episodes 300 --seeds "6"

# Seed 8
sbatch --account sbagchi --partition a30 --qos standby --time 01:00:00 \
  --ntasks=1 --cpus-per-task=2 --mem=20G --gres=gpu:1 \
  --export=ALL,RL_NUM_TEST_EPISODES=5,RL_STEP_MUL=32,RL_BATCH_SIZE=2 \
  /home/jmckerra/Code/ARL-RL/scripts/run_e1.sh --res 32 --episodes 300 --seeds "8"
```

## Results (from e1_results.csv)
```
timestamp_utc,run_id,seed,lr,eps_decay,target_update,win_rate,avg_reward,artifacts_path
2025-10-19T04:30:34.579959Z,20251019_041819_E1_seed6,6,0.00005,100000,300,0.0,0.0,/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_041819_E1_seed6
2025-10-19T15:23:35.583000Z,20251019_151225_E1_seed8,8,0.00005,100000,300,20.0,0.0,/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_151225_E1_seed8
```

## Artifacts
- [[20251019_041819_E1_seed6]]
- [[20251019_151225_E1_seed8]]
- Aggregation CSV: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/e1_results.csv`

## Notes
- High variance across seeds (seed 6=0%, seed 8=20% vs earlier seed 4=80%).
- Recommend longer confirms or parameter checks before promoting E1.
