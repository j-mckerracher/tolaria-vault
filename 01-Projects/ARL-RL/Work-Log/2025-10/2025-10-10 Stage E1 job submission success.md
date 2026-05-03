---
project: ARL RL
tags: [project/arl-rl, work-log, slurm]
created: 2025-10-10
---

# Stage E1 Job Submission — success (A30 standby) — 2025-10-10

## Summary
Successfully submitted Stage E1 training job on Gilbreth using the new SLURM wrapper and corrected submission parameters.

- Partition/account/QoS: a30 / sbagchi / standby
- Resources: ntasks=1, gpus=1 (via --gres), cpus-per-task=4, mem=50G, time=2:00:00
- Training: res=32×32, seeds=4 6 8, episodes=10000
- Job ID: 9716984

## Commands
Wrapper invocation:
```bash
bash scripts/submit_e1_job.sh --account sbagchi
```

Resulting sbatch command:
```bash
sbatch --job-name=E1_Training_32x32 \
  --time=2:00:00 \
  --account=sbagchi \
  --partition=a30 \
  --qos=standby \
  --ntasks=1 \
  --gres=gpu:1 \
  --cpus-per-task=4 \
  --mem=50G \
  /home/jmckerra/Code/ARL-RL/scripts/run_e1.sh \
  --res 32 --seeds "4 6 8" --episodes 10000
```

Submission output:
```text
✅ Job submitted successfully!
Submitted batch job 9716984
```

## Monitoring
```bash
squeue -u $USER
squeue -j 9716984

# After completion
cat e1_training_9716984.out
cat e1_training_9716984.err
```

## Recent Developments (captured in code + docs)
- SLURM requirements corrected for Gilbreth (partition, account, QoS required; GPUs via --gres=gpu:N).
- scripts/run_e1.sh:
  - Added SBATCH block with resources and placement defaults (a30/standby), time, logging, pre-flight checks, conda activation path (/depot/sbagchi/data/preeti/anaconda3/envs/gpu), cleanup trap, job summary.
- scripts/submit_e1_job.sh:
  - Requires --account; supports --partition/--qos; uses --gres=gpu:N; validates ntasks/cpus/mem.
  - Fixed set -u issues (removed legacy NODES/GPUS vars).
- scripts/README_SLURM.md: Updated examples and guidance.
- Documents:
  - Submitting SLURM Jobs on Gilbreth for LLMs.md: Replaced nodes/gpus-per-node guidance with partition/account/qos + resources and --gres examples.
  - How to construct a SLURM job submission script.md: Updated directive examples and fixed formatting.
  - Gilbreth SLURM Queues.md: Added and referenced RCAC guidance.
- Work Completed entries added for the Gilbreth submission fixes.

## Next
- Monitor job 9716984; verify logs and artifacts.
- Confirm e1_results.csv aggregation updates.
- If stable, extend time to 12:00:00 for full runs and/or adjust QoS as needed.
