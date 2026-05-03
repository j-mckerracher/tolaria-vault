---
project: ARL RL
tags: [project/arl-rl, log]
created: 2025-10-22
---

# 2025-10-22 — E2 dueling head implemented and smoke runs submitted

## Summary of what happened
- Created and switched to branch "e2-dueling-nonspatial".
- Implemented E2 feature: enabled dueling head on the non-spatial branch; added config flag `RL_USE_DUELING_DQN` (default true) with environment variable override.
- Updated agent initialization so policy and target networks honor the dueling flag; adjusted optimizer preallocation to include dueling outputs; enhanced startup logging to show dueling usage.
- Submitted initial E2 jobs with 500 episodes per seed (seeds 4/6/8) on standby QoS.
- Aggregated E2 100-episode test results across seeds: mean win rate ≈ 44% with high variance.

## Decisions and motivations
- Enable dueling on non-spatial head to explore performance improvements with minimal hyperparameter changes.
- Use 100-episode tests as a quick gating metric to decide whether to progress to longer runs or tune.

## Impact on subsequent steps
- Do not progress to long confirmatory runs yet due to high variance and borderline mean.
- Plan a short sweep of Target Update Frequency (TUF: 200 and 400) under E2 to assess stability and seed sensitivity.
- After completing the sweep and aggregating across seeds, decide whether to run 1,000‑episode confirmatory tests.

## Metadata
- Config: `RL_USE_DUELING_DQN=true` (default), other hyperparameters retained from E1 unless noted; env override supported.
- Artifacts: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/10-22-2025/`
