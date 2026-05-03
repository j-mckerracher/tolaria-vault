# Research Path: PATH-C - Cross-Site Runtime + Peak Memory Prediction (Generalization)

**Created**: 2026-01-25  
**Last Updated**: 2026-02-01  
**Status**: Active  
**Lead**: jmckerra

---

## Research Questions

1. **RQ-2A (Runtime transfer)**: If we train a runtime predictor on cluster/site A, how well does it predict runtime on cluster/site B with no retraining?
2. **RQ-2B (Memory transfer)**: If we train a peak-memory predictor on A, how well does it predict peak memory on B?
3. **RQ-2C (Why transfer fails)**: Which job subpopulations drive cross-site error (e.g., GPU jobs, I/O-heavy jobs, short jobs, specific queues/partitions)?
4. **RQ-2D (Mitigation)**: How quickly can few-shot calibration on the target site reduce the cross-site transfer gap?

## Hypothesis

**Primary Hypothesis**:  
Cross-site prediction error will increase substantially vs within-site evaluation due to policy/hardware/workload shift, and adding normalization + submission-context features (F0→F1) will reduce the transfer gap.

**Null Hypothesis**:  
Cross-site error is not meaningfully worse than within-site error (within statistical uncertainty), and/or the feature additions do not measurably reduce the cross-site gap.

**Alternative Hypotheses**:  
- Transfer degradation is driven primarily by temporal drift rather than site differences (era shift dominates site shift).
- Memory prediction transfers comparably to runtime (or worse), depending on how “peak memory” is defined in FRESCO and how missingness is handled.

---

## Background & Motivation

### Why This Research Matters

Operational resource management (scheduling, queue selection, admission control, and user guidance) depends on accurate expectations of job runtime and peak memory. Most predictive models are evaluated within a single site, but real deployments often face distribution shift: new hardware generations, policy changes, and differing workload mixes across institutions.

FRESCO provides a rare multi-institution, longitudinal view of production HPC workloads. This path aims to quantify “transferability” (train on one site, test on another) and to identify the job archetypes responsible for transfer failures, producing evidence and mitigation strategies that are directly usable by HPC operators and publishable as generalizable findings.

### Connection to FRESCO Dataset

This path uses job attributes and aggregate performance metrics from multiple FRESCO sites/clusters.

- **Clusters used**: Purdue Anvil, Purdue Conte, TACC Stampede
- **Time period of interest**: To be defined per experiment; prioritize stable windows with sufficient history for user-aggregate features
- **Key metrics**: Runtime (end-start), memory usage aggregates (peak/high-water), plus CPU/GPU/I/O aggregates if available and leakage-safe
- **Key job attributes**: submit/start/end times; requested CPUs/nodes/GPUs/memory/walltime; queue/partition; exit state/codes; user/account/project identifiers (if available)

---

## Literature Review

See detailed literature in: [literature.md](literature.md)

### Key Prior Work

| Paper | Relevance | Key Finding |
|-------|-----------|-------------|
| (TBD) | Cross-site generalization and workload prediction | (TBD) |

### Research Gap

Cross-site generalization for runtime and memory prediction is rarely quantified on large, real, multi-institution HPC datasets with strict leakage controls and reproducible evaluation. This path will provide (i) a transfer-matrix baseline with confidence intervals, (ii) feature/model ablations to identify what improves transfer, (iii) error decomposition by job archetype/queue/size/era, and (iv) at least one practical mitigation (few-shot calibration).

---

## Methodology

### Approach

Build supervised ML models to predict (1) runtime_seconds and (2) peak memory using only FRESCO fields. Evaluate both within-site (time-based) and cross-site (train A → test B) with strict leakage avoidance. Quantify transfer gaps with bootstrap confidence intervals, then analyze domain shift and error slices to identify failure archetypes. Implement few-shot calibration on the target site to measure how quickly transfer can be recovered.

### Data Pipeline

1. **Data Acquisition**: Query required job attributes + aggregate performance metrics from FRESCO for Anvil/Conte/Stampede with documented time windows.
2. **Preprocessing**: Hard filters (valid start/end; runtime>0; required request fields present); define canonical peak-memory label; handle missingness with explicit indicators + documented imputation.
3. **Analysis**: Train baseline models (median, ElasticNet, tree-based gradient boosting) on log targets; run feature-group ablations (F0 vs F0+F1 vs F0+F1+F2).
4. **Validation**: Time-based within-site splits; cross-site transfer matrix; leakage checks; bootstrap CIs; error slicing (GPU vs non-GPU, queue/partition, size deciles, runtime deciles, I/O bins if available).

