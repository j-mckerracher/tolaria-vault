---
project: ARL RL
tags: [project/arl-rl, work-log, slurm]
created: 2025-10-11
---

# Stage E1 submission — normal QoS, 12h, 4k episodes — 2025-10-11

## Summary
Submitted Stage E1 training using normal QoS to allow a longer wall time window, and reduced per-seed episodes to 4,000 to ensure completion.

- Partition/account/QoS: a30 / sbagchi / normal
- Resources: ntasks=1, gpus=1 (via --gres), cpus-per-task=4, mem=50G, time=12:00:00
- Training: res=32×32, seeds=4 6 8, episodes=4,000 (per seed)
- Job ID: 9719090

## Commands
Wrapper invocation:
```bash
bash scripts/submit_e1_job.sh --account sbagchi --partition a30 --qos normal --time 12:00:00 --episodes 4000
```

Resulting sbatch:
```bash
sbatch --job-name=E1_Training_32x32 \
  --time=12:00:00 \
  --account=sbagchi \
  --partition=a30 \
  --qos=normal \
  --ntasks=1 \
  --gres=gpu:1 \
  --cpus-per-task=4 \
  --mem=50G \
  /home/jmckerra/Code/ARL-RL/scripts/run_e1.sh \
  --res 32 --seeds "4 6 8" --episodes 4000
```

Submission output:
```text
✅ Job submitted successfully!
Submitted batch job 9719090
```

## Rationale
- standby QoS window is too short for 10k episodes across 3 seeds.
- normal QoS allows longer wall times (subject to account policy), and reducing episodes per job increases the chance of completion.

## Notes
- If needed, further split runs by seed or chunk episodes per job (see Engineering Notes for chunking and job dependencies).

## Monitoring
```bash
squeue -j 9719090
cat e1_training_9719090.out
cat e1_training_9719090.err
```