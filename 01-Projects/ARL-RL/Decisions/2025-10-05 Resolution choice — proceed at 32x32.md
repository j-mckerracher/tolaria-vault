---
project: ARL RL
tags: [project/arl-rl, decision]
created: 2025-10-05
---

# Decision — Resolution choice: Proceed at 32×32

## Context
- Attempts to run 64×64 confirmation are blocked by GPU memory headroom on the shared A30 node.
- Confirm runs at 32×32 using the best parameters (LR=0.00005, EPS_DECAY=20000, TUF=200) achieved:
  - Seed 4 → 37.0%
  - Seed 6 → 29.0%
  - Mean ≈ 33.0%
- These exceed the original ~20% baseline and are stable across seeds.

## Decision
Proceed at 32×32 resolution for Phase 2 confirmation and Part 2 validation.

## Next actions
- Optional: Add a third 32×32 confirm run (seed 8) to further validate stability.
  - Example (bash):
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
    export RL_SEED=8
    export RL_RUN_ID=$(date -u +%Y%m%d_%H%M%S)_confirm_best_seed8
    python -u training_split.py
    ```
- Proceed to Part 2 (NO_OP fix validation) with short 32×32 runs; log observations and metrics.
- Update Status and Experiments after each run.
