---
title: "E1 Chunk 2 (Top-up) Seed 6"
experiment_id: "expt-20251021-e1-chunk2-seed6"
date: "2025-10-21"
last_updated: "2025-11-30T12:46:00Z"
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
  NUM_EPISODES: 200 # top-up
seeds: [6]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_212805_E1_seed6"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 0.0 }
  others:
    avg_reward: 0.0
    test_episodes: 100
hardware: {}
sources: []
related: ["[[01 Projects/ARL-RL/Documents/Experiments/expt-20251021-e1-chunk1-seed6]]"]
---
## Summary
Top-up run (+200 episodes) for Seed 6 in Stage E1, bringing total to ~1000.

## Goal
To reach ~1000 episodes for cross-seed comparison.

## Setup (Hardware/Software)
- **Environment:** Gilbreth
- **Resolution:** 32x32
- **Batch Size:** 4
- **Step Multiplier:** 16

## Procedure
Continuation from previous 800-episode chunk.

## Results
- **Win Rate:** 0.0% (100 test episodes)
- **Avg Reward:** 0.0

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-21-expt-20251021-e1-chunk2-seed6.md]] — status: unknown

## Artifacts
- `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251021_212805_E1_seed6`

## Changelog
- 2025-11-30T12:46:00Z Created from template, migrated from `20251021_212805_E1_seed6.md`
