#!/bin/bash
# submit_job.sh - Submits job to supercomputer and logs details
# Usage: ./submit_job.sh EXP-XXX script.sh [slurm|pbs]

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Paths
EXPERIMENTS_DIR="$PROJECT_ROOT/Experiments"

# Arguments
EXP_ID="$1"
SCRIPT_NAME="$2"
SCHEDULER="${3:-slurm}"  # Default to SLURM

if [ -z "$EXP_ID" ] || [ -z "$SCRIPT_NAME" ]; then
    echo "Usage: $0 EXP-XXX script.sh [slurm|pbs]"
    echo ""
    echo "Arguments:"
    echo "  EXP-XXX     Experiment ID"
    echo "  script.sh   Job script filename (relative to experiment directory)"
    echo "  scheduler   'slurm' (default) or 'pbs'"
    echo ""
    echo "Example:"
    echo "  $0 EXP-001 job.slurm slurm"
    echo "  $0 EXP-002 job.pbs pbs"
    exit 1
fi

# Validate scheduler
if [ "$SCHEDULER" != "slurm" ] && [ "$SCHEDULER" != "pbs" ]; then
    echo "Error: Invalid scheduler '$SCHEDULER'. Use 'slurm' or 'pbs'."
    exit 1
fi

NOW=$(date +"%Y-%m-%d %H:%M:%S")
TODAY=$(date +%Y-%m-%d)

# Find experiment directory
EXP_DIR=""
for dir in "$EXPERIMENTS_DIR"/${EXP_ID}*/; do
    if [ -d "$dir" ]; then
        EXP_DIR="$dir"
        break
    fi
done

if [ -z "$EXP_DIR" ] || [ ! -d "$EXP_DIR" ]; then
    echo "Error: Experiment $EXP_ID not found in $EXPERIMENTS_DIR"
    exit 1
fi

# Find job script
SCRIPT_PATH=""
if [ -f "${EXP_DIR}${SCRIPT_NAME}" ]; then
    SCRIPT_PATH="${EXP_DIR}${SCRIPT_NAME}"
elif [ -f "${EXP_DIR}scripts/${SCRIPT_NAME}" ]; then
    SCRIPT_PATH="${EXP_DIR}scripts/${SCRIPT_NAME}"
else
    echo "Error: Script '$SCRIPT_NAME' not found in $EXP_DIR or ${EXP_DIR}scripts/"
    exit 1
fi

README_PATH="${EXP_DIR}README.md"

echo "Submitting job for $EXP_ID"
echo "  Script: $SCRIPT_PATH"
echo "  Scheduler: $SCHEDULER"
echo ""

# Submit job based on scheduler
JOB_ID=""
CLUSTER=""

if [ "$SCHEDULER" = "slurm" ]; then
    # Prefer sbbest on Gilbreth (partition auto-selection), fallback to sbatch.
    if command -v sbbest &> /dev/null; then
        OUTPUT=$(sbbest "$SCRIPT_PATH" 2>&1)
        JOB_ID=$(echo "$OUTPUT" | grep -oP 'Submitted batch job \K\d+' || echo "")
    elif command -v sbatch &> /dev/null; then
        OUTPUT=$(sbatch "$SCRIPT_PATH" 2>&1)
        JOB_ID=$(echo "$OUTPUT" | grep -oP 'Submitted batch job \K\d+' || echo "")
        
        if [ -z "$JOB_ID" ]; then
            echo "Warning: Could not parse job ID from sbatch output:"
            echo "$OUTPUT"
            JOB_ID="UNKNOWN"
        fi
        
        # Try to get cluster name
        CLUSTER=$(scontrol show config 2>/dev/null | grep ClusterName | awk '{print $3}' || echo "Unknown")
    else
        echo "Warning: sbbest/sbatch not found. Simulating submission."
        JOB_ID="SIMULATED-$(date +%s)"
        CLUSTER="SIMULATION"
    fi
elif [ "$SCHEDULER" = "pbs" ]; then
    # Check if qsub is available
    if command -v qsub &> /dev/null; then
        # Submit and capture job ID
        JOB_ID=$(qsub "$SCRIPT_PATH" 2>&1)
        CLUSTER=$(hostname | cut -d'.' -f2 || echo "Unknown")
    else
        echo "Warning: qsub not found. Simulating submission."
        JOB_ID="SIMULATED-$(date +%s)"
        CLUSTER="SIMULATION"
    fi
fi

echo "✓ Job submitted"
echo "  Job ID: $JOB_ID"
echo "  Cluster: $CLUSTER"

# Update README with job details
if [ -f "$README_PATH" ]; then
    # Update Supercomputer Job section
    sed -i "s/| Job ID | .*/| Job ID | $JOB_ID |/" "$README_PATH"
    sed -i "s/| Cluster | .*/| Cluster | $CLUSTER |/" "$README_PATH"
    sed -i "s/| Scheduler | .*/| Scheduler | ${SCHEDULER^^} |/" "$README_PATH"
    sed -i "s/| Submitted | .*/| Submitted | $NOW |/" "$README_PATH"
    
    # Update status
    sed -i "s/^\*\*Status\*\*: .*/\*\*Status\*\*: Queued/" "$README_PATH"
    sed -i "s/^\*\*Last Updated\*\*: .*/\*\*Last Updated\*\*: $TODAY/" "$README_PATH"
    
    echo "✓ Updated README.md"
fi

# Update Master Index
INDEX_PATH="$PROJECT_ROOT/Documentation/Master_Index.md"
if [ -f "$INDEX_PATH" ]; then
    sed -i "s/^\(| $EXP_ID |[^|]*|\)[^|]*\(|[^|]*|[^|]*|\)[^|]*|/\1 Queued \2 $TODAY |/" "$INDEX_PATH"
    echo "✓ Updated Master Index"
fi

# Log submission
echo ""
echo "Job Details:"
echo "  Experiment: $EXP_ID"
echo "  Job ID: $JOB_ID"
echo "  Cluster: $CLUSTER"
echo "  Scheduler: $SCHEDULER"
echo "  Submitted: $NOW"
echo ""
echo "Next steps:"
echo "  - Monitor job: squeue -j $JOB_ID  (SLURM) or qstat $JOB_ID (PBS)"
echo "  - When complete, update status: ./update_status.sh $EXP_ID Completed"
