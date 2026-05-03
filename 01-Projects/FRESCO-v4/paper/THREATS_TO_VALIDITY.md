# Threats to Validity

**Last Updated**: 2026-03-13

This document catalogs known threats to the validity of v4 few-shot cross-cluster transfer claims. Each threat includes a description, severity assessment, and mitigations applied.

---

## 1. Measurement Non-Equivalence (Inherited from v3)

**Description**: Memory metrics are collected via different mechanisms across clusters. Conte uses cgroup-based accounting where `memory_includes_cache = true` (peak memory includes page cache), while Anvil uses a method where `memory_includes_cache = false`. This means identical workloads will report different peak memory values on different clusters, and the difference is not a constant offset — it depends on the application's I/O behavior.

**Impact on few-shot**: Few-shot calibration (especially output recalibration: ŷ = a·f(x) + b) MAY learn to correct a systematic measurement shift if the shift is approximately linear across all jobs. However, if the shift is application-dependent (e.g., I/O-heavy jobs have larger cache inflation than compute-bound jobs), a linear correction will not suffice, and residual miscalibration will persist.

**Severity**: High. This is the most fundamental threat to cross-cluster memory comparisons.

**Mitigations**:
- Provenance metadata (`memory_includes_cache`, `memory_collection_method`) is recorded per cluster so downstream consumers can assess comparability.
- Regime matching restricts to jobs with similar characteristics, potentially reducing the variance of the measurement shift within a regime.
- We report calibration slope and intercept explicitly so readers can assess the magnitude of the learned correction.
- Future work: non-linear calibration (e.g., quantile mapping) may better handle application-dependent shifts.

---

## 2. Temporal Drift

**Description**: The clusters span different eras — Conte (2015) vs Anvil (2022). Workloads, software stacks, user behaviors, and compiler optimizations have evolved over 7 years. Differences between clusters conflate hardware/measurement differences with temporal evolution of the HPC workload landscape.

**Impact on few-shot**: The calibration function g learned from N target examples captures the current state of the target cluster. If the target workload distribution shifts after calibration (e.g., new applications deployed, user behavior changes), the calibration may degrade without re-collection.

**Severity**: Medium. Temporal drift is real but partially mitigated by the fact that few-shot calibration can be cheaply re-collected.

**Mitigations**:
- We acknowledge that cross-cluster differences include temporal confounding and do not claim to isolate hardware-only effects.
- Few-shot calibration is explicitly framed as a periodic recalibration procedure, not a one-time transfer.
- Timestamps are preserved in the data, enabling future temporal stratification analyses.

---

## 3. Covariate Shift

**Description**: Even within the matched `hardware_cpu_standard` regime and after propensity filtering, a domain classifier achieves AUC ≈ 0.93 (from v3 EXP-001/002). This means the 5-feature set alone can distinguish clusters with high accuracy, indicating substantial residual distributional differences.

**Impact on few-shot**: High domain classifier AUC means the source model f was trained on a different feature distribution than the target. Calibration strategies that only adjust the output (Strategy 1: OLS) may underperform strategies that can reweight features (Strategy 2: fine-tuning, Strategy 3: stacking).

**Severity**: Medium-High. This is the primary motivation for few-shot calibration rather than zero-shot transfer.

**Mitigations**:
- Regime matching and propensity filtering reduce (but do not eliminate) covariate shift.
- We report domain classifier AUC for all experiments so readers can assess the severity.
- Multiple calibration strategies are compared, including those that can address feature-level shift (fine-tuning, stacking).
- We explicitly test the effect of regime matching in the ablation experiment (E2).

---

## 4. Hidden Confounding

**Description**: Application type, user expertise, batch scheduling policy, and queue configuration are unobserved in the feature set. These factors may drive both resource usage and feature values, creating confounding that no amount of feature-level matching can resolve.

