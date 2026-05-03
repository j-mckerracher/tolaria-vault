#!/bin/bash
#SBATCH --job-name=verify_v3
#SBATCH --output=logs/verify_v3_%j.out
#SBATCH --error=logs/verify_v3_%j.err
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --partition=a100-80gb
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mckerracher@gmail.com

echo "========================================"
echo "FRESCO v3 Output Verification"
echo "========================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo ""

cd /home/jmckerra/Code/FRESCO-Pipeline

# Activate conda environment
source ~/anaconda3/bin/activate fresco_v2

# Run verification
python verify_v3_output.py

exit_code=$?

echo ""
echo "========================================"
echo "Completed: $(date)"
echo "Exit code: $exit_code"
echo "========================================"

exit $exit_code
