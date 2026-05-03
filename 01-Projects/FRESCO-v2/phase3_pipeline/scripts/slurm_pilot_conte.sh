#!/bin/bash
#SBATCH --job-name=fresco_v2_conte
#SBATCH --output=logs/conte_pilot_%j.out
#SBATCH --error=logs/conte_pilot_%j.err
#SBATCH --time=00:30:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mckerracher@gmail.com

# FRESCO v2.0 Conte Pilot
# Extracts March 2015 Conte data and writes in hourly chunks

echo "================================"
echo "FRESCO v2.0 Conte Pilot"
echo "================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo ""

# Activate conda environment
source ~/anaconda3/bin/activate fresco_v2

# Run Conte pilot
python scripts/run_pilot_conte.py

echo ""
echo "================================"
echo "Completed: $(date)"
echo "================================"
