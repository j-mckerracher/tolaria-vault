---
project: ARL RL
tags: [project/arl-rl, work-log, slurm]
created: 2025-10-21
---

# Stage E1 — 2h standby chunks (800 eps per seed) — 2025-10-21

## Summary
Completed 2-hour standby runs at 32×32 for seeds 4, 6, and 8. Each run reached ~800 episodes and produced test evaluations over 5 episodes.

## Results
- Seed 4 — Run [[20251021_164433_E1_seed4]]: win_rate 20.0%, avg_reward 1.0
- Seed 6 — Run [[20251021_164432_E1_seed6]]: win_rate 40.0%, avg_reward 0.4
- Seed 8 — Run [[20251021_164435_E1_seed8]]: win_rate 20.0%, avg_reward 0.2

Artifacts (local): `01 Projects/ARL RL/Experiment-Results/10-21-2025/`

## Configuration (per job)
- Episodes: 800
- Resolution: 32×32
- LR=5e-5, EPS_DECAY=100k, TUF=300, Batch=4, StepMul=16
- Test episodes: 5

## Notes
- Variance persists across seeds but appears to moderate relative to 300-episode smoke runs.
- Proceed by adding another short chunk per seed to reach 1k+ episodes for more reliable comparison.

## Next
1) Submit additional short chunks (200–400 eps) per seed to reach ≥1000 episodes.  
2) Aggregate in `e1_results.csv` and update Experiments with final 1k-episode outcomes.  
3) Decide E2 (Dueling) vs. E1 tuning based on cross-seed mean/variance at ≥1k eps.
