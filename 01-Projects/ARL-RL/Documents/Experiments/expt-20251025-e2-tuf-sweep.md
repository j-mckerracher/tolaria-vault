---
title: "E2 TUF Sweep — 500-Episode Gate Validation"
experiment_id: "expt-20251025-e2-tuf-sweep"
date: "2025-10-25"
last_updated: "2025-10-25T16:44:16Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "e2", "dueling-dqn", "sweep"]
stage: "E2"
algorithm: "Dueling Double DQN + Cosine LR Scheduler"
dataset: "SC2 FindAndDefeatZerglings"
params:
  LR: 5e-5
  EPS_DECAY: 100000
  BATCH_SIZE: 4
  REPLAY_MEMORY_SIZE: 100000
  TARGET_UPDATE_FREQ: 400
  SCREEN_RESOLUTION: 32
  MINIMAP_RESOLUTION: 32
  STEP_MUL: 16
  USE_DUELING_DQN: true
seeds: [4, 6, 8]
episodes: 500
code_ref:
  repo: "C:\\Users\\jmckerra\\PycharmProjects\\ARL-RL"
  entrypoint: "training_split.py"
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/TUF-sweep-alt-3/"
job_ids: ["(HPC jobs, standby QoS)"]
metrics:
  primary:
    name: "100-episode test win rate"
    value: 52.7
    unit: "percent"
    seed_breakdown:
      seed_4: 56.0
      seed_6: 68.0
      seed_8: 34.0
    stdev: 35.9
  gate_status: "PASSED"
  gate_criteria:
    mean_threshold: 44
    stdev_threshold: 40
    mean_actual: 52.7
    stdev_actual: 35.9
hardware:
  gpu: 1
  gpu_model: "A30"
  cpu: 4
  ram_gb: 50
  partition: "a30"
sources:
  - "[[../../../Experiments|Experiments.md]]"
  - "[[../../../Work Completed/2025-10-25 E2 dueling validation and config freeze]]"
related:
  - "[[expt-20251025-e2-confirm-1k]] — Follow-up confirmation run (91.3%)"
  - "[[expt-20251025-e2-prod-3k]] — Production scale-up (94.3%)"
---

## Summary
E2 (Dueling DQN) smoke validation at 500 episodes. **Mean win rate 52.7%** (seeds 56%/68%/34%), stdev 35.9 pp. **Gate criteria passed**: mean ≥ 44% and stdev < 40 pp. Cleared for 1k-episode confirmation run.

## Goal
Validate E2 configuration (Dueling DQN enabled, TUF=400) at 500 episodes to gate proceed to 1k-episode confirmatory runs.

## Setup (Hardware/Software)
- **Environment**: Gilbreth HPC
- **GPU**: NVIDIA A30
- **QoS**: standby (backfill scheduling)
- **Time per seed**: ~2-2.5 hours

## Procedure
1. Submit three independent 500-episode runs (seeds 4, 6, 8)
2. Test on 100-episode evaluation set at final episode
3. Aggregate results
4. Evaluate against gate: mean ≥ 44% AND stdev < 40 pp

## Results
### Win Rates (100-episode test)
- **Seed 4**: 56.0%
- **Seed 6**: 68.0%
- **Seed 8**: 34.0%
- **Mean**: 52.7%
- **StdDev**: 35.9 pp

### Gate Status
✓ **PASSED**
- Mean: 52.7% > 44% threshold ✓
- StdDev: 35.9 pp < 40 pp threshold ✓

## Analysis
- **High variance**: 34% gap between seeds suggests still exploring parameter space or seed sensitivity
- **Mean above baseline**: Clear improvement over E1 baseline (44%)
- **Gate criteria met**: Sufficient confidence to proceed to 1k runs despite high variance
- **Next phase**: 1k-episode runs should converge on stable mean performance

## Issues
None. All three seeds completed successfully.

## Next Steps
- Proceed to [[expt-20251025-e2-confirm-1k]] (1,000 episodes) — **COMPLETED**
- Then to [[expt-20251025-e2-prod-3k]] (3,000 episodes) — **COMPLETED**

## Jobs
- [[../../Job-Submission-Commands/2025-10-25-expt-20251025-e2-tuf-sweep]]

## Changelog
- 2025-10-25T16:44:16Z Created from template

# Original Experiment Notes (Restored)

# E2 TUF-sweep-alt-3 — Dueling DQN Validation (500 episodes)

## Overview
- Run ID: TUF-sweep-alt-3 (seeds 4, 6, 8)
- Objective: Validate dueling DQN with TUF=400 at 500 episodes per seed
- Part: Stage E2 — Dueling DQN architecture

## Config deltas (from E1 baseline)
- DUELING_DQN: enabled
- TARGET_UPDATE_FREQ: 300 → 400
- NUM_EPISODES: 500
- All other parameters locked to E2 baseline:
  - LR: 5e-5
  - EPS_DECAY: 100000
  - BATCH_SIZE: 4
  - REPLAY_MEMORY_SIZE: 100000
  - STEP_MUL: 16
  - SCREEN_RESOLUTION / MINIMAP_RESOLUTION: 32

## Metadata
- Date/Time (UTC): 2025-10-25
- Git commit: (not tracked)
- Branch: main
- Seed(s): 4, 6, 8
- Environment: Gilbreth HPC
- SLURM: account=sbagchi, partition=a30, QoS=standby
- Resources: 1 GPU A30, 4 CPUs, 50GB RAM per job
- Command / Env overrides:
```bash
sbatch --account=sbagchi --partition=a30 --qos=standby --gres=gpu:1 \
  --ntasks=1 --cpus-per-task=4 --mem=50G --time=02:00:00 \
  --export=ALL,RL_SEED=<seed>,RL_NUM_EPISODES=500,RL_LEARNING_RATE=0.00005,\
RL_EPS_DECAY=100000,RL_BATCH_SIZE=4,RL_REPLAY_MEMORY_SIZE=100000,\
RL_SCREEN_RESOLUTION=32,RL_STEP_MUL=16,RL_TARGET_UPDATE_FREQ=400,\
RL_DUELING_DQN=1 \
  scripts/run_e2.sh
```
- Artifacts path: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/TUF-sweep-alt-3/`

## Results
- 100-episode test win rates:
  - Seed 4: 56.0%
  - Seed 6: 68.0%
  - Seed 8: 34.0%
- Aggregate: Mean = 52.7%, StdDev = 35.9 pp
- Gate criterion: **PASSED** (mean ≥ 44%, stdev < 40 pp)
- Training curves: Available in run directories
- Checkpoints: Saved at intervals

## Observations
- Dueling architecture showed promising results with TUF=400
- High variance across seeds but mean win rate exceeded E1 baseline
- Seed 8 lower than seeds 4/6 but still reasonable
- Gate criteria met, indicating readiness for 1k-episode confirmatory runs

## Next steps
- Proceed to 1,000-episode confirmatory runs (run-6) with locked parameters
- If confirmed, freeze E2 configuration as production baseline
- Prepare for Stage E3 (PER) smoke tests