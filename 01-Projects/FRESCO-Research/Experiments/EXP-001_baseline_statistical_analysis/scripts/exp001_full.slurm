#!/bin/bash
#SBATCH --job-name=EXP001_baseline
#SBATCH --output=/depot/sbagchi/data/josh/FRESCO-Research/Experiments/EXP-001_baseline_statistical_analysis/logs/exp001_%j.out
#SBATCH --error=/depot/sbagchi/data/josh/FRESCO-Research/Experiments/EXP-001_baseline_statistical_analysis/logs/exp001_%j.err
#==============================================================================
#                        RESOURCES
#==============================================================================
# NOTE: Gilbreth is GPU-only; must request >=1 GPU even for CPU-heavy jobs.
#       Using a30 partition (190GB RAM, 24GB GPU) with minimal GPU for headroom.
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#==============================================================================
#                PLACEMENT & POLICY (required on Gilbreth)
#==============================================================================
# NOTE: Before submitting, check which partition has least traffic:
#   sinfo -p a30,a100-40gb,a100-80gb,v100 -t idle -o "%12P %6D"
#   squeue -p a30,a100-40gb,a100-80gb,v100 --states=PENDING -o "%P" | tail -n +2 | sort | uniq -c | sort -n
# Then submit with: sbatch --partition=<best_partition> exp001_full.slurm
#SBATCH --partition=a30
#SBATCH --account=sbagchi
#SBATCH --qos=normal
#SBATCH --mail-user=jmckerra@purdue.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

# Adjust as needed for your environment
# module load python

EXP_DIR=/depot/sbagchi/data/josh/FRESCO-Research/Experiments/EXP-001_baseline_statistical_analysis
mkdir -p "$EXP_DIR/logs" "$EXP_DIR/results" "$EXP_DIR/results/figures" "$EXP_DIR/results/tmp"

# Create a venv inside node-local scratch for speed, but keep all EXP-001 outputs under $EXP_DIR
VENV_DIR="${SLURM_TMPDIR:-/tmp}/exp001_venv_${SLURM_JOB_ID:-manual}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$EXP_DIR/scripts/requirements.txt"

# Ensure we run from EXP_DIR so any relative paths resolve under /depot/.../EXP-001...
cd "$EXP_DIR"

# Stage 1 can be sharded across a job array by setting RANK/STRIDE.
RANK=${RANK:-0}
STRIDE=${STRIDE:-1}

python "$EXP_DIR/scripts/exp001_baseline.py" stage1 \
  --input-root /depot/sbagchi/data/josh/FRESCO/chunks \
  --tmp-root "$EXP_DIR/results/tmp" \
  --out-root "$EXP_DIR/results" \
  --rank "$RANK" \
  --stride "$STRIDE" \
  --verbose-every 5000

# Reduce to per-job rollup + monthly summary (DuckDB)
python "$EXP_DIR/scripts/exp001_baseline.py" stage2 \
  --tmp-root "$EXP_DIR/results/tmp" \
  --out-root "$EXP_DIR/results" \
  --threads 16

python "$EXP_DIR/scripts/exp001_baseline.py" stage3 \
  --tmp-root "$EXP_DIR/results/tmp" \
  --out-root "$EXP_DIR/results" \
  --threads 16

# Optional plotting
python "$EXP_DIR/scripts/plot_monthly.py" \
  --monthly-csv "$EXP_DIR/results/monthly_summary.csv" \
  --figdir "$EXP_DIR/results/figures"
