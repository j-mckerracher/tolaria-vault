---
project: ARL RL
tags: [project/arl-rl, work-completed]
created: 2025-10-25
---

# E2 Production 3k Validation Complete — 2025-10-25

## Summary
Successfully completed Stage E2 production validation with 3,000-episode runs across seeds 4, 6, and 8. Achieved **94.3% mean win rate** (97%/88%/98%), exceeding 1k-episode results (91.3%) and confirming E2 configuration as production-ready at scale.

## Work completed

### E2 production runs (3,000 episodes per seed)
- **Configuration**: Frozen E2 baseline (Dueling DQN, TUF=400, LR=5e-5, EPS_DECAY=100k, Batch=4, Replay=100k, Res=32, StepMul=16)
- **Seeds**: 4, 6, 8
- **Episodes**: 3,000 per seed
- **Results**:
  - Seed 4: **97.0%** win rate (502.0 total reward, 5.02 avg)
  - Seed 6: **88.0%** win rate (163.0 total reward, 1.63 avg)
  - Seed 8: **98.0%** win rate (517.0 total reward, 5.17 avg)
  - **Mean: 94.3%, StdDev: 5.7 pp**
- **Artifacts (HPC)**: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251025_021201_E1_seed{4,6,8}/`
- **Artifacts (local)**: `C:\Users\jmckerra\OneDrive - purdue.edu\Documents\ARL-RL-Experiment-Results\10-25-2025\`

### Performance progression confirmed
- 500 episodes: 52.7% mean (TUF-sweep-alt-3)
- 1,000 episodes: 91.3% mean (run-6 confirmatory)
- 3,000 episodes: **94.3% mean** (production)
- **Trend**: Robust improvement with scale, stable training

### Checkpoints saved
- 30+ checkpoints per seed (every 100 episodes)
- File size: ~64MB per checkpoint
- Total: ~6GB across all seeds
- **Recommendation**: Archive strategic checkpoints (ep100, ep1000, ep2000, ep3000), delete intermediates

## Impact
- **E2 validated at scale**: Production-level performance confirmed
- **Best individual result**: Seed 8 achieved 98% win rate (highest yet)
- **Configuration stability**: All seeds performed excellently (88-98% range)
- **Ready for next stage**: Foundation solid for resolution scaling, E4, or deployment

## Commands used
```bash
sbatch --account=sbagchi --partition=a30 --qos=normal --gres=gpu:1 \
  --ntasks=1 --cpus-per-task=4 --mem=50G --time=06:00:00 \
  --export=ALL,RL_SEED=<seed>,RL_NUM_EPISODES=3000,RL_LEARNING_RATE=0.00005,\
RL_EPS_DECAY=100000,RL_BATCH_SIZE=4,RL_REPLAY_MEMORY_SIZE=100000,\
RL_SCREEN_RESOLUTION=32,RL_STEP_MUL=16,RL_TARGET_UPDATE_FREQ=400,\
RL_DUELING_DQN=1 \
  scripts/run_e2.sh
```

## Next options
1. **Resolution scaling (64×64)**: Test E2 at higher resolution for improved spatial awareness
2. **Stage E4 (N-step returns)**: Add multi-step bootstrapping (n=3) for better credit assignment
3. **Extended validation (4k-5k eps)**: Push convergence limits
4. **Deployment prep**: Prepare best model (seed 8 ep3000) for production/demos

## Experiment log
- [[20251025_E2_production_3k]]

## Related
- [[Status]] — Updated with production results
- [[01 Projects/ARL-RL/Plan]] — Updated with next exploration options
- [[Experiments]] — Added production entry to summary table
- [[01 Projects/ARL-RL/Backlog]] — Marked production tasks complete
