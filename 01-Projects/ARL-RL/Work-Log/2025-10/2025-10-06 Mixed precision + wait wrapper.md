---
project: ARL RL
tags: [project/arl-rl, work-log]
created: 2025-10-06
---

# Mixed precision + wait wrapper (E1 hardening) — 2025-10-06

Summary
- Enabled true mixed precision to reduce GPU memory use and avoid OOM under A30 contention.
- Added a wait-and-run wrapper to automatically start E1 once GPU free memory is above a threshold.
- Extended env overrides for scheduler and test params to avoid code edits during experiments.

Changes
1) training_split.py
   - Mixed precision autocast:
     - Wrapped all network forward passes in `torch.amp.autocast('cuda')` when CUDA is available
       * select_action exploitation path (policy_net)
       * optimize_model (policy_net current batch)
       * optimize_model Double DQN target computation (policy_net next, target_net next)
   - GradScaler update:
     - Replaced deprecated `torch.cuda.amp.GradScaler()` with `torch.amp.GradScaler('cuda')`
     - Fallback to non-scaler path on CPU
   - Env overrides extended:
     - `RL_NUM_TEST_EPISODES`, `RL_USE_DOUBLE_DQN`, `RL_LR_SCHEDULER`, `RL_SCHEDULER_TMAX`, `RL_MIN_LR`, `RL_STEP_LR_STEP_SIZE`, `RL_STEP_LR_GAMMA`

2) scripts/wait_and_run_e1.sh (new)
   - Waits for GPU free memory to exceed a threshold, then runs Stage E1 via `scripts/run_e1.sh`
   - Flags:
     - `--gpu <index>`: pin to a specific GPU (exports CUDA_VISIBLE_DEVICES)
     - `--min-free <MB>`: minimum free memory threshold (default 2048)
     - `--sleep <seconds>`: polling interval (default 300)
     - `--timeout <seconds>`: maximum wait time before proceeding (default: infinite)
     - `--fallback-batch <size>`: batch size to use if timeout is reached (requires run_e1.sh --allow-env)
     - `--` then pass-through args to `run_e1.sh`

3) scripts/run_e1.sh (enhanced)
   - Added `--allow-env` flag to accept environment variable overrides on fallback
   - Supports `RL_BATCH_SIZE` override for memory-constrained scenarios

Usage examples
```bash
# Default: wait for any GPU to have >= 2GB free, then run seeds 4/6/8 at 32×32
bash scripts/wait_and_run_e1.sh -- --res 32

# Pin GPU 0, require 3GB+ free, poll every 120s, then run with explicit flags
bash scripts/wait_and_run_e1.sh --gpu 0 --min-free 3072 --sleep 120 -- --res 32 --seeds "4 6 8" --episodes 10000

# Run overnight (detached)
nohup bash scripts/wait_and_run_e1.sh -- --res 32 > e1_master.log 2>&1 &
```

Context & rationale
- We encountered OOM when the shared GPU had ~65MB free; even Adam’s optimizer state allocations can fail at that level.
- Autocast typically reduces activation memory by ~25–40%; the wait wrapper avoids starting until there is sufficient headroom.

Next
- Use `wait_and_run_e1.sh` for the overnight E1 runs.
- If memory remains tight even after autocast, consider a temporary `RL_BATCH_SIZE=2` run (we can add a safe override flag to `run_e1.sh` on request) or switch optimizer to SGD as a last resort.
