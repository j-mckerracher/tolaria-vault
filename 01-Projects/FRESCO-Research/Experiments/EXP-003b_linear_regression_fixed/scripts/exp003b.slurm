#!/bin/bash
#SBATCH --job-name=EXP003b_linreg
#SBATCH --output=/home/jmckerra/Experiments/EXP-003b_linear_regression_fixed/logs/exp003b_%j.out
#SBATCH --error=/home/jmckerra/Experiments/EXP-003b_linear_regression_fixed/logs/exp003b_%j.err
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
# Submit with: sbbest scripts/exp003b.slurm
#SBATCH --partition=a30
#SBATCH --account=sbagchi
#SBATCH --qos=standby
#SBATCH --mail-user=jmckerra@purdue.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

EXP_DIR=/home/jmckerra/Experiments/EXP-003b_linear_regression_fixed
FRESCO_DIR=/depot/sbagchi/data/josh/FRESCO/chunks

mkdir -p "$EXP_DIR/logs" "$EXP_DIR/results" "$EXP_DIR/results/figures" "$EXP_DIR/results/models"

# Create venv in scratch
VENV_DIR="${SLURM_TMPDIR:-/tmp}/exp003b_venv_${SLURM_JOB_ID:-manual}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip --quiet
python -m pip install -r "$EXP_DIR/scripts/requirements.txt" --quiet

cd "$EXP_DIR"

# Train linear regression models with ablation studies
python "$EXP_DIR/scripts/exp003b_linear_regression.py" train \
  --input-dir "$FRESCO_DIR" \
  --out-dir "$EXP_DIR/results" \
  --threads 16 \
  --alpha 1.0

echo "EXP-003b complete"
