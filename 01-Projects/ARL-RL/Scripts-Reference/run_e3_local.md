script
```bash
#!/usr/bin/env bash

# This script runs a local training session for the ARL-RL project (Stage E3 PER Smoke Test).
# It sets the necessary environment variables and then executes the training script.
#
# Usage:
#   bash scripts/run_e3_local.sh
#
# You can customize the parameters by editing the variables in this script.

set -euo pipefail

# --- Paths ---
# IMPORTANT: Adjust these paths if your setup on the HPC is different.
export RL_SAVE_PATH="/home/jmckerra/PycharmProjects/ARL-RL/results"
export RL_LOG_DIR="/home/jmckerra/PycharmProjects/ARL-RL/logs"
export SC2PATH="/home/jmckerra/StarCraftII"

# --- E3 Experiment Parameters (from sbatch command) ---
export RL_NUM_EPISODES=500
export RL_LEARNING_RATE=0.00005
export RL_EPS_DECAY=100000
export RL_BATCH_SIZE=4
export RL_REPLAY_MEMORY_SIZE=100000
export RL_SCREEN_RESOLUTION=32
export RL_MINIMAP_RESOLUTION=32 # Assuming same as SCREEN_RESOLUTION
export RL_STEP_MUL=16
export RL_TARGET_UPDATE_FREQ=400
export RL_DUELING_DQN=1
export RL_PER_ENABLED=1
export RL_PER_ALPHA=0.6
export RL_PER_BETA_START=0.4
export RL_PER_BETA_END=1.0

# --- Loop through seeds and run training for each ---
for seed in 4 6 8; do
  export RL_SEED=$seed
  export RL_RUN_ID="$(date -u +%Y%m%d_%H%M%S)_E3_smoke_seed_${seed}"
  
  echo "--- Starting E3 Smoke Test for Seed $RL_SEED ---"
  echo "Run ID: $RL_RUN_ID"
  
  # Create run directory for logs and config
  mkdir -p "$RL_SAVE_PATH/$RL_RUN_ID"

  # Run the training script
  python training_split.py 2>&1 | tee "$RL_SAVE_PATH/$RL_RUN_ID/train.log"
  
  echo "--- Completed Seed $RL_SEED ---"
done

echo "All E3 smoke test runs completed."
```
