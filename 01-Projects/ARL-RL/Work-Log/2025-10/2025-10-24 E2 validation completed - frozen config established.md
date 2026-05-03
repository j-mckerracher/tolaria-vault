---
project: ARL RL
tags: [project/arl-rl, log]
created: 2025-10-24
---

# 2025-10-24 — E2 validation completed; config frozen

## Summary
- Completed 1,000‑episode confirm runs at 32×32 with E2 dueling + TUF=400 and locked E1 hyperparams.
- Results: seed4=86%, seed6=99%, seed8=89% (mean=91.3%, low variance).
- Decision: E2 confirmed; configuration frozen for downstream stages (see [[E2 Config Freeze]]).

## Configuration (frozen)
- USE_DUELING_DQN=true (non-spatial head); USE_DOUBLE_DQN=true; LR_SCHEDULER=cosine
- RL_LEARNING_RATE=5e-5; RL_EPS_START=0.90; RL_EPS_END=0.01; RL_EPS_DECAY=100000
- RL_TARGET_UPDATE_FREQ=400; RL_BATCH_SIZE=4; RL_REPLAY_MEMORY_SIZE=100000
- RL_SCREEN_RES=32; RL_MINIMAP_RES=32; RL_STEP_MUL=16

## Artifacts
- Local results hub: `C:\Users\jmckerra\ObsidianNotes\Main\01 Projects\ARL RL\Experiment-Results\10-22-2025\run-6`
- HPC run dirs: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251023_*_E1_seed{4,6,8}`
