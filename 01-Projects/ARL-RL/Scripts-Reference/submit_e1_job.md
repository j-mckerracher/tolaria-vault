script
```bash
#!/usr/bin/env bash

# submit_e1_job.sh — SLURM job submission wrapper for E1 training
# Provides easy parameter override and job submission with validation
#
# Usage:
#   bash scripts/submit_e1_job.sh [OPTIONS]
#
# Options:
#   --time HH:MM:SS     Set job wall time (default: 12:00:00)
#   --account NAME      REQUIRED: SLURM account (find yours with `slist`)
#   --partition NAME    GPU partition (default: a30)
#   --qos NAME          QoS policy (default: standby)
#   --ntasks N          Tasks (default: 1)
#   --gpus N            GPUs total (default: 1)
#   --cpus-per-task N   CPUs per task (default: 4)
#   --mem SIZE          Memory (default: 50G)
#   --res RES           Set resolution 32|64 (default: 32)
#   --seeds "S1 S2"     Set seeds (default: "4 6 8")
#   --episodes N        Set episodes per seed (default: 10000)
#   --dry-run           Show command without submitting
#   --help              Show this help

set -euo pipefail

# Default values
TIME="2:00:00"
PARTITION="a30"
QOS="standby"
ACCOUNT=""   # REQUIRED on Gilbreth; set with --account
NTASKS=1
GPUS=1
CPUS_PER_TASK=4
MEM="50G"
RES=32
SEEDS="4 6 8"
EPISODES=10000
DRY_RUN=0
SHOW_HELP=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --time)
            TIME="$2"; shift 2 ;;
        --account)
            ACCOUNT="$2"; shift 2 ;;
        --partition)
            PARTITION="$2"; shift 2 ;;
        --qos)
            QOS="$2"; shift 2 ;;
        --ntasks)
            NTASKS="$2"; shift 2 ;;
        --gpus)
            GPUS="$2"; shift 2 ;;
        --cpus-per-task)
            CPUS_PER_TASK="$2"; shift 2 ;;
        --mem)
            MEM="$2"; shift 2 ;;
        --res)
            RES="$2"; shift 2 ;;
        --seeds)
            SEEDS="$2"; shift 2 ;;
        --episodes)
            EPISODES="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN=1; shift ;;
        --help)
            SHOW_HELP=1; shift ;;
        *)
            echo "[ERROR] Unknown argument: $1" >&2
            echo "Use --help for usage information"
            exit 1 ;;
    esac
done

# Show help if requested
if [[ $SHOW_HELP -eq 1 ]]; then
    sed -n '3,20p' "$0" | sed 's/^# //'
    exit 0
fi

# Validation
if [[ -z "$ACCOUNT" ]]; then
    echo "[ERROR] --account is required on Gilbreth. Find yours with: slist" >&2
    exit 1
fi

if [[ ! "$RES" =~ ^(32|64)$ ]]; then
    echo "[ERROR] Resolution must be 32 or 64, got: $RES" >&2
    exit 1
fi

if [[ ! "$TIME" =~ ^[0-9]{1,2}:[0-9]{2}:[0-9]{2}$ ]]; then
    echo "[ERROR] Time must be in HH:MM:SS format, got: $TIME" >&2
    exit 1
fi

# Validate numeric resource fields
if [[ ! "$NTASKS" =~ ^[1-9][0-9]*$ ]]; then
    echo "[ERROR] ntasks must be a positive integer, got: $NTASKS" >&2
    exit 1
fi
if [[ ! "$GPUS" =~ ^[1-9][0-9]*$ ]]; then
    echo "[ERROR] gpus must be a positive integer, got: $GPUS" >&2
    exit 1
fi
if [[ ! "$CPUS_PER_TASK" =~ ^[1-9][0-9]*$ ]]; then
    echo "[ERROR] cpus-per-task must be a positive integer, got: $CPUS_PER_TASK" >&2
    exit 1
fi
# MEM can be values like 50G; skip strict numeric check

# Check if the job script exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
JOB_SCRIPT="$SCRIPT_DIR/run_e1.sh"

if [[ ! -f "$JOB_SCRIPT" ]]; then
    echo "[ERROR] Job script not found: $JOB_SCRIPT" >&2
    exit 1
fi


# Build the sbatch command
SBATCH_CMD="sbatch"
SBATCH_CMD+=" --job-name=E1_Training_${RES}x${RES}"
#SBATCH resources per Gilbreth guide
SBATCH_CMD+=" --time=$TIME"
SBATCH_CMD+=" --account=$ACCOUNT"
SBATCH_CMD+=" --partition=$PARTITION"
SBATCH_CMD+=" --qos=$QOS"
SBATCH_CMD+=" --ntasks=$NTASKS"
SBATCH_CMD+=" --gres=gpu:$GPUS"
SBATCH_CMD+=" --cpus-per-task=$CPUS_PER_TASK"
SBATCH_CMD+=" --mem=$MEM"
SBATCH_CMD+=" $JOB_SCRIPT"
SBATCH_CMD+=" --res $RES"
SBATCH_CMD+=" --seeds \"$SEEDS\""
SBATCH_CMD+=" --episodes $EPISODES"

# Show configuration
echo "====== SLURM Job Submission Configuration ======"
echo "Time limit:     $TIME"
echo "Account:        $ACCOUNT"
echo "Partition:      $PARTITION"
echo "QOS:            $QOS"
echo "ntasks:         $NTASKS"
echo "gpus:           $GPUS"
echo "cpus-per-task:  $CPUS_PER_TASK"
echo "mem:            $MEM"
echo "Resolution:     ${RES}x${RES}"
echo "Seeds:          $SEEDS"
echo "Episodes:       $EPISODES"
echo "Conda env:      /depot/sbagchi/data/preeti/anaconda3/envs/gpu (fixed)"
echo "Job script:     $JOB_SCRIPT"
echo "==============================================="
echo ""
echo "SBATCH command:"
echo "$SBATCH_CMD"
echo ""

# Execute or show dry run
if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY RUN] Job would be submitted with the above configuration"
    echo "To actually submit, remove the --dry-run flag"
else
    echo "Submitting job..."
    JOB_ID=$(eval "$SBATCH_CMD")
    if [[ $? -eq 0 ]]; then
        echo "✅ Job submitted successfully!"
        echo "$JOB_ID"
        echo ""
        echo "Monitor job status:"
        echo "  squeue -u \$USER"
        echo "  squeue -j \$(echo '$JOB_ID' | grep -o '[0-9]*')"
        echo ""
        echo "View job output (after completion):"
        echo "  cat e1_training_\$(echo '$JOB_ID' | grep -o '[0-9]*').out"
        echo "  cat e1_training_\$(echo '$JOB_ID' | grep -o '[0-9]*').err"
    else
        echo "❌ Job submission failed"
        exit 1
    fi
fi
```