---
title: "Baseline Run with Memory Constraints"
experiment_id: "expt-20251004-baseline"
date: "2025-10-04"
last_updated: "2025-11-30T12:00:00Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "baseline"]
dataset: ""
algorithm: "DQN"
params:
  BATCH_SIZE: 8
  REPLAY_MEMORY_SIZE: 5000
  SCREEN_RESOLUTION: 32
  MINIMAP_RESOLUTION: 32
  NUM_EPISODES: 100
  START_EPISODE: 0
  EPS_START: 0.90
  EPS_END: 0.05
  EPS_DECAY: 50000
  LEARNING_RATE: 0.0001
  TARGET_UPDATE_FREQ: 100
  STEP_MUL: 8
seeds: [4]
code_ref:
  repo: ""
  commit: ""
  entrypoint: "training_split.py"
artifacts: "/home/jmckerra/ARL-RL/runs/20251004_013929_baseline"
job_ids: []
metrics:
  primary: { name: "win_rate", value: 8.00, step: 100 }
  others:
    mean_reward: -0.43
hardware: { gpu: 1, cpu: 4, ram_gb: 24 } # CPU count assumed from typical SLURM config
sources: []
related: []
---

## Summary
First baseline run to establish performance with reduced GPU memory settings (32x32 resolution, smaller batch and replay memory).

## Goal
Establish a baseline win rate and verify memory optimization under memory-constrained settings.

## Setup (Hardware/Software)
- **Environment:** Gilbreth
- **Resources:** NVIDIA A30 24GB (used 23.2GB, 967MB free)
- **Code:** `training_split.py`

## Procedure
An interactive terminal session was used to run the experiment. Configuration was controlled via environment variables.

## Results
- **100-episode test win rate:** 8.00%
- **Mean/median test reward:** -0.43
- **Training:** 100 episodes completed successfully
- **Checkpoints:** `model_ep100.pth` saved
- **GPU:** No OOM errors with reduced settings

## Analysis
- Memory optimization was successful, no CUDA OOM.
- Win rate (8%) was lower than expected (20%) due to:
  - Reduced spatial resolution (64x64 -> 32x32)
  - Smaller batch size
  - Different random seed
  - Training from scratch

## Issues
- High baseline GPU memory usage (23.2GB/24GB) from other processes, indicating memory contention.

## Next Steps
- Try higher resolution (48x48 or 64x64) if memory allows.
- Increase batch size gradually to find memory limit.
- Run longer training (1000+ episodes) for better evaluation.
- Parameter sweep targets: EPS_DECAY, LEARNING_RATE, BATCH_SIZE, TARGET_UPDATE_FREQ.

## Jobs
- [[01 Projects/ARL-RL/Job-Submission-Commands/2025-10-04-expt-20251004-baseline.md]] — status: succeeded

## Artifacts
- Path: `/home/jmckerra/ARL-RL/runs/20251004_013929_baseline`

## Links

## Changelog
- 2025-11-30T12:00:00Z Created from template, migrated from `20251004_013929_baseline.md`

# Original Experiment Notes (Restored)

# 20251004_013929_baseline — Experiment Run

First baseline run with reduced GPU memory settings to establish current performance.

## Overview
- Run ID: 20251004_013929_baseline
- Objective: Establish baseline win rate with memory-constrained settings
- Part: 1 = parameter-only (memory optimization)

## Config deltas (from original baseline)
List only changed parameters, with previous -> new values.
- BATCH_SIZE: 32 -> 8
- REPLAY_MEMORY_SIZE: 10000 -> 5000
- SCREEN_RESOLUTION: 64 -> 32
- MINIMAP_RESOLUTION: 64 -> 32
- NUM_EPISODES: 10000 -> 100 (short test)
- START_EPISODE: 2000 -> 0 (train from scratch)
- EPS_START: 0.95 -> 0.90
- EPS_DECAY: 10000 -> 50000
- TARGET_UPDATE_FREQ: 20 -> 100
- SEED: 42 -> 4

## Metadata
- Date/Time (UTC): 2025-10-04 01:39:29
- Git commit: (not tracked - code repo not initialized)
- Branch: (not tracked)
- Seed(s): 4
- Environment: Gilbreth
- SLURM: [N/A - interactive terminal session]
- Resources: NVIDIA A30 24GB (23.2GB used, 967MB free)
- Command / Env overrides:
  ```bash
  export RL_BATCH_SIZE=8
  export RL_REPLAY_MEMORY_SIZE=5000
  export RL_SCREEN_RES=32
  export RL_MINIMAP_RES=32
  export RL_NUM_EPISODES=100
  export RL_START_EPISODE=0
  export RL_EPS_START=0.90
  export RL_EPS_END=0.05
  export RL_EPS_DECAY=50000
  export RL_LEARNING_RATE=0.0001
  export RL_TARGET_UPDATE_FREQ=100
  export RL_STEP_MUL=8
  export RL_SEED=4
  export RL_SAVE_PATH=/home/jmckerra/ARL-RL/runs
  export RL_RUN_ID=20251004_013929_baseline
  export SC2PATH=/home/jmckerra/StarCraftII
  export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
  python -u training_split.py
  ```
- Artifacts path: /home/jmckerra/ARL-RL/runs/20251004_013929_baseline

## Results
- 100-episode test win rate: 8.00%
- Mean/median test reward: -0.43
- Training: 100 episodes completed successfully
- Checkpoints: model_ep100.pth saved
- GPU: No OOM errors with reduced settings

## Observations
- What worked: Memory optimization successful, no CUDA OOM
- GPU memory usage: High baseline usage (23.2GB/24GB) from other processes
- NO_OP behavior: Not specifically monitored in this run
- Performance: 8% win rate is lower than expected 20% baseline, likely due to:
  - Reduced spatial resolution (64x64 -> 32x32) limiting visual information
  - Smaller batch size reducing learning stability  
  - Different random seed
  - Training from scratch vs. checkpoint

## Next steps
- Immediate follow-ups: 
  - Try higher resolution (48x48 or 64x64) if memory allows
  - Increase batch size gradually to find memory limit
  - Run longer training (1000+ episodes) for better evaluation
- Parameter sweep targets:
  - EPS_DECAY: try 20000-100000 range
  - LEARNING_RATE: try 5e-5, 1e-4, 2.5e-4
  - BATCH_SIZE: find maximum that fits in available GPU memory
  - TARGET_UPDATE_FREQ: try 50, 100, 200