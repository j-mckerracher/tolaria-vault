---
project: ARL RL
tags: [project/arl-rl, decision]
created: 2025-10-06
---

# Decision — Adopt Double DQN + LR schedule (Stage E1)

## Context
- Parameter-only tuning reached ~24.3% mean (seeds 4/6/8) at 32×32.
- Goal is ~90% on FindAndDefeatZerglings; requires algorithmic upgrades for stable, high performance.

## Decision
Adopt Stage E1:
- Enable Double DQN (policy selection, target evaluation) across non-spatial and spatial branches (max of the two).
- Enable LR scheduler (default: cosine; T_max=NUM_EPISODES, eta_min=MIN_LR).

## Implementation (summary)
- Config flags: USE_DOUBLE_DQN=True, LR_SCHEDULER="cosine", SCHEDULER_TMAX=None, MIN_LR=1e-6.
- Optimize step: Double DQN target computed by selecting best next via policy_net and evaluating with target_net.
- Scheduler stepped per episode; LR logged every 100 episodes.

## Next
- Run 3 long confirms (32×32): NUM_EPISODES=10000, REPLAY=100k, EPS_END=0.01, EPS_DECAY=100k, TUF=300, STEP_MUL=16; seeds 4, 6, 8.
- Evaluate with 200 test episodes per run and aggregate.
