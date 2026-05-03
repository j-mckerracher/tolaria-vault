---
title: "Plan — ARL RL"
last_updated: "2025-11-30"
tags: ["project/arl-rl", "plan"]
---

## Objectives
Improve SC2 FindAndDefeatZerglings win rate with a staged RL roadmap under HPC constraints (Gilbreth), while maintaining reproducible runs and robust infrastructure.

### Strategy (Hierarchy)
- **Stage E1 (Double DQN + LR scheduler)**: ✅ Done. Validated at 32x32.
- **Stage E2 (Dueling DQN)**: ✅ Done. Production validation (3k eps) achieved 94.3% win rate. Config frozen.
- **Stage E3 (Prioritized Experience Replay)**: ⏸ Parked. Underperformed E2 baseline in alpha sweeps.
- **Stage E4 (N-step returns)**: Planned. Tune `n` (e.g., n=3) to assess stability and performance.
- **Resolution Scaling**: In Progress. Testing 64x64 resolution with frozen E2 config.

## Milestones

| Milestone | Owner | Target Date | Status | Links |
|---|---|---|---|---|
| E1 Baseline (Double DQN + LR scheduler) | josh | 2025-10-21 | ✅ Done | [[Documents/Experiments/expt-20251025-e2-tuf-sweep]] |
| E2 Validation (Dueling DQN gate) | josh | 2025-10-25 | ✅ Done | [[Documents/Experiments/expt-20251025-e2-confirm-1k]] |
| E2 Production (3k episodes) | josh | 2025-10-25 | ✅ Done | [[Documents/Experiments/expt-20251025-e2-prod-3k]] |
| E3 PER Exploration | josh | 2025-10-25 | ⏸ Parked | [[Decisions/2025-10-25 Park Stage E3 PER]] |
| Resolution Scaling (64×64) | josh | 2025-12-03 | 🚀 Ready for Submission | [[Documents/Experiments/expt-20251203-e2-res64]] |
| Documentation Restructuring Phase 1 | josh | 2025-10-25 | ✅ Done | [[RESTRUCTURING_SUMMARY_2025-10-25]] |
| Documentation Phase 2 (Legacy Migration) | josh | 2025-11-30 | ✅ Done | [[Work-Completed/Index]] |
| E4 N-step Returns (Design) | josh | 2025-12-01 | 📅 Planned | |

## Tasks

### Backlog
- E4 N-step returns smoke tests
- Extended validation (4k-5k episodes)
- Checkpoint cleanup and deployment prep
- KPI dashboard setup

### In Progress
- Resolution scaling 64×64 runs (monitor and analyze)
- System-wide wikilink audit (fix broken links from migration)
- Address information gaps (E1 smoke run job IDs, exact SLURM commands)

### Blocked
- E4 implementation (waiting on 64x64 results to decide baseline)

### Done
- Phase 2 legacy experiment migration (23 files)
- Phase 2 job note extraction
- Phase 2 daily log consolidation
- E1 & E2 validation and production runs
- E3 exploration and parking

## Risks & Mitigation
- **Risk**: 64×64 runs exceed memory. **Mitigation**: Use 80GB memory allocation; monitor GPU usage.
- **Risk**: E2 performance degrades with resolution. **Mitigation**: Fallback to 48×48 or revert to 32×32.
- **Risk**: Gilbreth queue congestion. **Mitigation**: Use standby QoS as backup; submit micro-chunks.

## Next 3 Actions
1. **Submit 64×64 resolution scaling jobs**: Execute the prepared sbatch command (standby/80GB).
2. **Monitor Job Progress**: Track for OOM and initial performance metrics.
3. **Address Info Gaps**: Locate missing E1 smoke run IDs and add to notes.

## Links
- [[Status]]
- [[Experiments]]
- [[Documents/Index]]
- [[Work-Completed/Index]]

## Changelog
- 2025-11-30 Updated structure to new template; marked Phase 2 migration as done.
- 2025-10-25 Updated for E2 production success and Phase 1 documentation completion.