---
project: ARL RL
tags: [project/arl-rl, work-log]
created: 2025-10-06
---

# Stage E1 — Double DQN + LR scheduler (implemented) — 2025-10-06

Summary
- Implemented Stage E1 in `training_split.py`:
  - Double DQN target across non-spatial and spatial branches:
    - Select best next (non-spatial action idx and spatial arg idx) via policy_net
    - Evaluate those choices via target_net
    - Use max(non-spatial, spatial) as next-state target
  - LR scheduler support (default: CosineAnnealingLR; optional StepLR):
    - Stepped per-episode; logged every 100 episodes
  - Config flags (defaults on): `USE_DOUBLE_DQN=True`, `LR_SCHEDULER="cosine"`, `SCHEDULER_TMAX=None`, `MIN_LR=1e-6`, `STEP_LR_STEP_SIZE=1000`, `STEP_LR_GAMMA=0.5`
  - Logging: run start logs DoubleDQN+Scheduler settings

Automation
- Added `scripts/run_e1.sh` to launch the three long confirms sequentially (seeds 4, 6, 8) and append results to `e1_results.csv`.
  - Enforces long-run recipe: `NUM_EPISODES=10000`, `REPLAY=100k`, `EPS_END=0.01`, `EPS_DECAY=100k`, `TUF=300`, `STEP_MUL=16`, `LR=5e-5` at 32×32.
  - Per-run artifacts in `$RL_SAVE_PATH/$RL_RUN_ID/`; central logs in `$RL_LOG_DIR`.

Commands (bash, 32×32)
```bash
bash scripts/run_e1.sh --res 32
# optional
# bash scripts/run_e1.sh --res 32 --seeds "4 6 8" --episodes 10000
```

Outputs
- Per run: `config.json`, `eval/test_results.json`, `train.log`, central `.log` file
- Aggregated: `$RL_SAVE_PATH/e1_results.csv`

Next
- Let Stage E1 long runs complete overnight.
- In the morning, aggregate results and update Experiments/Status; then decide whether to proceed to E2 (Dueling) or adjust E1 parameters.
