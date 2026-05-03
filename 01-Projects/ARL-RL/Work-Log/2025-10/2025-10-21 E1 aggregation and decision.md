---
project: ARL RL
tags: [project/arl-rl, work-log]
created: 2025-10-21
---

# E1 aggregation (100-ep tests) and decision — 2025-10-21

## Summary
Aggregated 100-episode tests after +200-episode top-ups at 32×32 for seeds 4/6/8.

- Seed 4: 59.0%
- Seed 6: 0.0%
- Seed 8: 73.0%
- Mean: 44.0%; StdDev: 38.7 pp

## Decision
Per criteria (proceed to E2 unless mean < 40% or StdDev > 40 pp):
- Proceed to **Stage E2 (Dueling DQN)**.

## Notes
- High variance persists but below the >40 pp threshold; move forward while keeping runs short and parallel to respect queue limits.
- See per-run pages:
  - [[20251021_212042_E1_seed4]]
  - [[20251021_212805_E1_seed6]]
  - [[20251021_212805_E1_seed8]]
