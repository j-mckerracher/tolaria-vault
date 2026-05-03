---
project: ARL RL
tags: [project/arl-rl, work-log, slurm, e1]
created: 2025-10-19
---

# Stage E1 chained submissions — standby, 1k eps/seed, 32×32 — 2025-10-19

## Summary
- Submitted chained Stage E1 runs under standby QoS: seeds 4 → 6 → 8, each 1000 episodes, 32×32.
- Used job dependency chaining (afterok) to auto-start next seed on completion.

## Command run
```bash
jid4=$(sbatch --account sbagchi --partition a30 --qos standby --time 2:00:00 \
  --ntasks=1 --cpus-per-task=4 --mem=50G --gres=gpu:1 \
  /home/jmckerra/Code/ARL-RL/scripts/run_e1.sh --res 32 --episodes 1000 --seeds "4" | awk '{print $4}'); \
jid6=$(sbatch --dependency=afterok:$jid4 --account sbagchi --partition a30 --qos standby --time 2:00:00 \
  --ntasks=1 --cpus-per-task=4 --mem=50G --gres=gpu:1 \
  /home/jmckerra/Code/ARL-RL/scripts/run_e1.sh --res 32 --episodes 1000 --seeds "6" | awk '{print $4}'); \
jid8=$(sbatch --dependency=afterok:$jid6 --account sbagchi --partition a30 --qos standby --time 2:00:00 \
  --ntasks=1 --cpus-per-task=4 --mem=50G --gres=gpu:1 \
  /home/jmckerra/Code/ARL-RL/scripts/run_e1.sh --res 32 --episodes 1000 --seeds "8" | awk '{print $4}'); \
echo "Submitted: seed4=$jid4 seed6=$jid6 seed8=$jid8"
```

## Job IDs
- seed4: 9774460
- seed6: 9774461 (afterok:9774460)
- seed8: 9774462 (afterok:9774461)

## Context
- Backfill-friendly 2h chunks due to normal QoS queue pressure; chaining ensures sequential execution without manual resubmission.

## Monitoring
```bash
squeue -j 9774460,9774461,9774462 -o "%18i %9P %32j %8T %10M %9l %6D %R"
for j in 9774460 9774461 9774462; do f=$(scontrol show job $j | awk -F= '/StdOut=/{print $2}'); echo $j $f; done
```

## Artifacts
- Aggregation CSV: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/e1_results.csv`

## Next
- After completion, append results will be in `e1_results.csv`; create per-run notes if desired and update status.
