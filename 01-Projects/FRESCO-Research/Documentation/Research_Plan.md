# FRESCO Research Plan

**Goal**: Discover new trends, issues, and insights in the FRESCO dataset using systematic ML experimentation.

## Research Paths

### Path A: Anomaly Detection
*Objective: Identify abnormal job behaviors.*
- [x] EXP-001: Baseline statistical analysis
- [ ] EXP-002: Isolation Forest implementation

### Path B: Performance Prediction
*Objective: Predict job completion time or resource usage.*
- [ ] EXP-003: Linear Regression baseline
- [ ] EXP-004: Transformer-based time-series model

### Path C: Cross-Site Runtime + Peak Memory Prediction (Generalization)
*Objective: Quantify and mitigate cross-site transfer gaps for runtime and peak-memory prediction across Anvil/Conte/Stampede using leakage-safe FRESCO features.*
*Document: [Planning/PATH-C_cross_site_runtime_memory_prediction/README.md](../Planning/PATH-C_cross_site_runtime_memory_prediction/README.md)*
- [ ] EXP-005: Data extraction + cleaning validation
- [ ] EXP-006: Within-site baselines (time splits) for runtime + peak memory
- [x] EXP-007: Cross-site zero-shot transfer matrix + error slicing
- [x] EXP-008: Transfer matrix CIs + shift metrics + pooled training
- [x] EXP-009: Conte anomaly resolution (Drift vs Under-specification)
- [x] EXP-010: Few-shot calibration on target site (error vs label fraction)

## Backlog
- Explore correlation between failures and user request patterns.
- Cross-institutional comparison (Purdue vs TACC).
