---
title: "E3 PER Alpha Sweep — Tuning for Stability"
experiment_id: "expt-20251025-e3-per-sweep"
date: "2025-10-25"
last_updated: "2025-10-25T16:44:16Z"
status: "completed"
tags: ["project/arl-rl", "experiment", "e3", "per", "sweep", "ablation"]
stage: "E3"
algorithm: "Dueling Double DQN + PER"
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
  PER_ALPHA: "sweep: {0.4, 0.5}"
  PER_BETA_START: 0.6
  PER_BETA_END: 1.0
seeds: [4, 6, 8]
episodes: "300-500"
code_ref:
  repo: "C:\\Users\\jmckerra\\PycharmProjects\\ARL-RL"
  entrypoint: "training_split.py"
artifacts: "/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/run-2/"
job_ids: ["(HPC jobs)"]
metrics:
  primary:
    name: "100-episode test win rate"
    value: "sweep_results"
    alpha_0p4:
      mean: "below E2 baseline"
      seed_8_status: "still unstable"
    alpha_0p5:
      mean: "below E2 baseline"
      variance: "still high"
  comparison_to_e2_baseline:
    e2_baseline_mean: 91.3
    sweep_conclusion: "no alpha value matched E2 baseline"
hardware:
  gpu: 1
  gpu_model: "A30"
  cpu: 4
  ram_gb: 50
  partition: "a30"
sources:
  - "[[../../../Work Completed/2025-10-25 E3 PER exploration and parking decision]]"
related:
  - "[[expt-20251025-e3-per-smoke]] — Initial α=0.6 smoke (underperformed)"
  - "[[expt-20251025-e2-prod-3k]] — E2 baseline for comparison (94.3%)"
  - "[[../../../Decisions/2025-10-25 Park Stage E3 PER]] — Final parking decision"
---

## Summary
PER alpha sweep with α ∈ {0.4, 0.5}, β 0.6→1.0. **Conclusion: All configurations underperformed E2 baseline.** Seed 8 remained consistently unstable. No stable alpha found. **Decision: Park PER** and focus on E2 production validation.

## Goal
Find stable PER alpha configuration by testing lower values (0.4, 0.5) to reduce over-prioritization and improve training stability.

## Setup (Hardware/Software)
- **Environment**: Gilbreth HPC
- **GPU**: NVIDIA A30
- **QoS**: standby
- **Time per seed**: ~2-3 hours per alpha value

## Procedure
1. Test two alpha values: 0.4 and 0.5
2. Keep β 0.6→1.0, all E2 params locked
3. Run 300-500 episodes per seed per alpha
4. Evaluate final test performance
5. Compare against E2 baseline (91.3%)

## Results
### Alpha 0.4
- **Status**: Mean win rate below E2 baseline
- **Seed 8**: Still unstable, did not resolve from smoke run
- **Finding**: Reducing alpha alone insufficient

### Alpha 0.5
- **Status**: Mean win rate below E2 baseline
- **Variance**: Still elevated despite higher episodes than smoke
- **Finding**: Intermediate alpha also underperforms

### Aggregate
- **No sweep value** matched or exceeded E2 baseline (91.3%)
- **Seed 8 persistent issue**: Remains problematic across all PER configs
- **Trend**: Indicates PER fundamentally incompatible with task at this resolution

## Analysis
- **Root cause**: PER appears to amplify TD errors in sparse-reward environments
- **Seed 8 sensitivity**: Particular random initialization vulnerable to priority-based sampling
- **Configuration space**: No alpha/beta combination found that improves on vanilla E2
- **Sample efficiency vs stability tradeoff**: PER sacrifices stability gains without efficiency benefits
- **Next phase**: Focus on E2 production runs instead; consider PER revisit after major changes

## Issues
- Seed 8 training consistently disrupted by any PER configuration
- Possible underlying issue: TD errors on first encounters of important states amplified by priority

## Next Steps
- **DECISION: Park PER** — does not improve over E2 baseline
- Focus on E2 production (3k+ episodes) — **COMPLETED** (94.3% mean achieved)
- Consider resolution scaling (64×64) instead of algorithmic changes
- Revisit PER only after architecture/task changes

