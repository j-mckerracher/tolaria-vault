---
project: ARL RL
tags: [project/arl-rl, work-log]
created: 2025-10-03
---

# Code updates — 2025-10-03

Summary of changes made to `training_split.py` to support runs on Gilbreth via terminal and to reduce idle NO_OP behavior.

What changed
- Training-from-scratch: removed hard gating on the final checkpoint; if checkpoint not found, prints a message and trains from scratch.
- Env-var parameter overrides: added `override_from_env()` so runs can be configured without editing code (e.g., `RL_EPS_START`, `RL_LEARNING_RATE`, `RL_REPLAY_MEMORY_SIZE`, `RL_NUM_EPISODES`, `RL_START_EPISODE`, `RL_SAVE_PATH`, `RL_RUN_ID`, etc.).
- NO_OP idling fix: action selection now prioritizes `select_army` when `attack_screen` is unavailable and de-prioritizes `no_op` whenever other actions are available (both in exploration and exploitation paths). Removed a duplicate unreachable `select_army` fallback branch in `_get_pysc2_action`.
- Default `START_EPISODE` set to 0 to match the train-from-scratch workflow.

Where
- File: `C:\Users\jmckerra\PycharmProjects\ARL-RL\training_split.py`

Notes
- These are targeted changes; no network/algorithm modifications.
- Use env vars to run parameter sweeps on Gilbreth from an interactive terminal session.

Next
- Baseline run from scratch with default parameters, then parameter sweeps via env vars and track results in `Experiments.md`.
