---
project: ARL RL
tags: [project/arl-rl, work-log, slurm]
created: 2025-10-21
---

# Queue Stall Fix — Normal QoS Resubmission — 2025-10-21

## Summary
Canceled long-pending standby job chain (9774460–9774462) and resubmitted as independent normal QoS jobs on A30 partition for significantly faster start.

## Problem
- Standby chain (9774460→9774461→9774462) had been queued for 2+ days with no start.
- Low-priority backfill unlikely to get GPU time soon under cluster load.
- Time-sensitive experiments needed faster execution.

## Solution

### Cancellation
```bash
scancel 9774460 9774461 9774462
```

### Resubmission (independent, normal QoS)
```bash
for s in 4 6 8; do bash scripts/submit_e1_job.sh --account sbagchi --partition a30 --qos normal --time 04:00:00 --seeds "$s" --episodes 1000; done
```

## New Job IDs (Normal QoS, Independent Runs)
- Seed 4: **9795192** (1000 eps, 4h wall time)
- Seed 6: **9795193** (1000 eps, 4h wall time)
- Seed 8: **9795194** (1000 eps, 4h wall time)

## Configuration (Per Job)
- Partition: a30
- QoS: normal (higher priority, no dependency chain)
- Wall time: 04:00:00 (sufficient for ~1000 episodes at 32×32)
- Resources: ntasks=1, gpu=1, cpus-per-task=4, mem=50G
- Training: 1000 episodes per seed, Stage E1 recipe (Double DQN + LR scheduler)
- Resolution: 32×32

## Rationale
- **Independent runs**: Removes dependency chain overhead; each job can start as soon as GPU frees.
- **Normal QoS**: Higher priority than standby; typical wait time minutes–hours vs. days.
- **4h wall time**: Sufficient for 1k episodes; allows some headroom without bloating request.
- **Parallel potential**: If multiple A30 GPUs free, all three can run concurrently.

## Monitoring
```bash
squeue -j 9795192,9795193,9795194 -o "%18i %9P %32j %8T %10M %9l %6D %R"

# Per-job
squeue -j 9795192
squeue -j 9795193
squeue -j 9795194

# Watch completion
for j in 9795192 9795193 9795194; do 
  echo "Job $j:"; scontrol show job $j | grep -i "State\|RunTime\|TimeLimit"; 
done
```

## Expected Outcome
- Faster start (normal QoS priority vs. standby backfill)
- Results aggregated in `e1_results.csv` once complete
- Per-run artifacts in `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/`

## Next Steps
1. Monitor jobs for start and completion
2. Verify results in CSV and per-run directories
3. Analyze variance if results show similar spread (0–80%) as smoke runs
4. Decide on Stage E2 or parameter adjustment based on E1 convergence

## Related
- [[2025-10-19 Stage E1 chained 1k eps seeds 4 6 8]] (canceled)
- [[2025-10-19 Stage E1 smoke runs seeds 6 and 8]]
- [[2025-10-19 Stage E1 smoke run 300eps seed4]]
