---
project: ARL RL
tags: [project/arl-rl, work-log]
created: 2025-10-06
---

# Stage E1 Overnight Run Initiated — 2025-10-06

## Summary
- Successfully initiated Stage E1 overnight training runs using the wait-and-run wrapper
- Set up robust memory monitoring and fallback batch size reduction for GPU contention scenarios
- Configured 2-hour timeout with automatic fallback to smaller batch size if needed

## Command Executed
```bash
bash scripts/wait_and_run_e1.sh --min-free 2048 --sleep 300 --timeout 7200 --fallback-batch 2 -- --res 32 > e1_master.log 2>&1 &
```

## Configuration Details
- **Memory threshold**: 2048MB (2GB) minimum free GPU memory required
- **Polling interval**: 300 seconds (5 minutes)
- **Timeout**: 7200 seconds (2 hours) - will proceed with fallback after this time
- **Fallback batch size**: 2 (reduced from default 8) if timeout is reached
- **Resolution**: 32×32 (GPU memory optimized)
- **Background execution**: Detached with logs redirected to `e1_master.log`

## Expected Behavior
1. **Phase 1**: Script monitors GPU memory every 5 minutes
2. **Phase 2a** (if memory available): Runs full Stage E1 training with batch_size=8
3. **Phase 2b** (if timeout reached): Runs Stage E1 training with batch_size=2 fallback
4. **Output**: Three sequential training runs (seeds 4, 6, 8) with 10,000 episodes each

## Stage E1 Training Parameters (Long Run Recipe)
- `NUM_EPISODES=10000` (extended from confirm runs)
- `REPLAY=100k` (double the replay buffer)
- `EPS_END=0.01` (lower final epsilon)
- `EPS_DECAY=100k` (slower decay)
- `TARGET_UPDATE_FREQ=300` (less frequent updates)
- `STEP_MUL=16` (higher action repeat)
- `LR=5e-5` (validated learning rate)
- `USE_DOUBLE_DQN=True` (Stage E1 algorithm)
- `LR_SCHEDULER=cosine` (Stage E1 learning rate scheduling)

## Monitoring & Results
- **Live monitoring**: Check `e1_master.log` for progress updates
- **Per-run artifacts**: Saved in `$RL_SAVE_PATH/{run_id}/` directories
- **Aggregated results**: Will be appended to `e1_results.csv`
- **Expected completion**: 8-12 hours depending on GPU availability and contention

## Risk Mitigation
- ✅ **Mixed precision training**: Reduces GPU memory usage by 25-40%
- ✅ **Memory monitoring**: Waits for sufficient GPU headroom before starting
- ✅ **Timeout fallback**: Automatically reduces batch size if memory never frees up
- ✅ **Background execution**: Won't be interrupted by terminal disconnection
- ✅ **Comprehensive logging**: All output captured for post-run analysis

## Next Steps (Morning Review)
1. Check `e1_master.log` for completion status and any errors
2. Review individual run results in `e1_results.csv`
3. Analyze win rates across the three seeds for Stage E1 effectiveness
4. Update Status.md and Experiments.md with results
5. Decide on next stage (E2: Dueling DQN) or parameter adjustments

## Context
This run represents the first major overnight training session using:
- The full Stage E1 algorithmic improvements (Double DQN + LR scheduling)
- Robust memory management and GPU contention handling
- Extended training episodes for better statistical validation
- Automated result collection and analysis pipeline