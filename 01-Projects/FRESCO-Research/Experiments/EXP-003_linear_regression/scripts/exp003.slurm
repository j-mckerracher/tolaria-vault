#!/bin/bash
#SBATCH --job-name=EXP003_linreg
#SBATCH --output=/home/jmckerra/Experiments/EXP-003_linear_regression/logs/exp003_%j.out
#SBATCH --error=/home/jmckerra/Experiments/EXP-003_linear_regression/logs/exp003_%j.err
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
# NOTE: Before submitting, auto-select best partition:
#   source ~/setup_slurm_aliases.sh  # if not already in .bashrc
#   sbbest scripts/exp003.slurm
# Or manually:
#   PART=$(best_partition); sbatch --partition=$PART scripts/exp003.slurm
#SBATCH --partition=a30
#SBATCH --account=sbagchi
#SBATCH --qos=standby
#SBATCH --mail-user=jmckerra@purdue.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

EXP_DIR=/home/jmckerra/Experiments/EXP-003_linear_regression
FRESCO_DIR=/depot/sbagchi/data/josh/FRESCO/chunks

mkdir -p "$EXP_DIR/logs" "$EXP_DIR/results" "$EXP_DIR/results/figures" "$EXP_DIR/results/models"

# Create venv in scratch
VENV_DIR="${SLURM_TMPDIR:-/tmp}/exp003_venv_${SLURM_JOB_ID:-manual}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip --quiet
python -m pip install -r "$EXP_DIR/scripts/requirements.txt" --quiet

cd "$EXP_DIR"

# Train linear regression models from raw FRESCO data
python "$EXP_DIR/scripts/exp003_linear_regression.py" train \
  --input-dir "$FRESCO_DIR" \
  --out-dir "$EXP_DIR/results" \
  --threads 16 \
  --alpha 1.0 \
  --from-raw

echo "EXP-003 complete"
