---
project: ARL RL
tags: [project/arl-rl, decision]
created: 2025-10-24
---

# E2 Config Freeze — 2025-10-24

Decision: Freeze the E2 configuration based on 1,000‑episode confirm runs (mean=91.3%; seeds 4=86%, 6=99%, 8=89%). Proceed to E3 using this as the fixed baseline.

## Frozen configuration
- USE_DUELING_DQN: true (non-spatial head)
- USE_DOUBLE_DQN: true
- LR_SCHEDULER: cosine (min_lr=1e-6)
- RL_LEARNING_RATE: 0.00005
- RL_EPS_START: 0.90
- RL_EPS_END: 0.01
- RL_EPS_DECAY: 100000
- RL_TARGET_UPDATE_FREQ: 400
- RL_BATCH_SIZE: 4
- RL_REPLAY_MEMORY_SIZE: 100000
- RL_SCREEN_RES / RL_MINIMAP_RES: 32
- RL_STEP_MUL: 16
- NUM_TEST_EPISODES: 100

## Evidence
- 1k‑episode confirm runs (run-6):
  - 20251023_202213_E1_seed4 → win_rate=86%
  - 20251023_211015_E1_seed6 → win_rate=99%
  - 20251023_220049_E1_seed8 → win_rate=89%
- Artifacts root: `C:\Users\jmckerra\ObsidianNotes\Main\01 Projects\ARL RL\Experiment-Results\10-22-2025\run-6`
- HPC artifacts roots: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251023_*_E1_seed{4,6,8}`

## Next
- Stage E3 (PER) smoke: α≈0.6; β anneal 0.4→1.0; keep all other hyperparameters frozen.
