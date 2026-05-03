---
project: ARL RL
tags: [project/arl-rl, decision]
created: 2025-10-05
---

# Decision — Learning Rate choice after Sweep A

## Context
LR sweep results (top = best):
```
- 0.00005 → win_rate 57.0%, avg_reward 1.11
- 0.00025 → win_rate 11.0%, avg_reward 0.18
- 0.00010 → win_rate 6.0%,  avg_reward 0.11
```
Source CSV: C:\\Users\\jmckerra\\Downloads\\sweep_results_lr.csv
Artifacts per-run under: /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/

## Decision
Proceed with LR = 0.00005 for subsequent sweeps.

## Next actions (per Experiments Plan)
- Run Sweep B (epsilon decay) with LR fixed at 0.00005 and same resolution used in Sweep A (default 32×32):

```bash
export RL_SAVE_PATH="/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced"
export RL_LOG_DIR="/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/logs"
export SC2PATH="/home/jmckerra/StarCraftII"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

export RL_LEARNING_RATE=0.00005
bash scripts/sweep_eps_decay.sh --res 32
```

- After Sweep B, select the best epsilon decay and run Sweep C (target update freq) with LR=0.00005 and best decay.

## Notes
- Keep batch size at 8 and replay memory at 50k due to GPU contention.
- If GPU headroom improves, consider a follow-up confirmatory run at 64×64 with the winning parameters after Sweep C.
