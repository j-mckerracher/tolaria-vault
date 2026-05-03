---
title: "E1 Chunk 1 Seed 4"
experiment_id: "expt-20251021-e1-chunk1-seed4"
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
  SEED: 4
  RESOLUTION: "32x32"
  BATCH_SIZE: 4
  STEP_MUL: 16
  NUM_EPISODES: 800
seeds: [4]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164433_E1_seed4"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 20.0 }
  others:
    avg_reward: 1.0
    test_episodes: 5
hardware: {}
sources: []
related: []
---

## Summary
First 800-episode chunk for Seed 4 in Stage E1 production.

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
- **Avg Reward:** 1.0

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-21-expt-20251021-e1-chunk1-seed4.md]] — status: unknown

## Artifacts
- `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164433_E1_seed4`

## Changelog
- 2025-11-30T12:42:00Z Created from template, migrated from `20251021_164433_E1_seed4.md`

# Original Experiment Notes (Restored)

# Run 20251021_164433_E1_seed4 — Stage E1 (800 eps, 32×32)

- Timestamp (UTC): 2025-10-21T17:12:56.304104Z
- Seed: 4
- Episodes: 800
- Resolution: 32×32
- Algorithm: Stage E1 (Double DQN + Cosine LR)
- Config highlights: LR=5e-5, EPS_DECAY=100k, TUF=300, Batch=4, StepMul=16

## Results (5 test episodes)
- Win rate: 20.0%
- Avg reward: 1.0

## Artifacts
- Local: `01 Projects/ARL RL/Experiment-Results/10-21-2025/20251021_164433_E1_seed4/`
- HPC: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_164433_E1_seed4`

## Notes
- 2h standby chunk (~800 episodes) completed; lower win rate vs earlier 300‑ep smoke for seed 4.
- Continue chunking to reach ≥1000 episodes before cross‑seed comparison.

# Original Experiment Notes (Restored)

# Run 20251021_212042_E1_seed4 — Stage E1 top-up (+200 eps, 32×32)

- Timestamp (UTC): 2025-10-21T21:30:44.846851Z
- Seed: 4
- Episodes (top-up): 200 (after prior 800)
- Resolution: 32×32
- Algorithm: Stage E1 (Double DQN + Cosine LR)
- Config highlights: LR=5e-5, EPS_DECAY=100k, TUF=300, Batch=4, StepMul=16

## Results (100 test episodes)
- Win rate: 59.0%
- Avg reward: 1.21

## Artifacts
- Local: `01 Projects/ARL RL/Experiment-Results/10-21-2025/20251021_212042_E1_seed4/`
- HPC: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_212042_E1_seed4`