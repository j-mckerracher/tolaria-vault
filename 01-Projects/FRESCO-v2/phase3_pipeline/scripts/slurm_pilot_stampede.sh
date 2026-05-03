#!/bin/bash
#SBATCH --job-name=fresco_v2_stampede
#SBATCH --output=logs/stampede_pilot_%j.out
#SBATCH --error=logs/stampede_pilot_%j.err
#SBATCH --time=04:00:00
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mckerracher@gmail.com

# FRESCO v2.0 Stampede Pilot
# Extracts 2015-03 for cross-cluster validation with Conte
# NOTE: Stampede has 6,172 node directories - may take longer than other pilots

echo "=============================================="
echo "FRESCO v2.0 Stampede Pilot"
echo "=============================================="
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo "=============================================="

# Activate conda environment
source ~/anaconda3/bin/activate fresco_v2

# Navigate to pipeline directory
cd /depot/sbagchi/data/josh/FRESCO-Research/Experiments/phase4_validation/phase3_pipeline

# Ensure logs directory exists
mkdir -p logs

# Run pilot
python scripts/run_pilot_stampede.py

echo ""
echo "=============================================="
echo "Completed: $(date)"
echo "=============================================="
