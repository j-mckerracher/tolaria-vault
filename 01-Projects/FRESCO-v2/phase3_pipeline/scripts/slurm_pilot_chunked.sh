#!/bin/bash
#SBATCH --job-name=fresco_v2_chunked
#SBATCH --output=logs/chunked_pilot_%j.out
#SBATCH --error=logs/chunked_pilot_%j.err
#SBATCH --time=00:30:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mckerracher@gmail.com

# FRESCO v2.0 Chunked Pilot
# Extracts August 2022 Anvil data and writes in hourly chunks

echo "================================"
echo "FRESCO v2.0 Chunked Pilot"
echo "================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo ""

# Activate conda environment
source ~/anaconda3/bin/activate fresco_v2

# Create output directory
mkdir -p /depot/sbagchi/data/josh/FRESCO/chunks-v2.0

# Run chunked pilot
python scripts/run_pilot_chunked.py \
    --cluster anvil \
    --year 2022 \
    --month 8 \
    --source-data-dir /depot/sbagchi/www/fresco/repository \
    --clusters-json config/clusters.json \
    --output-dir /depot/sbagchi/data/josh/FRESCO/chunks-v2.0

echo ""
echo "================================"
echo "Completed: $(date)"
echo "================================"
