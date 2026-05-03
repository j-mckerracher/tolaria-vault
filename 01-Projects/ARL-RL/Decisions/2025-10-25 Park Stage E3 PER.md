---
project: ARL RL
tags: [project/arl-rl, decision]
created: 2025-10-25
---

# Park Stage E3 (PER) — 2025-10-25

**Decision**: Park Prioritized Experience Replay (PER) exploration. PER does not improve over E2 baseline across multiple alpha configurations. Proceed with E2 production runs (2k-4k episodes per seed) instead.

## Rationale

### E3 PER smoke results (α=0.6, β=0.4→1.0)
- Seed 4: ~60-70% win rate (decent but below E2)
- Seed 6: ~50-60% win rate (decent but below E2)
- Seed 8: ~10-15% win rate (severe instability)
- Aggregate mean: Well below E2 baseline of 91.3%

### E3 PER alpha sweep (run-2: α∈{0.4, 0.5}, β=0.6→1.0)
- Alpha 0.4: Mean win rate below E2 baseline; seed 8 still unstable
- Alpha 0.5: Mean win rate below E2 baseline; high variance persists
- No alpha value tested matched or exceeded E2 baseline performance
- Seed 8 consistently problematic across all PER configurations

### E2 baseline comparison
- E2 (Dueling DQN, no PER): 91.3% mean, 4.0 pp stdev
- Seeds: 4=92%, 6=95%, 8=87%
- Outstanding stability and reproducibility

## Evidence
- Smoke run artifacts: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/E3-smoke/`
- Alpha sweep artifacts: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/run-2/`
- Experiment logs:
  - [[20251025_E3_PER_smoke]]
  - [[20251025_E3_PER_run2_alpha_sweep]]

## Observations
- PER may be fundamentally incompatible with current task/architecture at 32×32 resolution
- High-priority sampling appears to destabilize training, especially for certain seeds
- Beta annealing adjustments (0.4→1.0 vs 0.6→1.0) had minimal stabilizing effect
- E2 without PER is already achieving excellent performance

## Next steps
- **Immediate**: Submit E2 production runs (2k-4k episodes per seed, frozen E2 config)
- **Future consideration**: Revisit PER after:
  - Resolution scaling (64×64 or higher)
  - Architecture changes
  - Task complexity increases
  - If sample efficiency becomes critical bottleneck

## Frozen E2 configuration (baseline going forward)
- DUELING_DQN: enabled
- LR: 5e-5
- EPS_DECAY: 100000
- TARGET_UPDATE_FREQ: 400
- BATCH_SIZE: 4
- REPLAY_MEMORY_SIZE: 100000
- SCREEN_RESOLUTION: 32
- STEP_MUL: 16
- PER: **disabled**
