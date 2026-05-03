---
project: ARL RL
tags: [project/arl-rl, work-completed]
created: 2025-10-25
---

# E3 PER Exploration & Parking Decision — 2025-10-25

## Summary
Completed Stage E3 (Prioritized Experience Replay) exploration through smoke runs and alpha sweep. PER consistently underperformed E2 baseline across all tested configurations (α∈{0.4, 0.5, 0.6}, β annealing). **Decision: Park PER** and proceed with E2 production runs.

## Work completed

### E3 PER smoke runs (α=0.6, β=0.4→1.0)
- **Objective**: Initial validation of PER with baseline alpha/beta values
- **Configuration**: E2 frozen config + PER enabled (α=0.6, β=0.4→1.0)
- **Seeds**: 4, 6, 8
- **Episodes**: 500 per seed
- **Results**:
  - Seed 4: ~60-70% (decent but below E2)
  - Seed 6: ~50-60% (decent but below E2)
  - Seed 8: ~10-15% (severe instability)
  - Aggregate mean: Well below E2 baseline (91.3%)
- **Observation**: Seed 8 showed severe instability with PER enabled
- **Artifacts**: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/E3-smoke/`

### E3 PER alpha sweep (run-2: α∈{0.4, 0.5}, β=0.6→1.0)
- **Objective**: Find stable alpha configuration by testing lower values
- **Configuration**: E2 frozen config + PER with swept alpha values
- **Seeds**: 4, 6, 8
- **Episodes**: 300-500 per seed
- **Alpha values tested**: 0.4, 0.5
- **Beta annealing**: Adjusted to 0.6→1.0 (from 0.4→1.0 in smoke)
- **Results**:
  - Alpha 0.4: Mean below E2 baseline; seed 8 still unstable
  - Alpha 0.5: Mean below E2 baseline; high variance persists
  - No alpha value matched or exceeded E2 baseline
  - Seed 8 consistently problematic across all PER configurations
- **Artifacts**: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/run-2/`

### Decision: Park PER
- **Rationale**: 
  - PER underperforms E2 baseline across all tested configurations
  - High-priority sampling destabilizes training
  - Seed 8 consistently unstable with PER
  - E2 without PER already achieves excellent performance (91.3%)
- **Documentation**: Created [[2025-10-25 Park Stage E3 PER]]
- **Next step**: E2 production runs (2k-4k episodes per seed)

## Commands used

### Smoke runs (α=0.6)
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

### Alpha sweep (α=0.4, 0.5)
```bash
# Alpha 0.4
sbatch ... RL_PER_ALPHA=0.4,RL_PER_BETA_START=0.6 ...

# Alpha 0.5
sbatch ... RL_PER_ALPHA=0.5,RL_PER_BETA_START=0.6 ...
```

## Impact
- Comprehensive PER exploration completed
- Decision made based on solid empirical evidence
- Resources can now focus on E2 production validation
- PER revisit criteria documented for future consideration

## Observations & lessons learned
- PER may be incompatible with current task/architecture at 32×32 resolution
- High-priority sampling can destabilize learning in sparse reward environments
- Not all algorithmic improvements from literature generalize to all tasks
- Sometimes simpler approaches (E2 without PER) outperform more complex ones

## Future considerations
Revisit PER if:
- Resolution scales to 64×64 or higher
- Architecture changes significantly
- Task complexity increases
- Sample efficiency becomes critical bottleneck

## Experiment logs
- [[20251025_E3_PER_smoke]]
- [[20251025_E3_PER_run2_alpha_sweep]]

## Related
- [[Status]] — Updated with E3 parking decision
- [[01 Projects/ARL-RL/Plan]] — Updated next steps to E2 production
- [[Experiments]] — Added E3 entries to summary table
- [[2025-10-25 Park Stage E3 PER]] — Parking decision documented
