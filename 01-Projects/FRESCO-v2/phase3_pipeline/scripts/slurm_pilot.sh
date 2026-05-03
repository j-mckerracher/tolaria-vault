#!/bin/bash
#SBATCH --job-name=fresco_v2_pilot
#SBATCH --output=logs/pilot_%j.out
#SBATCH --error=logs/pilot_%j.err
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1

# FRESCO v2.0 Pilot Run - Anvil August 2022
# Phase 4: Validation

echo "=========================================="
echo "FRESCO v2.0 Pilot Validation"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "Start time: $(date)"
echo "=========================================="

# Load environment
module load anaconda
source activate fresco_v2

# Set paths
PILOT_DIR=/depot/sbagchi/data/josh/FRESCO-Research/Experiments/phase4_validation
PIPELINE_DIR=${PILOT_DIR}/phase3_pipeline
SOURCE_PATH=/depot/sbagchi/www/fresco/repository/
OUTPUT_DIR=${PILOT_DIR}/pilot_output

# Create directories
mkdir -p ${PILOT_DIR}/logs
mkdir -p ${OUTPUT_DIR}

cd ${PIPELINE_DIR}

echo ""
echo "Environment:"
echo "  Python: $(python --version)"
echo "  Pandas: $(python -c 'import pandas; print(pandas.__version__)')"
echo "  PyArrow: $(python -c 'import pyarrow; print(pyarrow.__version__)')"
echo ""

# Run pilot extraction
echo "=========================================="
echo "Running pilot extraction..."
echo "=========================================="

python scripts/run_pilot.py \
  --month 2022-08 \
  --cluster anvil \
  --source ${SOURCE_PATH} \
  --output ${OUTPUT_DIR} \
  --clusters-json config/clusters.json

PILOT_EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Pilot extraction completed with exit code: ${PILOT_EXIT_CODE}"
echo "End time: $(date)"
echo "=========================================="

if [ ${PILOT_EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "SUCCESS: Pilot extraction completed successfully"
    echo ""
    echo "Output files:"
    ls -lh ${OUTPUT_DIR}/
    echo ""
    echo "Validation report:"
    cat ${OUTPUT_DIR}/validation_report_anvil_202208.json | python -m json.tool
else
    echo ""
    echo "ERROR: Pilot extraction failed with exit code ${PILOT_EXIT_CODE}"
    echo "Check logs at: ${PILOT_DIR}/logs/pilot_${SLURM_JOB_ID}.err"
    exit ${PILOT_EXIT_CODE}
fi

exit 0