### Tools & Technologies

- **Languages**: Python
- **Key Libraries**: scikit-learn (baseline); optionally LightGBM/XGBoost/CatBoost if available/approved in environment
- **Compute Resources**: Local dev for prototyping; cluster execution as needed for full-scale runs

### Success Criteria

- Produce a reproducible Train×Test transfer matrix (runtime + memory) with bootstrap confidence intervals.
- Identify and quantify top error-driving slices (“archetypes”) and their contribution to total error.
- Demonstrate at least one mitigation (few-shot calibration) with an error-vs-label-fraction curve.

---

## Experiments

| ID | Title | Status | Key Result |
|----|-------|--------|------------|
| EXP-007 | Cross-cluster transfer matrix | Completed | Transfer can be competitive with timelimit; without timelimit, transfer R² < 0 in all cases. |
| EXP-008 | Transfer matrix w/ bootstrap CIs + pooled training | Completed | Conte “better-than-self” verified by CIs; pooled+clusterID improves Anvil to R²≈0.752. |
| EXP-009 | Conte anomaly resolution | Completed | Conte time split is extremely harsh vs random split (R² 0.11→0.47), indicating strong temporal non-stationarity. |

### Planned Experiments

- [x] **EXP-010**: Few-shot calibration on target site (error vs label fraction) *(Completed; see FIND-024)*
- [ ] **EXP-011**: Memory transfer baseline + missingness analysis

---

## Decision Log

Document all significant decisions and pivots in the research direction.

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2026-01-25 | Create PATH-C focused on cross-site runtime + peak-memory prediction | Matches stated research direction and paper-ready deliverables | Establishes consistent definitions and evaluation requirements |

---

## Findings Summary

Key discoveries from this research path. Full details in [Findings Log](../../Documentation/Findings_Log.md).

| Finding ID | Description | Publication Potential |
|------------|-------------|----------------------|
| FIND-020 | Cross-cluster transfer is viable *only* when timelimit is included; without timelimit, all transfer R² are negative. | High |
| FIND-021 | Anvil has the largest transfer gap; pooled training with cluster conditioning materially improves Anvil (R²≈0.752). | High |
| FIND-022 | Conte “better-than-self” anomaly is statistically real (Anvil/NONE→Conte/C R² CI > Conte/C→Conte/C R² CI). | Medium |
| FIND-023 | Conte’s time split is unusually harsh vs random split (strong temporal non-stationarity); support-matched transfer helps. | High |
| FIND-024 | Few-shot calibration under naive mixing is non-monotonic; some k values degrade performance (needs verification). | Medium |

---

## Progress Toward Publication

### Target Venue

- **Journal/Conference**: TBD (HPC/Systems/ML-for-Systems venue)
- **Submission Deadline**: TBD
- **Paper Type**: Full paper

### Paper Outline

1. **Introduction**: Not started
2. **Related Work**: Not started
3. **Methodology**: Not started
4. **Results**: Not started
5. **Discussion**: Not started
6. **Conclusion**: Not started

### Current Status

Runtime transfer baseline established (EXP-007/008) and Conte anomaly diagnosed (EXP-009). Next: mitigation via few-shot calibration (EXP-010) and extend to memory transfer (EXP-011).

---

## Next Steps

1. [ ] Create first experiment: data extraction + cleaning validation (EXP-XXX)
2. [ ] Define canonical peak-memory label based on available FRESCO fields (document in EXP)
3. [ ] Draft initial “papers to read” list in literature.md

---

## Notes

This path is scoped to use only FRESCO-provided fields and to prioritize reproducibility (queries, row-count funnels, leakage checks, fixed seeds, and stored artifacts). If user IDs are not linkable across sites, user-history features must be computed per-site only and reported explicitly as such.

### Hand-off Prompt (for another LLM agent)

Mission: Implement Option 2 end-to-end: build runtime + peak-memory predictors with strict leakage control and cross-site evaluation. Produce the deliverables (executive summary, figures, tables) and follow the data/query/cleaning/feature/model/evaluation/mitigation requirements defined for this path. Prioritize reproducibility and clear, publishable quantification (transfer gap + ablations + few-shot calibration).
