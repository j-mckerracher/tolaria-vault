#!/bin/bash
#SBATCH --job-name=fresco_v3_production
#SBATCH --output=logs/production_v3_%j.out
#SBATCH --error=logs/production_v3_%j.err
#SBATCH --time=12:00:00
#SBATCH --mem=128G
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --partition=a100-80gb
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mckerracher@gmail.com

# FRESCO v3 Production Data Build
# Processes raw FRESCO shards -> chunks-v3/ and finalizes manifests/validation

echo "========================================"
echo "FRESCO v3 PRODUCTION DATA BUILD"
echo "========================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo ""

RUN_STARTED_AT="$(date --iso-8601=seconds)"

# Change to project directory
cd /home/jmckerra/Code/FRESCO-Pipeline

# Create directories
mkdir -p logs
mkdir -p /depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests
mkdir -p /depot/sbagchi/data/josh/FRESCO/chunks-v3/validation
mkdir -p /depot/sbagchi/data/josh/FRESCO/chunks-v3/logs

# Activate conda environment
source ~/anaconda3/bin/activate fresco_v2

# Verify environment
echo "Python version: $(python --version)"
echo "Conda env: $CONDA_DEFAULT_ENV"
echo ""

PIPELINE_GIT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"

# Run production build
python scripts/build_production_v3.py --config config/production_v3.json
build_exit_code=$?

if [ "$build_exit_code" -eq 0 ]; then
  python scripts/finalize_production_v3.py \
    --config config/production_v3.json \
    --output-root /depot/sbagchi/data/josh/FRESCO/chunks-v3 \
    --slurm-job-id "$SLURM_JOB_ID" \
    --started-at "$RUN_STARTED_AT" \
    --completed-at "$(date --iso-8601=seconds)" \
    --pipeline-git-commit "$PIPELINE_GIT_COMMIT"
  exit_code=$?
else
  exit_code=$build_exit_code
fi

echo ""
echo "========================================"
echo "Completed: $(date)"
echo "Exit code: $exit_code"
echo "========================================"

exit $exit_code
