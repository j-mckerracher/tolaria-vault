---
project: ARL RL
tags: [project/arl-rl, work-completed]
created: 2025-10-25
---

# E2 Dueling DQN Validation & Config Freeze — 2025-10-25

## Summary
Successfully validated Stage E2 (Dueling DQN) through TUF-sweep-alt-3 (500 episodes) and 1k-episode confirmatory runs (run-6). E2 configuration achieved 91.3% mean win rate with 4.0 pp stdev across seeds 4, 6, and 8. Configuration frozen for production use.

## Work completed

### TUF-sweep-alt-3 (500 episodes, gate validation)
- **Objective**: Validate dueling DQN with TUF=400 and E2 baseline hyperparameters
- **Configuration**: Dueling DQN enabled, TUF=400, LR=5e-5, EPS_DECAY=100k, Batch=4, Replay=100k, Res=32, StepMul=16
- **Seeds**: 4, 6, 8
- **Results**: 
  - Seed 4: 56.0%
  - Seed 6: 68.0%
  - Seed 8: 34.0%
  - Mean: 52.7%, StdDev: 35.9 pp
- **Gate criterion**: PASSED (mean ≥ 44%, stdev < 40 pp)
- **Artifacts**: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/TUF-sweep-alt-3/`

### run-6 (1,000-episode confirmatory runs)
- **Objective**: Confirm E2 performance at 1k episodes per seed
- **Configuration**: Same as TUF-sweep-alt-3 with NUM_EPISODES=1000
- **Seeds**: 4, 6, 8
- **Results**:
  - Seed 4: 92.0%
  - Seed 6: 95.0%
  - Seed 8: 87.0%
  - Mean: 91.3%, StdDev: 4.0 pp
- **Outcome**: **E2 CONFIRMED** — Outstanding performance and stability
- **Artifacts**: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/run-6/`

### Configuration freeze
- **Decision**: Freeze E2 configuration as production baseline
- **Documentation**: Created [[E2 Config Freeze]]
- **Frozen parameters**:
  - DUELING_DQN: enabled
  - LR: 5e-5
  - EPS_DECAY: 100000
  - TARGET_UPDATE_FREQ: 400
  - BATCH_SIZE: 4
  - REPLAY_MEMORY_SIZE: 100000
  - SCREEN_RESOLUTION: 32
  - STEP_MUL: 16

## Impact
- E2 baseline vastly outperforms E1 (44.0% → 91.3% mean win rate)
- Low variance (4.0 pp stdev) indicates stable, reproducible training
- All three seeds performed strongly (87-95% range)
- Configuration ready for long-duration production runs

## Experiment logs
- [[20251025_E2_TUF_sweep_alt3]]
- [[20251025_E2_run6_confirm_1k]]

## Related
- [[Status]] — Updated with E2 confirmation
- [[01 Projects/ARL-RL/Plan]] — Updated with E2 production next steps
- [[Experiments]] — Added E2 entries to summary table
- [[E2 Config Freeze]] — Frozen configuration documented
