---
title: "E3 PER Smoke — Initial Testing (α=0.6)"
experiment_id: "expt-20251025-e3-per-smoke"
date: "2025-10-25"
last_updated: "2025-10-25T16:44:16Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "e3", "per", "ablation"]
stage: "E3"
algorithm: "Dueling Double DQN + PER (Prioritized Experience Replay)"
dataset: "SC2 FindAndDefeatZerglings"
params:
  LR: 5e-5
  EPS_DECAY: 100000
  BATCH_SIZE: 4
  REPLAY_MEMORY_SIZE: 100000
  TARGET_UPDATE_FREQ: 400
  SCREEN_RESOLUTION: 32
  MINIMAP_RESOLUTION: 32
  STEP_MUL: 16
  USE_DUELING_DQN: true
  PER_ENABLED: true
  PER_ALPHA: 0.6
  PER_BETA_START: 0.4
  PER_BETA_END: 1.0
seeds: [4, 6, 8]
episodes: 500
code_ref:
  repo: "C:\\Users\\jmckerra\\PycharmProjects\\ARL-RL"
  entrypoint: "training_split.py"
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/E3-smoke/"
job_ids: ["(HPC jobs, standby QoS)"]
metrics:
  primary:
    name: "100-episode test win rate"
    value: "mixed"
    seed_breakdown:
      seed_4: "60-70%"
      seed_6: "50-60%"
      seed_8: "10-15%"
  comparison_to_e2_baseline:
    e2_baseline_mean: 91.3
    e3_smoke_status: "below baseline"
hardware:
  gpu: 1
  gpu_model: "A30"
  cpu: 4
  ram_gb: 50
  partition: "a30"
sources:
  - "[[../../../Experiments|Experiments.md]]"
  - "[[../../../Work Completed/2025-10-25 E3 PER exploration and parking decision]]"
related:
  - "[[expt-20251025-e2-prod-3k]] — E2 baseline (94.3%)"
  - "[[expt-20251025-e3-per-sweep]] — Alpha sweep follow-up"
  - "[[../../../Decisions/2025-10-25 Park Stage E3 PER]] — Parking decision"
---

# E3 PER Smoke — Prioritized Experience Replay Initial Test

## Overview
- Run ID: E3 PER smoke (seeds 4, 6, 8)
- Objective: Initial validation of PER with α=0.6, β annealing 0.4→1.0
- Part: Stage E3 — Prioritized Experience Replay

## Config deltas (from E2 frozen baseline)
- PER_ENABLED: true
- PER_ALPHA: 0.6
- PER_BETA_START: 0.4
- PER_BETA_END: 1.0
- NUM_EPISODES: 500 (smoke test)
- All E2 parameters locked:
  - LR: 5e-5
  - EPS_DECAY: 100000
  - BATCH_SIZE: 4
  - REPLAY_MEMORY_SIZE: 100000
  - STEP_MUL: 16
  - SCREEN_RESOLUTION: 32
  - TARGET_UPDATE_FREQ: 400
  - DUELING_DQN: enabled

## Metadata
- Date/Time (UTC): 2025-10-25
- Git commit: (not tracked)
- Branch: main
- Seed(s): 4, 6, 8
- Environment: Gilbreth HPC
- SLURM: account=sbagchi, partition=a30, QoS=standby
- Resources: 1 GPU A30, 4 CPUs, 50GB RAM per job
- Command / Env overrides:
```bash
sbatch --account=sbagchi --partition=a30 --qos=standby --gres=gpu:1 \
  --ntasks=1 --cpus-per-task=4 --mem=50G --time=02:00:00 \
  --export=ALL,RL_SEED=<seed>,RL_NUM_EPISODES=500,RL_LEARNING_RATE=0.00005,\
RL_EPS_DECAY=100000,RL_BATCH_SIZE=4,RL_REPLAY_MEMORY_SIZE=100000,\
RL_SCREEN_RESOLUTION=32,RL_STEP_MUL=16,RL_TARGET_UPDATE_FREQ=400,\
RL_DUELING_DQN=1,RL_PER_ENABLED=1,RL_PER_ALPHA=0.6,RL_PER_BETA_START=0.4,\
RL_PER_BETA_END=1.0 \
  scripts/run_e3.sh
```
- Artifacts path: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/E3-smoke/`

## Results
- 100-episode test win rates:
  - Seed 4: ~60-70% (decent)
  - Seed 6: ~50-60% (decent)
  - Seed 8: ~10-15% (poor, unstable)
- Aggregate: Mixed results with high variance
- Mean win rate below E2 baseline (91.3%)
- Seed 8 showed significant instability with α=0.6

## Observations
- PER with α=0.6 introduced training instability, especially for seed 8
- Seeds 4 and 6 showed acceptable but degraded performance vs. E2
- High alpha may be over-prioritizing rare transitions
- Beta annealing 0.4→1.0 did not stabilize training sufficiently
- Results suggest need for alpha sweep to find stable operating point

## Next steps
- Run PER alpha sweep: α ∈ {0.4, 0.5} with β 0.6→1.0
- 300-500 episodes per seed for faster iteration
- Keep all other E2 parameters locked
- If alpha sweep fails to match E2 baseline, park PER and proceed with E2 production runs