#!/bin/bash
# setup_slurm_aliases.sh - Install SLURM convenience aliases to ~/.bashrc
# Run once on Gilbreth: bash setup_slurm_aliases.sh

cat >> ~/.bashrc << 'ALIAS_BLOCK'

#==============================================================================
# SLURM Aliases (added by FRESCO Research System)
#==============================================================================

# View jobs
alias sq='squeue -u $USER'
alias sqw='squeue -u $USER -o "%.10i %.12P %.30j %.8u %.8T %.10M %.10l %.4D %R"'
alias sqstart='squeue -u $USER --start'
alias sqa='squeue'

# Job control
alias sc='scancel'
alias scall='scancel -u $USER'

# Account/resource info
alias slist='slist'

# Job details
sj() { scontrol show job "$1"; }
sjob() { scontrol show job "$1"; }

# Show partition traffic
sqshort() {
    echo "=== Idle Nodes ==="
    sinfo -p a30,a100-40gb,a100-80gb,v100 -t idle -o "%12P %6D %10G"
    echo ""
    echo "=== Pending Jobs ==="
    squeue -p a30,a100-40gb,a100-80gb,v100 -t PENDING -o "%P" | tail -n +2 | sort | uniq -c | sort -n
}

# Quick submit helpers
alias sba30='sbatch --partition=a30 --account=sbagchi --gres=gpu:1'
alias sba100='sbatch --partition=a100-40gb --account=sbagchi --gres=gpu:1'
alias sbstandby='sbatch --partition=a30 --account=sbagchi --gres=gpu:1 --qos=standby --time=04:00:00'

# Auto-select best partition (least pending jobs)
best_partition() {
    local partitions="a30,a100-40gb,a100-80gb,v100"
    # Get partition with fewest pending jobs
    local best=$(squeue -p "$partitions" --states=PENDING -o "%P" 2>/dev/null | tail -n +2 | \
        awk -F, '{print $1}' | sort | uniq -c | sort -n | head -1 | awk '{print $2}')
    # If no pending jobs, pick partition with most idle nodes
    if [ -z "$best" ]; then
        best=$(sinfo -p "$partitions" -t idle -o "%P %D" 2>/dev/null | tail -n +2 | \
            sort -k2 -rn | head -1 | awk '{print $1}' | tr -d "*")
    fi
    # Default fallback
    [ -z "$best" ] && best="a30"
    echo "$best"
}

# Submit to best partition automatically
sbbest() {
    local part=$(best_partition)
    echo "Selected partition: $part"
    sbatch --partition="$part" --account=sbagchi --gres=gpu:1 "$@"
}

# Show all SLURM aliases
slurm-help() {
    echo ""
    echo "=== SLURM Aliases ==="
    echo ""
    echo "VIEW JOBS:"
    echo "  sq          - Show my jobs (compact)"
    echo "  sqw         - Show my jobs (wide format with more details)"
    echo "  sqstart     - Show my jobs with estimated start times"
    echo "  sqa         - Show all jobs on cluster"
    echo ""
    echo "JOB CONTROL:"
    echo "  sc <JOBID>  - Cancel a specific job"
    echo "  scall       - Cancel ALL my jobs (use with caution!)"
    echo ""
    echo "JOB DETAILS:"
    echo "  sj <JOBID>  - Show detailed info for a job"
    echo "  sjob <JOBID>- Same as sj"
    echo ""
    echo "CLUSTER INFO:"
    echo "  slist       - Show accounts and resources available to me"
    echo "  sqshort     - Show which partition has shortest queue"
    echo ""
    echo "QUICK SUBMIT:"
    echo "  sba30 <script>     - Submit to a30 partition (normal qos)"
    echo "  sba100 <script>    - Submit to a100-40gb partition (normal qos)"
    echo "  sbstandby <script> - Submit to a30 with standby qos (4h max)"
    echo "  sbbest <script>    - Auto-select partition with shortest queue"
    echo "  best_partition     - Print the best partition (for manual use)"
    echo ""
    echo "EXAMPLES:"
    echo "  sq                      # Check my queue"
    echo "  sc 12345                # Cancel job 12345"
    echo "  sj 12345                # See job 12345 details"
    echo "  sbstandby myscript.slurm  # Quick standby submit"
    echo "  sbbest myscript.slurm     # Submit to least-busy partition"
    echo '  PART=$(best_partition); sbatch --partition=$PART script.slurm'
    echo ""
}

alias slurm-aliases='slurm-help'
#==============================================================================
ALIAS_BLOCK

echo "✓ SLURM aliases installed to ~/.bashrc"
echo ""
echo "To activate now, run:"
echo "  source ~/.bashrc"
echo ""
echo "Then type 'slurm-help' to see all available aliases."
