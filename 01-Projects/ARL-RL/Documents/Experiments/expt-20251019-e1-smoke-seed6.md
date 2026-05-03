---
title: "E1 Smoke Validation Seed 6"
experiment_id: "expt-20251019-e1-smoke-seed6"
date: "2025-10-19"
last_updated: "2025-11-30T12:38:00Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "smoke", "E1"]
dataset: ""
algorithm: "Double DQN"
params:
  LR: 0.00005
  EPS_DECAY: 100000
  TARGET_UPDATE_FREQ: 300
  SEED: 6
  RESOLUTION: "32x32"
  BATCH_SIZE: 2
  STEP_MUL: 32
  NUM_EPISODES: 300 # train
seeds: [6]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_041819_E1_seed6"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 0.0 }
  others:
    avg_reward: 0.0
    test_episodes: 5
hardware: { gpu: 1, cpu: 2, ram_gb: 20 }
sources: []
related: []
---

## Summary
Stage E1 smoke validation run (short, backfill-friendly) using Seed 6.

## Goal
To validate the E1 configuration (Double DQN + LR scheduler) with a short, low-resource run.

## Setup (Hardware/Software)
- **Cluster:** Gilbreth
- **Partition:** standby
- **Resources:** 1 GPU (A30), 2 CPUs, 20GB Mem, 1h limit
- **Resolution:** 32x32
- **Batch Size:** 2
- **Step Multiplier:** 32

## Procedure
Submitted as a short job to fit backfill windows.

## Results
- **Win Rate:** 0.0% (5 test episodes)
- **Avg Reward:** 0.0

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-19-expt-20251019-e1-smoke-seed6.md]] — status: unknown

## Artifacts
- `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_041819_E1_seed6`

## Changelog
- 2025-11-30T12:38:00Z Created from template, migrated from `20251019_041819_E1_seed6.md`

# Original Experiment Notes (Restored)

# 20251019_041819_E1_seed6 — Experiment Run

## Overview
- Run ID: 20251019_041819_E1_seed6
- Objective: Stage E1 smoke validation (short, backfill-friendly)
- Part: Algorithmic upgrade — E1 (Double DQN + LR scheduler)

## Metadata
- Date/Time (UTC): 2025-10-19T04:30:34.579959Z
- Resolution: 32×32
- Episodes (train): 300
- Test episodes: 5
- Seed(s): 6
- LR: 0.00005
- EPS_DECAY: 100000
- TARGET_UPDATE_FREQ: 300
- Batch size: 2
- Step multiplier: 32
- Artifacts path: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_041819_E1_seed6
- Aggregation CSV: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/e1_results.csv
- SLURM: a30 / sbagchi / standby, 1h, 1×GPU, 2 CPU, 20G mem

## Results
- 5-episode test win rate: 0.0%
- Avg reward: 0.0
- CSV entry:
  - timestamp_utc: 2025-10-19T04:30:34.579959Z
  - run_id: 20251019_041819_E1_seed6, seed: 6
  - lr: 0.00005, eps_decay: 100000, target_update: 300
  - artifacts_path: as above

## Notes
- No wins in 5 test episodes; consider increasing test episodes for stability or extending training before test.