## Jobs
- [[../../Job-Submission-Commands/2025-10-25-expt-20251025-e3-per-sweep]]

## Artifacts
- Artifacts root: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/run-2/`

## Changelog
- 2025-10-25T16:44:16Z Created from template
- 2025-10-25T14:19 Documented in Work Completed; parking decision finalized

# Original Experiment Notes (Restored)

# E3 PER run-2 — Alpha Sweep (α=0.4, 0.5)

## Overview
- Run ID: run-2 (PER alpha sweep)
- Objective: Find stable PER alpha with α ∈ {0.4, 0.5}, β 0.6→1.0
- Part: Stage E3 — PER parameter tuning

## Config deltas (from E2 frozen baseline)
- PER_ENABLED: true
- PER_ALPHA: 0.4 or 0.5 (swept)
- PER_BETA_START: 0.6 (adjusted from 0.4)
- PER_BETA_END: 1.0
- NUM_EPISODES: 300-500 (sweep runs)
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
# Alpha 0.4
sbatch --account=sbagchi --partition=a30 --qos=standby --gres=gpu:1 \
  --ntasks=1 --cpus-per-task=4 --mem=50G --time=02:00:00 \
  --export=ALL,RL_SEED=<seed>,RL_NUM_EPISODES=500,RL_LEARNING_RATE=0.00005,\
RL_EPS_DECAY=100000,RL_BATCH_SIZE=4,RL_REPLAY_MEMORY_SIZE=100000,\
RL_SCREEN_RESOLUTION=32,RL_STEP_MUL=16,RL_TARGET_UPDATE_FREQ=400,\
RL_DUELING_DQN=1,RL_PER_ENABLED=1,RL_PER_ALPHA=0.4,RL_PER_BETA_START=0.6,\
RL_PER_BETA_END=1.0 \
  scripts/run_e3.sh

# Alpha 0.5
sbatch --account=sbagchi --partition=a30 --qos=standby --gres=gpu:1 \
  --ntasks=1 --cpus-per-task=4 --mem=50G --time=02:00:00 \
  --export=ALL,RL_SEED=<seed>,RL_NUM_EPISODES=500,RL_LEARNING_RATE=0.00005,\
RL_EPS_DECAY=100000,RL_BATCH_SIZE=4,RL_REPLAY_MEMORY_SIZE=100000,\
RL_SCREEN_RESOLUTION=32,RL_STEP_MUL=16,RL_TARGET_UPDATE_FREQ=400,\
RL_DUELING_DQN=1,RL_PER_ENABLED=1,RL_PER_ALPHA=0.5,RL_PER_BETA_START=0.6,\
RL_PER_BETA_END=1.0 \
  scripts/run_e3.sh
```
- Artifacts path: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/run-2/`

## Results
- Alpha 0.4 results (seeds 4, 6, 8):
  - Mean win rate: Below E2 baseline
  - Seed 8 still showing instability
- Alpha 0.5 results (seeds 4, 6, 8):
  - Mean win rate: Below E2 baseline
  - Variance still high, especially seed 8
- Aggregate across sweep:
  - No alpha value matched or exceeded E2 baseline (91.3%)
  - Seed 8 consistently unstable with PER enabled
  - Alpha reduction (0.6 → 0.5 → 0.4) did not resolve instability

## Observations
- Lower alpha values (0.4, 0.5) did not stabilize PER training
- Seed 8 remains problematic across all PER configurations tested
- PER may be fundamentally incompatible with current architecture/task
- E2 baseline (without PER) remains superior in both mean and variance
- Beta adjustment (0.6→1.0 vs 0.4→1.0) had minimal impact

## Next steps
- **Decision: Park PER** — does not improve over E2 baseline
- Proceed with E2 production runs: 2k-4k episodes per seed
- Document PER exploration and decision in Status/Plan
- Consider revisiting PER after resolution scaling or architecture changes
- Focus resources on E2 long-run validation and potential E4 (N-step returns)