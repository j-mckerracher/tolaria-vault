script
```bash
#!/usr/bin/env bash

#==============================================================================
#                        SLURM SBATCH DIRECTIVES
#==============================================================================
#
#SBATCH --job-name=E1_Training
#SBATCH --output=e1_training_%j.out
#SBATCH --error=e1_training_%j.err
# Resources (override at submit-time as needed)
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=50G
# Partition and QoS (override at submit-time if needed)
#SBATCH --partition=a30
#SBATCH --qos=standby
# IMPORTANT: Gilbreth requires a valid account. Do NOT hardcode here.
# Pass your account at submit time, e.g. via: sbatch --account=<your_account> scripts/run_e1.sh
#SBATCH --time=12:00:00

#==============================================================================
#                        JOB COMMANDS
#==============================================================================

set -euo pipefail

# run_e1.sh — Stage E1 automation (Double DQN + LR scheduler) for seeds 4,6,8
# Runs long trainings sequentially and appends results to e1_results.csv
# Usage:
#   sbatch scripts/run_e1.sh [--res 32|64] [--seeds "4 6 8"] [--episodes 10000]
# 
# SLURM Job Submission:
#   sbatch scripts/run_e1.sh
#   sbatch --time=08:00:00 --account=priority scripts/run_e1.sh

# Print SLURM job information
echo "====== SLURM Job Information ======"
echo "Job ID: $SLURM_JOBID"
echo "Running on nodes: $SLURM_JOB_NODELIST"
echo "Submitted from: $SLURM_SUBMIT_HOST"
echo "Submit directory: $SLURM_SUBMIT_DIR"
echo "====================================="

# Change to the submission directory
cd $SLURM_SUBMIT_DIR

# Load necessary modules
echo "[INFO] Initializing conda (no module load)..."
CONDA_ROOT=/depot/sbagchi/data/preeti/anaconda3
if [[ -f "$CONDA_ROOT/etc/profile.d/conda.sh" ]]; then
  source "$CONDA_ROOT/etc/profile.d/conda.sh"
else
  eval "$("$CONDA_ROOT/bin/conda" shell.bash hook)"
fi

echo "[INFO] Activating conda environment: /depot/sbagchi/data/preeti/anaconda3/envs/gpu"
conda activate /depot/sbagchi/data/preeti/anaconda3/envs/gpu

# Verify environment activation
echo "[INFO] Python path: $(which python)"
echo "[INFO] Python version: $(python --version)"
echo "[INFO] PyTorch available: $(python -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'Not available')"
echo "[INFO] CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null || echo 'Cannot check')"
if python -c 'import torch' 2>/dev/null && python -c 'import torch; torch.cuda.is_available()' 2>/dev/null; then
    echo "[INFO] GPU devices: $(python -c 'import torch; print(torch.cuda.device_count())')"
fi

# --- Defaults (overridable via flags) ---
: "${RL_SAVE_PATH:=/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced}"
: "${RL_LOG_DIR:=/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/logs}"
: "${SC2PATH:=/home/jmckerra/StarCraftII}"
: "${PYTORCH_CUDA_ALLOC_CONF:=expandable_segments:True,garbage_collection_threshold:0.7,max_split_size_mb:128}"

RES=32
SEEDS=(4 6 8)
EPISODES=10000

ALLOW_ENV=0
# --- Parse flags ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --res)
      RES="$2"; shift 2 ;;
    --seeds)
      IFS=' ' read -r -a SEEDS <<< "$2"; shift 2 ;;
    --episodes)
      EPISODES="$2"; shift 2 ;;
    --allow-env)
      ALLOW_ENV=1; shift ;;
    *)
      echo "[ERR] Unknown argument: $1" >&2; exit 1 ;;
  esac
done

export RL_SAVE_PATH RL_LOG_DIR SC2PATH PYTORCH_CUDA_ALLOC_CONF

# --- Pre-flight checks ---
echo "[INFO] Performing pre-flight checks..."

# Check if required directories exist
if [[ ! -d "$RL_SAVE_PATH" ]]; then
    echo "[ERROR] RL_SAVE_PATH directory not found: $RL_SAVE_PATH"
    echo "[INFO] Creating directory: $RL_SAVE_PATH"
    mkdir -p "$RL_SAVE_PATH" || { echo "[ERROR] Failed to create $RL_SAVE_PATH"; exit 1; }
fi

if [[ ! -d "$RL_LOG_DIR" ]]; then
    echo "[INFO] Creating log directory: $RL_LOG_DIR"
    mkdir -p "$RL_LOG_DIR" || { echo "[ERROR] Failed to create $RL_LOG_DIR"; exit 1; }
fi

# Check if StarCraft II path exists
if [[ ! -d "$SC2PATH" ]]; then
    echo "[ERROR] StarCraft II path not found: $SC2PATH"
    echo "[ERROR] Please ensure StarCraft II is installed and SC2PATH is correct"
    exit 1
fi

# Check if training script exists
if [[ ! -f "training_split.py" ]]; then
    echo "[ERROR] training_split.py not found in current directory"
    echo "[INFO] Current directory: $(pwd)"
    echo "[INFO] Available files: $(ls -la)"
    exit 1
fi

# Check GPU availability
if command -v nvidia-smi &> /dev/null; then
    echo "[INFO] GPU Status:"
    nvidia-smi --query-gpu=index,name,memory.free,memory.total --format=csv,noheader,nounits
else
    echo "[WARNING] nvidia-smi not available - cannot check GPU status"
fi

echo "[INFO] Pre-flight checks completed successfully"

# --- Cleanup handler ---
cleanup() {
    local exit_code=$?
    echo "[INFO] Job cleanup triggered (exit code: $exit_code)"
    if [[ $exit_code -ne 0 ]]; then
        echo "[ERROR] Job failed with exit code: $exit_code"
        echo "[INFO] Job ID: $SLURM_JOBID"
        echo "[INFO] Node: $SLURM_JOB_NODELIST"
        echo "[INFO] Working directory: $(pwd)"
        if command -v nvidia-smi &> /dev/null; then
            echo "[INFO] Final GPU status:"
            nvidia-smi --query-gpu=index,name,memory.free,memory.used --format=csv,noheader,nounits
        fi
    fi
}
trap cleanup EXIT

# --- E1 training parameters (with optional env override) ---
if [[ "$ALLOW_ENV" -eq 1 ]]; then
  : "${RL_NUM_EPISODES:=$EPISODES}"
  : "${RL_BATCH_SIZE:=4}"  # Reduced from 8 for memory safety on contended GPUs
  : "${RL_SCREEN_RES:=$RES}"
  : "${RL_MINIMAP_RES:=$RES}"
  : "${RL_REPLAY_MEMORY_SIZE:=100000}"
  : "${RL_EPS_START:=0.90}"
  : "${RL_EPS_END:=0.01}"
  : "${RL_EPS_DECAY:=100000}"
  : "${RL_LEARNING_RATE:=0.00005}"
  : "${RL_TARGET_UPDATE_FREQ:=300}"
  : "${RL_STEP_MUL:=16}"
else
  export RL_NUM_EPISODES="$EPISODES"
  export RL_BATCH_SIZE=4  # Reduced from 8 for memory safety on contended GPUs
  export RL_SCREEN_RES="$RES"
  export RL_MINIMAP_RES="$RES"
  export RL_REPLAY_MEMORY_SIZE=100000
  export RL_EPS_START=0.90
  export RL_EPS_END=0.01
  export RL_EPS_DECAY=100000
  export RL_LEARNING_RATE=0.00005
  export RL_TARGET_UPDATE_FREQ=300
  export RL_STEP_MUL=16
fi

# Stage E1 flags are defaults in code (USE_DOUBLE_DQN=True, LR_SCHEDULER=cosine)
# We log the effective configuration below as a sanity check.
echo "[CFG] E1 run: RES=$RES EPISODES=$EPISODES BATCH=${RL_BATCH_SIZE} REPLAY=100k LR=5e-5 EPS=(0.9→0.01 @100k) TUF=300 STEP_MUL=16"

echo "[INFO] Seeds: ${SEEDS[*]}"

CSV="$RL_SAVE_PATH/e1_results.csv"
if [[ ! -f "$CSV" ]]; then
  echo "timestamp_utc,run_id,seed,lr,eps_decay,target_update,win_rate,avg_reward,artifacts_path" > "$CSV"
fi

for seed in "${SEEDS[@]}"; do
  export RL_SEED="$seed"
  export RL_RUN_ID="$(date -u +%Y%m%d_%H%M%S)_E1_seed${seed}"
  run_dir="$RL_SAVE_PATH/$RL_RUN_ID"
  mkdir -p "$run_dir"

  echo "[INFO] Starting E1 seed=$seed -> $RL_RUN_ID (RES=$RES)"
  python -u training_split.py 2>&1 | tee "$run_dir/train.log"

  # Append results
  python - "$CSV" "$RL_RUN_ID" "$seed" "$run_dir" <<'PY'
import json, os, sys, datetime
csv_path, run_id, seed, run_dir = sys.argv[1:]
res_path = os.path.join(run_dir, 'eval', 'test_results.json')
cfg_path = os.path.join(run_dir, 'config.json')
now = datetime.datetime.utcnow().isoformat() + 'Z'
win_rate = avg_reward = lr = eps_decay = tuf = ''
try:
    with open(res_path) as f:
        data = json.load(f)
    win_rate = data.get('win_rate', '')
    avg_reward = data.get('avg_reward', '')
except Exception:
    pass
try:
    with open(cfg_path) as f:
        cfg = json.load(f)
    env = cfg.get('env', {})
    lr = env.get('RL_LEARNING_RATE', '')
    eps_decay = env.get('RL_EPS_DECAY', '')
    tuf = env.get('RL_TARGET_UPDATE_FREQ', '')
except Exception:
    pass
with open(csv_path, 'a') as f:
    f.write(f"{now},{run_id},{seed},{lr},{eps_decay},{tuf},{win_rate},{avg_reward},{run_dir}\n")
print(f"[OK] Appended results for {run_id}")
PY

echo "[INFO] Completed $RL_RUN_ID";

done

echo "[DONE] Wrote results to $CSV"

# --- Job completion summary ---
echo ""
echo "====== JOB COMPLETION SUMMARY ======"
echo "Job ID: $SLURM_JOBID"
echo "Completion time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Seeds processed: ${SEEDS[*]}"
echo "Episodes per seed: $EPISODES"
echo "Resolution: ${RES}x${RES}"
echo "Results CSV: $CSV"
if [[ -f "$CSV" ]]; then
    echo "CSV entries: $(tail -n +2 "$CSV" | wc -l)"
    echo "Latest results:"
    tail -n 3 "$CSV" | column -t -s ','
else
    echo "[WARNING] Results CSV not found: $CSV"
fi
echo "====================================="
echo "Job completed successfully!"
echo "Check SLURM output files:"
echo "  - Standard output: e1_training_${SLURM_JOBID}.out"
echo "  - Standard error:  e1_training_${SLURM_JOBID}.err"

```