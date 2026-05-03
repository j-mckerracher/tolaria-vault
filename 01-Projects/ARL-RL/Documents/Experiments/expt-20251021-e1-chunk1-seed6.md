---
title: "E1 Chunk 1 Seed 6"
experiment_id: "expt-20251021-e1-chunk1-seed6"
date: "2025-10-21"
last_updated: "2025-11-30T12:42:00Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "production", "chunk", "E1"]
dataset: ""
algorithm: "Double DQN + Cosine LR"
params:
  LR: 0.00005
  EPS_DECAY: 100000
  TARGET_UPDATE_FREQ: 300
  SEED: 6
  RESOLUTION: "32x32"
  BATCH_SIZE: 4
  STEP_MUL: 16
  NUM_EPISODES: 800
seeds: [6]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164432_E1_seed6"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 40.0 }
  others:
    avg_reward: 0.4
    test_episodes: 5
hardware: {}
sources: []
related: []
---

## Summary
First 800-episode chunk for Seed 6 in Stage E1 production.

## Goal
To accumulate training episodes (~800) in a 2h standby window.

## Setup (Hardware/Software)
- **Environment:** Gilbreth (standby)
- **Resolution:** 32x32
- **Batch Size:** 4
- **Step Multiplier:** 16

## Procedure
2-hour standby job.

## Results
- **Win Rate:** 40.0% (5 test episodes)
- **Avg Reward:** 0.4

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-21-expt-20251021-e1-chunk1-seed6.md]] — status: unknown

## Artifacts
- `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164432_E1_seed6`

## Changelog
- 2025-11-30T12:42:00Z Created from template, migrated from `20251021_164432_E1_seed6.md`

# Original Experiment Notes (Restored)

# Run 20251021_164432_E1_seed6 — Stage E1 (800 eps, 32×32)

- Timestamp (UTC): 2025-10-21T17:15:40.442534Z
- Seed: 6
- Episodes: 800
- Resolution: 32×32
- Algorithm: Stage E1 (Double DQN + Cosine LR)
- Config highlights: LR=5e-5, EPS_DECAY=100k, TUF=300, Batch=4, StepMul=16

## Results (5 test episodes)
- Win rate: 40.0%
- Avg reward: 0.4

## Artifacts
- Local: `01 Projects/ARL RL/Experiment-Results/10-21-2025/20251021_164432_E1_seed6/`
- HPC: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164432_E1_seed6`

## Notes
- 2h standby chunk (~800 episodes) completed; improved vs prior smoke for seed 6.
- Continue chunking to reach ≥1000 episodes before cross‑seed comparison.

# Original Experiment Notes (Restored)

# Run 20251021_212805_E1_seed6 — Stage E1 top-up (+200 eps, 32×32)

- Timestamp (UTC): 2025-10-21T21:42:08.070432Z
- Seed: 6
- Episodes (top-up): 200 (after prior 800)
- Resolution: 32×32
- Algorithm: Stage E1 (Double DQN + Cosine LR)
- Config highlights: LR=5e-5, EPS_DECAY=100k, TUF=300, Batch=4, StepMul=16

## Results (100 test episodes)
- Win rate: 0.0%
- Avg reward: 0.0

## Artifacts
- Local: `01 Projects/ARL RL/Experiment-Results/10-21-2025/20251021_212805_E1_seed6/`
- HPC: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_212805_E1_seed6`