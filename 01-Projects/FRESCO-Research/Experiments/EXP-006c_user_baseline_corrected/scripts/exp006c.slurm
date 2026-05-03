#!/bin/bash
#SBATCH --job-name=EXP006c
#SBATCH --output=/home/jmckerra/Experiments/EXP-006c_user_baseline_corrected/logs/exp006c_%j.out
#SBATCH --error=/home/jmckerra/Experiments/EXP-006c_user_baseline_corrected/logs/exp006c_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=a30
#SBATCH --account=sbagchi
#SBATCH --qos=standby
#SBATCH --mail-user=jmckerra@purdue.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

EXP_DIR=/home/jmckerra/Experiments/EXP-006c_user_baseline_corrected
FRESCO_DIR=/depot/sbagchi/data/josh/FRESCO/chunks

mkdir -p "$EXP_DIR/logs" "$EXP_DIR/results"

VENV_DIR="${SLURM_TMPDIR:-/tmp}/exp006c_venv_${SLURM_JOB_ID:-manual}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip --quiet
pip install pandas pyarrow duckdb scikit-learn numpy xgboost --quiet

python "$EXP_DIR/scripts/exp006c.py" train \
  --input-dir "$FRESCO_DIR" \
  --out-dir "$EXP_DIR/results" \
  --threads 16

echo "EXP-006c complete"
