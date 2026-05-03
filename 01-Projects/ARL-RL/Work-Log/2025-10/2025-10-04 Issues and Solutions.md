---
project: ARL RL
tags: [project/arl-rl, troubleshooting, work-log]
created: 2025-10-04
---

# Issues and Solutions — 2025-10-04

Comprehensive record of problems encountered while setting up parameter sweeps and NO_OP fixes for training_split.py on Gilbreth HPC.

## Issue 1: GPU Out of Memory

**Problem**: Initial run failed with CUDA OOM error on NVIDIA A30 (24GB)
```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 32.00 MiB. 
GPU 0 has a total capacity of 23.60 GiB of which 10.94 MiB is free. 
Process 1473544 has 21.62 GiB memory in use.
```

**Root Cause**: GPU heavily used by other processes (23.2GB/24GB occupied)

**Solution**: Reduced memory footprint via environment variables
- RL_BATCH_SIZE: 32 → 8
- RL_REPLAY_MEMORY_SIZE: 10000 → 5000  
- RL_SCREEN_RES: 64 → 32
- RL_MINIMAP_RES: 64 → 32
- Added: PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

**Result**: Training completed successfully, 8% baseline win rate established

## Issue 2: Password-Protected StarCraft II Archive

**Problem**: SC2.4.10.zip required password during extraction
```
[SC2.4.10.zip] StarCraftII/Versions/Shaders41359/OpenGL2/baselineCache.bin password:
```

**Root Cause**: Downloaded SC2 archive was password-protected

**Solution**: Downloaded alternative SC2 archive from Blizzard CDN
```bash
wget http://blzdistsc2-a.akamaihd.net/Linux/SC2.4.10.zip
```

**Result**: Successfully installed SC2 headless on Gilbreth with SC2PATH=/home/jmckerra/StarCraftII

## Issue 3: Training-from-Scratch Gating

**Problem**: Script required existing model_ep{NUM_EPISODES}.pth before training
- Would exit with "Train first!" if checkpoint not found
- START_EPISODE was 2000 but expected final checkpoint to exist

**Root Cause**: Logic designed for resuming training, not starting fresh

**Solution**: Modified main() function in training_split.py
- If checkpoint exists: load and optionally test
- If not: print message and proceed with training from scratch
- Changed START_EPISODE default: 2000 → 0

**Result**: Can now train from scratch without pre-existing checkpoints

## Issue 4: NO_OP Idling Behavior

**Problem**: Terran units staying idle instead of attacking
- 8% win rate lower than expected 20% baseline
- Agent choosing NO_OP even when meaningful actions available

**Root Cause**: Action selection didn't prioritize attack-enabling actions
- Exploration sampled NO_OP equally with other actions
- Exploitation didn't penalize NO_OP when better options existed

**Solution**: Modified select_action() in DQNAgent
- Priority gate: if attack_screen unavailable but select_army available → force select_army
- Exploration: exclude NO_OP from sampling if any other action available
- Exploitation: heavily penalize NO_OP (-1e9) when meaningful actions exist
- Removed duplicate/unreachable elif for ACTION_SELECT_ARMY

**Result**: Action selection now prioritizes unit selection and attacking over idling

## Issue 5: Parameter Sweep Infrastructure Missing

**Problem**: No way to run parameter sweeps without editing code
- Hard-coded Config class parameters
- No systematic result tracking

**Root Cause**: Script designed for single runs, not experimentation

**Solution**: Added environment variable override system
- Created override_from_env(Config) function
- Supports all key parameters: RL_EPS_START, RL_LEARNING_RATE, RL_BATCH_SIZE, etc.
- Added RL_RUN_ID for unique run identification
- Auto-creates run directories under SAVE_PATH/RUN_ID

**Result**: Can configure runs via bash exports without code changes

## Issue 6: Missing Result Persistence

**Problem**: No structured way to capture and compare experiment results
- Had to parse stdout manually for win rates
- No config traceability between runs

**Root Cause**: Script only printed results, didn't persist them

**Solution**: Added JSON result persistence
- config.json: effective Config + environment snapshot at run start
- eval/test_results.json: structured test results (win_rate, avg_reward, etc.)
- Timestamped with UTC for correlation

**Result**: Each run creates machine-readable artifacts for sweep aggregation

## Issue 7: Sweep Result Tracking

**Problem**: No systematic way to track multiple sweep runs
- Results scattered across individual run directories
- Manual effort to compare performance

**Root Cause**: Needed batch execution and result aggregation

**Solution**: Created sweep automation scripts
- scripts/sweep_lr.sh, sweep_eps_decay.sh, sweep_tuf.sh
- Each appends results to CSV: sweep_results_*.csv
- tools/aggregate_results.py for cross-run summary
- Logs tee'd to both stdout and per-run files

**Result**: Systematic parameter exploration with CSV tracking

## Issue 8: Lack of Debugging Information

**Problem**: First LR sweep produced blank CSV (no win_rate/avg_reward values)
- Couldn't diagnose what went wrong during runs
- Only stdout/stderr available, mixed with SC2 noise

**Root Cause**: Insufficient logging and error handling

**Solution**: Added logging system
- Per-run log files in RL_LOG_DIR (/depot/.../logs)
- Periodic episode summaries every 50 episodes
- Test completion logging with structured info
- Unhandled exception hook captures crashes
- Both console and file output

**Result**: Full visibility into run progress and failure modes

## Issue 9: JSON Serialization Error

**Problem**: Script crashed when writing test_results.json
```
TypeError: Object of type int64 is not JSON serializable
```

**Root Cause**: NumPy int64/float64 types not JSON-serializable by default

**Solution**: Explicit type casting in test results
- Cast all numeric values to built-in Python types (int, float)
- Added try/except around JSON write with logging
- Log success/failure of JSON persistence

**Result**: test_results.json writes successfully, sweep CSVs populate correctly

## Issue 10: Obsidian Experiment Tracking

**Problem**: No systematic way to document and compare experiments
- Results scattered across HPC filesystem
- No organized tracking of what was tried and learned

**Root Cause**: Needed structured experiment documentation

**Solution**: Created Obsidian experiment tracking system
- Experiments.md hub with summary table
- Experiments/TEMPLATE.md for consistent per-run documentation  
- Experiments/Plan.md with phased approach
- Work Completed entries for major changes
- Linked from Home.md for easy access

**Result**: Structured knowledge management for all experiments and decisions

## Summary of Key Learnings

1. **Memory Management**: GPU contention requires careful resource tuning
2. **Environment Setup**: HPC environments need robust installation procedures
3. **Code Architecture**: Single-run scripts need infrastructure for systematic experimentation
4. **Error Handling**: Comprehensive logging essential for remote debugging
5. **Data Serialization**: Type casting required for cross-language data exchange
6. **Documentation**: Structured tracking prevents lost knowledge and enables iteration

## Current Status

✅ Infrastructure complete: env overrides, logging, JSON persistence, sweep scripts  
✅ Obsidian tracking system in place  
✅ Issues 1-9 resolved  
🔄 Re-running LR sweep with fixes  
⏳ Pending: epsilon decay and target update frequency sweeps  

## Next Steps

1. Complete LR sweep with working result persistence
2. Analyze results and proceed to epsilon decay sweep
3. Use logging to diagnose any future issues quickly
4. Document results in per-run Obsidian pages