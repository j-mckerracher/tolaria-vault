#!/bin/bash
#SBATCH --job-name=EXP001_stage2_3
#SBATCH --output=/home/jmckerra/Experiments/EXP-001_baseline_statistical_analysis/logs/exp001_s23_%j.out
#SBATCH --error=/home/jmckerra/Experiments/EXP-001_baseline_statistical_analysis/logs/exp001_s23_%j.err
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
#SBATCH --partition=a100-80gb
#SBATCH --account=sbagchi
#SBATCH --qos=standby
#SBATCH --mail-user=jmckerra@purdue.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

EXP_DIR=/home/jmckerra/Experiments/EXP-001_baseline_statistical_analysis
mkdir -p "$EXP_DIR/logs" "$EXP_DIR/results"

# Create venv in scratch
VENV_DIR="${SLURM_TMPDIR:-/tmp}/exp001_venv_${SLURM_JOB_ID:-manual}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip --quiet
python -m pip install -r "$EXP_DIR/scripts/requirements.txt" --quiet

cd "$EXP_DIR"

# Stage 2: Reduce partials to per-job rollup
python "$EXP_DIR/scripts/exp001_baseline.py" stage2 \
  --tmp-root "$EXP_DIR/results/tmp" \
  --out-root "$EXP_DIR/results" \
  --threads 16

# Stage 3: Monthly summary
python "$EXP_DIR/scripts/exp001_baseline.py" stage3 \
  --tmp-root "$EXP_DIR/results/tmp" \
  --out-root "$EXP_DIR/results" \
  --threads 16

# Optional plotting
python "$EXP_DIR/scripts/plot_monthly.py" \
  --monthly-csv "$EXP_DIR/results/monthly_summary.csv" \
  --figdir "$EXP_DIR/results/figures"

echo "EXP-001 stage2+3 complete"
