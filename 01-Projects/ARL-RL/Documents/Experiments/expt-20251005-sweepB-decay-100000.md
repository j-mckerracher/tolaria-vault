---
title: "Sweep B Epsilon Decay 100000"
experiment_id: "expt-20251005-sweepB-decay-100000"
date: "2025-10-05"
last_updated: "2025-11-30T12:20:00Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "sweep", "epsilon-decay", "E1"]
dataset: ""
algorithm: "DQN"
params:
  LR: 0.0001
  EPS_DECAY: 100000
  TARGET_UPDATE_FREQ: 100
  RESOLUTION: "32x32" # Inferred from notes
  BATCH_SIZE: 8 # Inferred from notes
  REPLAY_MEMORY_SIZE: 50000 # Inferred from notes
seeds: []
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_033032_sweepB_decay_100000"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 10.0 }
  others:
    avg_reward: 0.10
hardware: {}
sources: []
related: []
---

## Summary
This experiment was part of Sweep B, investigating the impact of an epsilon decay value of 100000.

## Goal
To test the epsilon decay candidate (EPS_DECAY=100000) as part of Sweep B.

## Setup (Hardware/Software)
- **Environment:** Gilbreth (inferred from artifacts path)
- **Resolution:** 32x32
- **Batch Size:** 8
- **Replay Memory Size:** 50,000

## Procedure
Specific procedure details (e.g., job submission commands) are not explicitly recorded in this legacy note.

## Results
- **100-episode test win rate:** 10.0%
- **Average reward:** 0.10

## Analysis
The note provides no explicit analysis beyond the results.

## Issues
Lack of detailed setup information and job commands.

## Next Steps
(Not specified in original note)

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-05-expt-20251005-sweepB-decay-100000.md]] — status: unknown

## Artifacts
- Path: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_033032_sweepB_decay_100000`

## Links

## Changelog
- 2025-11-30T12:20:00Z Created from template, migrated from `20251005_033032_sweepB_decay_100000.md`

# Original Experiment Notes (Restored)

# 20251005_033032_sweepB_decay_100000 — Experiment Run

## Overview
- Run ID: 20251005_033032_sweepB_decay_100000
- Objective: Sweep B — test epsilon decay (EPS_DECAY=100000)
- Part: 1 = parameter-only

## Metadata
- Date/Time (UTC): 2025-10-05T04:27:18.907302Z
- LR: 0.0001
- EPS_DECAY: 100000
- TARGET_UPDATE_FREQ: 100
- Artifacts path: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_033032_sweepB_decay_100000

## Results
- 100-episode test win rate: 10.0%
- Avg reward: 0.10

## Notes
- Sweep B (Epsilon Decay). Resolution: 32×32 (assumed). Batch: 8. Replay: 50k.