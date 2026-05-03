#!/bin/bash
#SBATCH --job-name=EXP002b_reanalyze
#SBATCH --output=/home/jmckerra/Experiments/EXP-002_isolation_forest/logs/exp002b_%j.out
#SBATCH --error=/home/jmckerra/Experiments/EXP-002_isolation_forest/logs/exp002b_%j.err
#==============================================================================
#                        RESOURCES
#==============================================================================
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#==============================================================================
#                PLACEMENT & POLICY (required on Gilbreth)
#==============================================================================
# NOTE: Before submitting, check which partition has least traffic:
#   sinfo -p a30,a100-40gb,a100-80gb,v100 -t idle -o "%12P %6D"
#   squeue -p a30,a100-40gb,a100-80gb,v100 --states=PENDING -o "%P" | tail -n +2 | sort | uniq -c | sort -n
# Then submit with: sbatch --partition=<best_partition> exp002b.slurm
#SBATCH --partition=a30
#SBATCH --account=sbagchi
#SBATCH --qos=standby
#SBATCH --mail-user=jmckerra@purdue.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

EXP_DIR=/home/jmckerra/Experiments/EXP-002_isolation_forest

# Create venv in scratch
VENV_DIR="${SLURM_TMPDIR:-/tmp}/exp002b_venv_${SLURM_JOB_ID:-manual}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip --quiet
python -m pip install pandas pyarrow scipy --quiet

cd "$EXP_DIR"

# Re-analyze with corrected exitcode parsing
python "$EXP_DIR/scripts/exp002b_reanalyze.py" \
  --results-dir "$EXP_DIR/results"

echo "EXP-002b re-analysis complete"