**Impact on few-shot**: If hidden confounders create different f(x) → y mappings in source and target (beyond what's captured by observed features), calibration will learn an average correction that may be inaccurate for specific subpopulations.

**Severity**: Medium. Standard in observational studies; partially mitigated by the large sample sizes and Ridge regularization.

**Mitigations**:
- We do not claim causal identification of cluster effects, only predictive transfer.
- Regime matching reduces observable confounding.
- Stratified calibration sampling helps ensure the calibration set covers the target distribution.
- Future work: incorporating queue/application metadata where available.

---

## 5. Sample Selection Bias for Calibration Set

**Description**: The N calibration examples are drawn from the target cluster by stratified random sampling. However, the target dataset itself may not be representative of future workloads (survivorship bias: only completed jobs are included; failed or killed jobs have different memory profiles).

**Impact on few-shot**: If the calibration set is unrepresentative of the evaluation set (or future deployment), the learned calibration function g will be biased. At small N, a single outlier in the calibration set can substantially shift (a, b) in output recalibration.

**Severity**: Medium. Stratified sampling mitigates but does not eliminate this threat.

**Mitigations**:
- Stratified sampling on `workload_regime` ensures coverage of major workload classes.
- Multiple seeds (default: 3) are used to assess sensitivity to the specific calibration draw.
- We report variance across seeds to quantify instability from sample selection.
- At small N, we recommend output recalibration (2 parameters) over stacking (d+1 parameters) to reduce sensitivity to individual examples.

---

## 6. Overfitting to Calibration Set

**Description**: At small N (10–25), calibration parameters are estimated from very few examples. Output recalibration learns 2 parameters from N points; stacking learns d+1 parameters from N points. With the 5-feature set (d = 5), stacking has 6 parameters for potentially 10 examples — a dangerous ratio.

**Impact on few-shot**: Overfitting the calibration function to the N examples will produce optimistic calibration metrics on T_N but poor generalization to T \ T_N. This is why we never evaluate on the calibration set.

**Severity**: Medium-High at small N; Low at large N.

**Mitigations**:
- Strict train/evaluation separation: calibration set is never used for evaluation metrics.
- Ridge regularization with cross-validated α for all Ridge-based strategies.
- Bootstrap CI on the evaluation set captures the downstream effect of calibration overfitting (wider CI when calibration is unstable).
- We report performance across 3 seeds; high variance across seeds at small N is a signal of overfitting.
- We recommend output recalibration (2 DoF) over stacking (6 DoF) at very small N.

---

## 7. Baseline Fairness

**Description**: The target-only baseline (Strategy 4) trains Ridge on N examples with d = 5 features. At small N (e.g., N = 10), this is an underdetermined system regularized by Ridge. The comparison between transfer strategies (which leverage source data) and the target-only baseline is inherently unfair at small N in favor of transfer.

**Impact on few-shot**: At small N, the target-only baseline will appear weak, potentially overstating the value of transfer. At large N (e.g., N = 500), the baseline may match or exceed transfer strategies, correctly showing diminishing returns from source data.

**Severity**: Low. This is not a bias in the evaluation but a real phenomenon — transfer is most valuable when target labels are scarce.

**Mitigations**:
- We use strong Ridge regularization (large α, selected by LOO-CV) for the target-only baseline at small N.
- We explicitly discuss the asymmetry in the paper and frame the target-only baseline as a reference point, not a straw man.
- The full-target upper bound (Ridge on full T train split) provides the fair comparison for "how good can target-only be with enough data?"
- We report the target-only baseline at every N so readers can see the convergence trajectory.

---

## Summary of Mitigations

| Threat | Primary Mitigation | Detection Method |
|--------|-------------------|------------------|
| Measurement non-equivalence | Provenance metadata, regime matching | Calibration slope ≠ 1 in residual analysis |
| Temporal drift | Acknowledge confounding, periodic recalibration | Timestamp-stratified subgroup analysis |
| Covariate shift | Regime matching, propensity filtering | Domain classifier AUC |
| Hidden confounding | Predictive (not causal) framing | Residual analysis by subgroup |
| Sample selection bias | Stratified sampling, multiple seeds | Seed variance |
| Calibration overfitting | Ridge regularization, strict separation | Bootstrap CI width, seed variance |
| Baseline fairness | Strong regularization, explicit discussion | Convergence at large N |
