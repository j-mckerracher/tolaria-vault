---
title: "Confirm Best Parameters Seed 6"
experiment_id: "expt-20251005-confirm-best-seed6"
date: "2025-10-05"
last_updated: "2025-11-30T12:35:00Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "confirmation", "E1"]
dataset: ""
algorithm: "DQN"
params:
  LR: 0.00005
  EPS_DECAY: 20000
  TARGET_UPDATE_FREQ: 200
  SEED: 6
  RESOLUTION: "32x32"
  BATCH_SIZE: 8
  REPLAY_MEMORY_SIZE: 50000
  STEP_MUL: 8
seeds: [6]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_162324_confirm_best_seed6"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 29.0 }
  others:
    avg_reward: 0.56
hardware: {}
sources: []
related: []
---

## Summary
Confirmation run for best parameters using Seed 6.

## Goal
To confirm performance of best parameters (LR=0.00005, EPS_DECAY=20000, TUF=200) with Seed 6.

## Setup (Hardware/Software)
- **Environment:** Gilbreth (inferred)
- **Resolution:** 32x32
- **Batch Size:** 8
- **Replay Memory:** 50k
- **Step Multiplier:** 8

## Procedure
(No job details recorded)

## Results
- **Win Rate:** 29.0%
- **Avg Reward:** 0.56

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-05-expt-20251005-confirm-best-seed6.md]] — status: unknown

## Artifacts
- `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_162324_confirm_best_seed6`

## Changelog
- 2025-11-30T12:35:00Z Created from template, migrated from `20251005_162324_confirm_best_seed6.md`

# Original Experiment Notes (Restored)

# 20251005_162324_confirm_best_seed6 — Experiment Run

## Overview
- Run ID: 20251005_162324_confirm_best_seed6
- Objective: Confirm best parameters (LR=0.00005, EPS_DECAY=20000, TUF=200) — Seed 6
- Part: 1 = parameter-only

## Metadata
- Date/Time (UTC): 2025-10-05T16:29:14.785590Z
- LR: 0.00005
- EPS_DECAY: 20000
- TARGET_UPDATE_FREQ: 200
- Seed: 6
- Artifacts path: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_162324_confirm_best_seed6

## Results
- 100-episode test win rate: 29.0%
- Avg reward: 0.56

## Notes
- Confirmation run at 32×32 resolution, batch 8, replay 50k, step_mul 8.