---
project: ARL RL
tags: [project/arl-rl, log]
created: 2025-10-23
---

# 2025-10-23 — E2 TUF sweep (200 vs 400) preliminary results

## Summary of what happened
- Initiated TUF sweep under E2 (dueling enabled) with 500 episodes per seed on standby QoS.
- First set (presumed TUF=200): seeds 4/6/8 achieved 67% / 98% / 16%.
- Alternate run (presumed TUF=400) for seed 8 achieved 51% (vs. 16%), indicating TUF impacts stability/performance.

## Decisions and motivations
- Motivation: identify a target update frequency that stabilizes performance across seeds under E2 without changing other hyperparameters.
- Decision: complete missing seeds (4 and 6) at the better‑performing TUF (presumed 400) before drawing conclusions.

## Impact on subsequent steps
- Next: submit 500‑episode runs for seeds 4 and 6 at the presumed TUF=400, then aggregate across seeds.
- Progression gate: if mean ≥ 44% with acceptable variance, proceed to 1,000‑episode confirmatory runs; otherwise, consider minor E2 hyperparameter tweaks.
- Continue using standby backfill micro‑chunks for quick turnaround; keep detailed logs in Experiments.

## Metadata
- Artifacts root: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/10-22-2025/TUF-sweep-200-400-dueling-500-eps-per-seed/`
- Example runs: `20251023_014435_E1_seed{4,6,8}`, `20251023_014437_E1_seed8`
