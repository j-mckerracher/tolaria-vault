---
project: ARL RL
tags: [project/arl-rl, decision]
created: 2025-10-05
---

# Decision — Target Update Frequency after Sweep C

## Context
Target update frequency sweep (higher is better):
```
- 200  → win_rate 53.0%, avg_reward 1.47
- 100  → win_rate  9.0%, avg_reward 0.17
- 50   → win_rate  2.0%, avg_reward 0.03
```
Source CSV: C:\\Users\\jmckerra\\Downloads\\sweep_results_tuf.csv
Artifacts per-run under: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/
Note: CSV lists LR=0.0001, EPS_DECAY=50000 for these runs. Our chosen values are LR=0.00005 and EPS_DECAY=20000 from previous decisions. We will validate with those settings in Phase 2.

## Decision
Proceed with TARGET_UPDATE_FREQ = 200.

## Next actions (Phase 2 — Confirm and extend)
Run confirmatory longer trainings (3000 episodes) with two seeds (4, 6) using:
- LR=0.00005
- EPS_DECAY=20000
- TARGET_UPDATE_FREQ=200
- Batch size 8, replay size 50k, resolution 32×32

Commands (run on Gilbreth):
```bash
export RL_SAVE_PATH="/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced"
export RL_LOG_DIR="/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/logs"
export SC2PATH="/home/jmckerra/StarCraftII"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

export RL_NUM_EPISODES=3000
export RL_BATCH_SIZE=8
export RL_SCREEN_RES=32
export RL_MINIMAP_RES=32
export RL_REPLAY_MEMORY_SIZE=50000
export RL_EPS_START=0.90
export RL_EPS_END=0.05
export RL_LEARNING_RATE=0.00005
export RL_EPS_DECAY=20000
export RL_TARGET_UPDATE_FREQ=200
export RL_STEP_MUL=8

# Seed 4
export RL_SEED=4
export RL_RUN_ID=$(date -u +%Y%m%d_%H%M%S)_confirm_tuf200_seed4
python -u training_split.py

# Seed 6
export RL_SEED=6
export RL_RUN_ID=$(date -u +%Y%m%d_%H%M%S)_confirm_tuf200_seed6
python -u training_split.py
```

## After confirmation
- Evaluate both runs (100-episode tests are automatic at the end) and compare mean win rate.
- If stable (>20% and consistent), proceed to optional Phase 3 (resolution bump to 64×64) if GPU headroom allows.
