#!/bin/bash
#SBATCH --job-name=EXP002_iforest
#SBATCH --output=/home/jmckerra/Experiments/EXP-002_isolation_forest/logs/exp002_%j.out
#SBATCH --error=/home/jmckerra/Experiments/EXP-002_isolation_forest/logs/exp002_%j.err
#==============================================================================
#                        RESOURCES
#==============================================================================
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#==============================================================================
#                PLACEMENT & POLICY (required on Gilbreth)
#==============================================================================
# NOTE: Before submitting, check which partition has least traffic:
#   sinfo -p a30,a100-40gb,a100-80gb,v100 -t idle -o "%12P %6D"
#   squeue -p a30,a100-40gb,a100-80gb,v100 --states=PENDING -o "%P" | tail -n +2 | sort | uniq -c | sort -n
# Then submit with: sbatch --partition=<best_partition> exp002.slurm
#SBATCH --partition=a30
#SBATCH --account=sbagchi
#SBATCH --qos=standby
#SBATCH --mail-user=jmckerra@purdue.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

EXP_DIR=/home/jmckerra/Experiments/EXP-002_isolation_forest
EXP001_DIR=/home/jmckerra/Experiments/EXP-001_baseline_statistical_analysis

mkdir -p "$EXP_DIR/logs" "$EXP_DIR/results" "$EXP_DIR/results/figures" "$EXP_DIR/results/models"

# Create venv in scratch
VENV_DIR="${SLURM_TMPDIR:-/tmp}/exp002_venv_${SLURM_JOB_ID:-manual}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip --quiet
python -m pip install -r "$EXP_DIR/scripts/requirements.txt" --quiet

cd "$EXP_DIR"

# Train Isolation Forest models
python "$EXP_DIR/scripts/exp002_isolation_forest.py" train \
  --input-dir "$EXP001_DIR/results/job_rollup" \
  --out-dir "$EXP_DIR/results" \
  --threads 16 \
  --n-estimators 100 \
  --max-samples 10000 \
  --contamination 0.01 \
  --seed 42

# Generate analysis figures
python "$EXP_DIR/scripts/exp002_isolation_forest.py" analyze \
  --out-dir "$EXP_DIR/results"

echo "EXP-002 complete"
