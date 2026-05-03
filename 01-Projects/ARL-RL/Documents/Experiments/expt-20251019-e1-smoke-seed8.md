---
title: "E1 Smoke Validation Seed 8"
experiment_id: "expt-20251019-e1-smoke-seed8"
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
  SEED: 8
  RESOLUTION: "32x32"
  BATCH_SIZE: 2
  STEP_MUL: 32
  NUM_EPISODES: 300 # train
seeds: [8]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_151225_E1_seed8"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 20.0 }
  others:
    avg_reward: 0.0
    test_episodes: 5
hardware: { gpu: 1, cpu: 2, ram_gb: 20 }
sources: []
related: []
---

## Summary
Stage E1 smoke validation run (short, backfill-friendly) using Seed 8.

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
- **Win Rate:** 20.0% (5 test episodes)
- **Avg Reward:** 0.0

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-19-expt-20251019-e1-smoke-seed8.md]] — status: unknown

## Artifacts
- `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_151225_E1_seed8`

## Changelog
- 2025-11-30T12:38:00Z Created from template, migrated from `20251019_151225_E1_seed8.md`

# Original Experiment Notes (Restored)

# 20251019_151225_E1_seed8 — Experiment Run

## Overview
- Run ID: 20251019_151225_E1_seed8
- Objective: Stage E1 smoke validation (short, backfill-friendly)
- Part: Algorithmic upgrade — E1 (Double DQN + LR scheduler)

## Metadata
- Date/Time (UTC): 2025-10-19T15:23:35.583000Z
- Resolution: 32×32
- Episodes (train): 300
- Test episodes: 5
- Seed(s): 8
- LR: 0.00005
- EPS_DECAY: 100000
- TARGET_UPDATE_FREQ: 300
- Batch size: 2
- Step multiplier: 32
- Artifacts path: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251019_151225_E1_seed8
- Aggregation CSV: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/e1_results.csv
- SLURM: a30 / sbagchi / standby, 1h, 1×GPU, 2 CPU, 20G mem

## Results
- 5-episode test win rate: 20.0%
- Avg reward: 0.0
- CSV entry:
  - timestamp_utc: 2025-10-19T15:23:35.583000Z
  - run_id: 20251019_151225_E1_seed8, seed: 8
  - lr: 0.00005, eps_decay: 100000, target_update: 300
  - artifacts_path: as above

## Notes
- Moderate result with small-sample test; consider more episodes or longer training confirms for stability.