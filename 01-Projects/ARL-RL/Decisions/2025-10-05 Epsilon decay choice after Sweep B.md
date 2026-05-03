---
project: ARL RL
tags: [project/arl-rl, decision]
created: 2025-10-05
---

# Decision — Epsilon Decay choice after Sweep B

## Context
Epsilon-decay sweep results (higher is better):
```
- 20000  → win_rate 13.0%, avg_reward -0.10
- 100000 → win_rate 10.0%, avg_reward  0.10
- 50000  → win_rate  1.0%, avg_reward  0.00
```
Source CSV: C:\\Users\\jmckerra\\Downloads\\sweep_results_eps.csv
Artifacts per-run under: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/
Note: These runs recorded LR=0.0001 in the CSV; our LR choice from Sweep A is 0.00005. While LR and decay do interact, we proceed with the best decay observed here and validate in the next phase.

## Decision
Proceed with EPS_DECAY = 20000 for the next sweep (target update frequency), with LR fixed at 0.00005 from Sweep A.

## Next actions (per Experiments Plan)
Run Sweep C (target update frequency) with LR=0.00005 and EPS_DECAY=20000 at the same resolution used previously (32×32):

```bash
export RL_SAVE_PATH="/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced"
export RL_LOG_DIR="/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/logs"
export SC2PATH="/home/jmckerra/StarCraftII"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

export RL_LEARNING_RATE=0.00005
export RL_EPS_DECAY=20000
bash scripts/sweep_tuf.sh --res 32
```

- After Sweep C completes, pick the best TARGET_UPDATE_FREQ and proceed to Phase 2 (confirm and extend):
  - RL_NUM_EPISODES=3000
  - Seeds: 4 and 6
  - Use LR=0.00005, EPS_DECAY=20000, and the best TUF

## Optional quick validation
If desired, run a single short validation (e.g., 1200 episodes) with LR=0.00005 & EPS_DECAY=20000 before Sweep C to confirm no regression versus the Sweep B LR (0.0001).
