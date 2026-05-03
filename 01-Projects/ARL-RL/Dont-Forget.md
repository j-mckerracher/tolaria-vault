# Don't Forget — ARL RL

> [!note] Critical reminders
> Add key facts, deadlines, or gotchas here.

## PREFERRED: Use Standby QoS for Job Submissions (2025-11-20)

**Why**: Avoid hitting `AssocGrpGRES` limits on the `sbagchi` account.

**Preferred submission method** (direct sbatch with standby QoS):
```bash
cd /home/jmckerra/Code/ARL-RL

sbatch \
  --account sbagchi \
  --partition a30 \
  --qos standby \
  --time 4:00:00 \
  --mem 80G \
  scripts/run_e2.sh \
  --res 64 \
  --seeds "4 6 8" \
  --episodes 500
```

**Benefits**:
- Standby QoS uses backfill scheduling (avoids group GPU limits)
- Better for short/medium runs (2-4 hours)
- Less likely to block on `AssocGrpGRES`

**Queue Management**:
- Check queue: `squeue -u $USER`
- Check wait time: `squeue -u $USER -o "%.18i %.9P %.30j %.8u %.8T %.10M %.9l %.6D %R"`
- Cancel job: `scancel JOBID`

---

## Current Priority: Resolution Scaling (64×64)

**Next experiment**: Test frozen E2 config at 64×64 resolution
- **Why**: Better spatial awareness, natural progression from E2 success
- **Resource**: 80GB memory (vs 50GB for 32×32), 3-4h per seed
- **Episodes**: Start with 500-episode smoke test per seed
- **Expected**: Potential improvement over 94.3% baseline

**Before submitting**:
1. Check current queue: `squeue -u $USER`
2. Cancel any old pending jobs if blocking
3. Use standby QoS (see command above)

---

## Archive

### 2025-10-06: E1 OOM Fix (Completed - Archived)
Overnight E1 run hit OOM. Fixed with optimizer preallocation + reduced batch size (8→4).
See [[2025-10-06 OOM fix and memory optimizations]] for details.

