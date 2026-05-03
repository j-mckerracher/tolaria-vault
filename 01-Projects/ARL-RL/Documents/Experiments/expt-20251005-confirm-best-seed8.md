---
title: "Confirm Best Parameters Seed 8"
experiment_id: "expt-20251005-confirm-best-seed8"
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
  SEED: 8
  RESOLUTION: "32x32"
  BATCH_SIZE: 8
  REPLAY_MEMORY_SIZE: 50000
  STEP_MUL: 8
seeds: [8]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_165549_confirm_best_seed8"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 7.0 }
  others:
    avg_reward: 0.05
hardware: {}
sources: []
related: []
---

## Summary
Confirmation run for best parameters using Seed 8.

## Goal
To confirm performance of best parameters (LR=0.00005, EPS_DECAY=20000, TUF=200) with Seed 8.

## Setup (Hardware/Software)
- **Environment:** Gilbreth
- **Resolution:** 32x32
- **Batch Size:** 8
- **Replay Memory:** 50k
- **Step Multiplier:** 8
- **Log File:** `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/logs/20251005_165549_confirm_best_seed8.log`

## Procedure
(No job details recorded)

## Results
- **Win Rate:** 7.0%
- **Avg Reward:** 0.05
- **Note:** Trained from scratch on cuda device.

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-05-expt-20251005-confirm-best-seed8.md]] — status: unknown

## Artifacts
- `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_165549_confirm_best_seed8`

## Changelog
- 2025-11-30T12:35:00Z Created from template, migrated from `20251005_165549_confirm_best_seed8.md`

# Original Experiment Notes (Restored)

# 20251005_165549_confirm_best_seed8 — Experiment Run

## Overview
- Run ID: 20251005_165549_confirm_best_seed8
- Objective: Confirm best parameters (LR=0.00005, EPS_DECAY=20000, TUF=200) — Seed 8
- Part: 1 = parameter-only

## Metadata
- Date/Time (UTC): 2025-10-05T19:08:42.867186Z
- LR: 0.00005
- EPS_DECAY: 20000
- TARGET_UPDATE_FREQ: 200
- Seed: 8
- Artifacts path: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_165549_confirm_best_seed8
- Log file: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/logs/20251005_165549_confirm_best_seed8.log

## Results
- 100-episode test win rate: 7.0%
- Avg reward: 0.05

## Notes
- Confirmation run at 32×32 resolution, batch 8, replay 50k, step_mul 8.
- Trained from scratch on device: cuda (per log).