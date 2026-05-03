---
title: "Sweep C Target Update Frequency 200"
experiment_id: "expt-20251005-sweepC-tuf-200"
date: "2025-10-05"
last_updated: "2025-11-30T12:29:00Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "sweep", "target-update-frequency", "E1"]
dataset: ""
algorithm: "DQN"
params:
  LR: 0.0001
  EPS_DECAY: 50000
  TARGET_UPDATE_FREQ: 200
  RESOLUTION: "32x32" # Inferred from notes
  BATCH_SIZE: 8 # Inferred from notes
  REPLAY_MEMORY_SIZE: 50000 # Inferred from notes
seeds: []
code_ref:
  repo: ""
  commit: ""
  entrypoint: ""
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_070524_sweepC_tuf_200"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 53.0 }
  others:
    avg_reward: 1.47
hardware: {}
sources: []
related: []
---

## Summary
This experiment was part of Sweep C, investigating the impact of a target update frequency of 200.

## Goal
To test the target update frequency candidate (TUF=200) as part of Sweep C.

## Setup (Hardware/Software)
- **Environment:** Gilbreth (inferred from artifacts path)
- **Resolution:** 32x32
- **Batch Size:** 8
- **Replay Memory Size:** 50,000

## Procedure
Specific procedure details (e.g., job submission commands) are not explicitly recorded in this legacy note.

## Results
- **100-episode test win rate:** 53.0%
- **Average reward:** 1.47

## Analysis
The note provides no explicit analysis beyond the results.

## Issues
Lack of detailed setup information and job commands.

## Next Steps
(Not specified in original note)

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-05-expt-20251005-sweepC-tuf-200.md]] — status: unknown

## Artifacts
- Path: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_070524_sweepC_tuf_200`

## Links

## Changelog
- 2025-11-30T12:29:00Z Created from template, migrated from `20251005_070524_sweepC_tuf_200.md`

# Original Experiment Notes (Restored)

# 20251005_070524_sweepC_tuf_200 — Experiment Run

## Overview
- Run ID: 20251005_070524_sweepC_tuf_200
- Objective: Sweep C — test target update frequency (TUF=200)
- Part: 1 = parameter-only

## Metadata
- Date/Time (UTC): 2025-10-05T08:05:55.693502Z
- LR: 0.0001
- EPS_DECAY: 50000
- TARGET_UPDATE_FREQ: 200
- Artifacts path: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced//20251005_070524_sweepC_tuf_200

## Results
- 100-episode test win rate: 53.0%
- Avg reward: 1.47

## Notes
- Sweep C (Target Update Frequency). Resolution: 32×32 (assumed). Batch: 8. Replay: 50k.