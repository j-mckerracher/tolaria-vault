---
title: "E1 Chunk 1 Seed 8"
experiment_id: "expt-20251021-e1-chunk1-seed8"
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
  SEED: 8
  RESOLUTION: "32x32"
  BATCH_SIZE: 4
  STEP_MUL: 16
  NUM_EPISODES: 800
seeds: [8]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164435_E1_seed8"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 20.0 }
  others:
    avg_reward: 0.2
    test_episodes: 5
hardware: {}
sources: []
related: []
---

## Summary
First 800-episode chunk for Seed 8 in Stage E1 production.

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
- **Win Rate:** 20.0% (5 test episodes)
- **Avg Reward:** 0.2

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-21-expt-20251021-e1-chunk1-seed8.md]] — status: unknown

## Artifacts
- `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164435_E1_seed8`

## Changelog
- 2025-11-30T12:42:00Z Created from template, migrated from `20251021_164435_E1_seed8.md`

# Original Experiment Notes (Restored)

# Run 20251021_164435_E1_seed8 — Stage E1 (800 eps, 32×32)

- Timestamp (UTC): 2025-10-21T17:24:21.102417Z
- Seed: 8
- Episodes: 800
- Resolution: 32×32
- Algorithm: Stage E1 (Double DQN + Cosine LR)
- Config highlights: LR=5e-5, EPS_DECAY=100k, TUF=300, Batch=4, StepMul=16

## Results (5 test episodes)
- Win rate: 20.0%
- Avg reward: 0.2

## Artifacts
- Local: `01 Projects/ARL RL/Experiment-Results/10-21-2025/20251021_164435_E1_seed8/`
- HPC: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164435_E1_seed8`

## Notes
- 2h standby chunk (~800 episodes) completed; similar to seed 8 smoke run.
- Continue chunking to reach ≥1000 episodes before cross‑seed comparison.

# Original Experiment Notes (Restored)

# Run 20251021_212805_E1_seed8 — Stage E1 top-up (+200 eps, 32×32)

- Timestamp (UTC): 2025-10-21T21:41:26.274751Z
- Seed: 8
- Episodes (top-up): 200 (after prior 800)
- Resolution: 32×32
- Algorithm: Stage E1 (Double DQN + Cosine LR)
- Config highlights: LR=5e-5, EPS_DECAY=100k, TUF=300, Batch=4, StepMul=16

## Results (100 test episodes)
- Win rate: 73.0%
- Avg reward: 1.91

## Artifacts
- Local: `01 Projects/ARL RL/Experiment-Results/10-21-2025/20251021_212805_E1_seed8/`
- HPC: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_212805_E1_seed8`