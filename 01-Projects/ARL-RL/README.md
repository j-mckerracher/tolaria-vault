# ARL-RL Project

> [!NOTE] Last Updated
> 2025-11-20

## 🎯 Current Status

**Phase**: Stage E2 Production Validated ✅  
**Achievement**: **94.3% mean win rate** at 3,000 episodes (seeds 4/6/8: 97%/88%/98%)  
**Progress**: E1 (44% → E2 @ 52.7% → 91.3% → **94.3%**) — Excellent scaling confirmed

**Current Decision Point**: Choose next exploration direction (see Next Actions below)

---

## 🔴 Immediate Next Action

**PRIORITY**: Submit 64×64 Resolution Scaling Jobs

**Why**: Natural progression from E2 success; test if higher resolution improves spatial awareness  
**Status**: No jobs pending
**Blocker**: None

**Command** (after checking/canceling old jobs):
```bash
cd /home/jmckerra/Code/ARL-RL

sbatch --account sbagchi --partition a30 --qos standby \
  --time 4:00:00 --mem 80G \
  scripts/run_e2.sh --res 64 --seeds "4 6 8" --episodes 500
```

See [[Dont-Forget]] for preferred submission patterns.

---

## 📍 Quick Navigation

### Core Documentation
- **[[Status]]** — Current status, recent results, stage progression
- **[[Plan]]** — Overarching roadmap, milestones, risk tracking
- **[[Experiments]]** — Canonical experiment tracker with all runs
- **[[RESULTS_SUMMARY]]** — Executive summary for research reporting

### Finding Information
- **Decisions**: [[Decisions/Index]] — Key choices with rationale
- **Work Logs**: [[Work-Log/Index]] — Chronological work history
- **How-To Guides**: [[Documents/Index]] — SLURM, commands, engineering notes
- **Scripts**: [[Scripts-Reference/README|Scripts Reference]] — Reference copies of SLURM job scripts

---

## 🚧 Known Issues & Blockers

### Active Blockers
- **SLURM Queue**: 3 jobs hitting `AssocGrpGRES` limit (need cancellation)
- **Decision Point**: Need to choose next exploration direction

### Configuration Notes
- **Frozen E2 Config**: LR=5e-5, TUF=400, Batch=4, Replay=100k, Res=32, StepMul=16, Dueling=1
- **Preferred QoS**: Use `standby` to avoid group GPU limits (see [[01-Projects/Demo-ICLR-Confidential/Don't Forget]])
- **Account**: `sbagchi` on Gilbreth cluster

---

## 📊 Key Results Summary

| Stage       | Algorithm                 | Episodes | Win Rate  | Status     |
| ----------- | ------------------------- | -------- | --------- | ---------- |
| E1          | Double DQN + LR Scheduler | 1k       | 44.0%     | ✅ Done     |
| E2 (500)    | + Dueling DQN             | 500      | 52.7%     | ✅ Done     |
| E2 (1k)     | + TUF=400                 | 1k       | 91.3%     | ✅ Done     |
| **E2 (3k)** | **Frozen Config**         | **3k**   | **94.3%** | ✅ **Done** |
| E3          | + PER                     | 500      | <E2       | ⏸️ Parked  |

---

## 🔗 External Resources

- **Code Repository**: `/home/jmckerra/Code/ARL-RL` on Gilbreth
- **Results Path**: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced`
- **Local Results**: `C:\Users\jmckerra\OneDrive - purdue.edu\Documents\ARL-RL-Experiment-Results\`
- **Cluster**: Gilbreth HPC (Purdue)

---
