---
title: "Confirm Best Parameters Seed 4"
experiment_id: "expt-20251005-confirm-best-seed4"
date: "2025-10-05"
last_updated: "2025-11-30T12:32:00Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "confirmation", "E1"]
dataset: ""
algorithm: "DQN"
params:
  LR: 0.00005
  EPS_DECAY: 20000
  TARGET_UPDATE_FREQ: 200
  SEED: 4
  RESOLUTION: "32x32" # Inferred from notes
  BATCH_SIZE: 8 # Inferred from notes
  REPLAY_MEMORY_SIZE: 50000 # Inferred from notes
  STEP_MUL: 8 # Inferred from notes
seeds: [4]
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_161708_confirm_best_seed4"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 37.0 }
  others:
    avg_reward: 0.46
hardware: {}
sources: []
related: []
---

## Summary
This experiment aimed to confirm the best parameters identified from previous sweeps using Seed 4.

## Goal
To confirm the performance of best-performing parameters (LR=0.00005, EPS_DECAY=20000, TUF=200) with Seed 4.

## Setup (Hardware/Software)
- **Environment:** Gilbreth (inferred from artifacts path)
- **Resolution:** 32x32
- **Batch Size:** 8
- **Replay Memory Size:** 50,000
- **Step Multiplier:** 8

## Procedure
Specific procedure details (e.g., job submission commands) are not explicitly recorded in this legacy note.

## Results
- **100-episode test win rate:** 37.0%
- **Average reward:** 0.46

## Analysis
The note provides no explicit analysis beyond the results.

## Issues
Lack of detailed setup information and job commands.

## Next Steps
(Not specified in original note)

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-05-expt-20251005-confirm-best-seed4.md]] — status: unknown

## Artifacts
- Path: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_161708_confirm_best_seed4`

## Links

## Changelog
- 2025-11-30T12:32:00Z Created from template, migrated from `20251005_161708_confirm_best_seed4.md`

# Original Experiment Notes (Restored)

# 20251005_161708_confirm_best_seed4 — Experiment Run

## Overview
- Run ID: 20251005_161708_confirm_best_seed4
- Objective: Confirm best parameters (LR=0.00005, EPS_DECAY=20000, TUF=200) — Seed 4
- Part: 1 = parameter-only

## Metadata
- Date/Time (UTC): 2025-10-05T16:23:24.353115Z
- LR: 0.00005
- EPS_DECAY: 20000
- TARGET_UPDATE_FREQ: 200
- Seed: 4
- Artifacts path: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_161708_confirm_best_seed4

## Results
- 100-episode test win rate: 37.0%
- Avg reward: 0.46

## Notes
- Confirmation run at 32×32 resolution, batch 8, replay 50k, step_mul 8.