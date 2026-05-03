# Paper Outline: How Many Labels? Sample-Efficient Cross-Cluster HPC Memory Prediction

**Last Updated**: 2026-03-13

## Title (Working)
How Many Labels? Sample-Efficient Cross-Cluster HPC Memory Prediction

## Abstract
- Motivation: HPC centers need portable memory-usage models, but cross-cluster transfer is unreliable due to measurement and workload shift.
- Gap: v3 demonstrated that zero-shot transfer fails systematically. The open question is: how many labeled target examples suffice?
- Contribution: systematic few-shot calibration framework — four strategies, sample efficiency analysis, and practical deployment guidance.
- Results: few-shot calibration with as few as N target labels recovers competitive accuracy; we identify the break-even N and recommend deployment strategies.

## §1 Introduction
- Why cross-cluster memory prediction matters for HPC resource management and scheduling.
- v3 established that zero-shot transfer fails (calibration slope ≠ 1, residual bias, covariate shift even after regime matching).
- Few-shot transfer is the practical middle ground: collect a small labeled calibration set at the target site and adapt.
- **Contributions**:
  1. Systematic evidence that zero-shot cross-cluster transfer fails (reproducing and extending v3 EXP-001/002).
  2. Four few-shot calibration strategies with formal definitions and comparative evaluation.
  3. Sample efficiency analysis: how prediction quality scales with N labeled target examples.
  4. Practical deployment guidance: minimum N for operational use at new HPC sites.

## §2 Background & Dataset
- FRESCO overview: large-scale HPC workload dataset with scheduler logs and telemetry.
- Clusters:
  - **Conte** (Purdue, 2015): older hardware, cgroup-based memory accounting.
  - **Stampede** (TACC): large-scale, different scheduling policies.
  - **Anvil** (Purdue, 2022): modern A100 nodes, updated memory telemetry.
- Prior work: v1 (single-cluster), v2 (multi-cluster extraction), v3 (unified schema + regime matching + zero-shot transfer characterization).
- The measurement non-equivalence problem: `memory_includes_cache` differs across clusters, making raw memory values incomparable.

## §3 Problem Formulation
- **Setting**: source cluster S (fully labeled), target cluster T (N labeled for calibration, |T|−N for evaluation).
- **Goal**: learn a predictor that generalizes to T using S's model and N target calibration labels.
- **Why zero-shot fails**: reference v3 evidence (EXP-001/002). Even with regime matching, domain AUC ≈ 0.93 indicates features encode cluster identity. Calibration slope ≠ 1 and residual bias persist.
- **Few-shot formulation**: train f on S, then learn calibration function g such that g∘f(x) ≈ y_target using N labeled pairs from T. Evaluate on T \ calibration set.

## §4 Methods
- **Pipeline** (inherited from v3): extraction → transformation → schema enforcement → validation → output. Unified parquet shards with provenance metadata.
- **Regime matching**: `hardware_cpu_standard` regime, domain classifier propensity overlap in [0.2, 0.8], 5-feature set (ncores, nhosts, timelimit_sec, runtime_sec, runtime_fraction).
- **Calibration strategies**:
  1. **Output recalibration**: y_cal = a·f(x) + b, fitted by OLS on N calibration pairs. Corrects systematic bias and scale.
  2. **Fine-tuning**: retrain Ridge on S ∪ T_N with sample weights (upweight target). Allows feature reweighting.
  3. **Stacking**: Ridge on [f(x), x] using N calibration pairs. Combines source prediction with raw features.
  4. **Target-only baseline**: Ridge trained only on T_N (no source information). Lower bound on what N labels alone can achieve.
- **Evaluation metrics**: R², MAE(log), bootstrap 95% CI, calibration slope.

## §5 Experimental Design
- **Sweep parameters**:
  - N ∈ {10, 25, 50, 100, 250, 500} (calibration set sizes)
  - 4 strategies × 6 N-values × 3 seeds = 72 runs per cluster pair
- **Evaluation protocol**: stratified sampling for calibration set, fixed seeds, bootstrap confidence intervals.
- **Baselines**:
  - Zero-shot (N = 0): v3 regime-matched transfer, no target labels.
  - Target-only at each N: Ridge on T_N alone.
  - Full-target upper bound: Ridge on full T train split.
- **Experiments**:
  - E0: Reproduce v3 zero-shot negatives (EXP-001/002).
  - E1: Full few-shot sweep (72 runs).
  - E2: Regime matching ablation (matched vs unmatched at key N values).
  - E3: Second cluster pair (if overlap exists).

## §6 Results
- **Sample efficiency curves**: R² and MAE(log) vs N for each strategy, with bootstrap CIs.
- **Strategy comparison**: which strategy wins at each N? Does the winner change with N?
- **Break-even analysis**: smallest N where few-shot matches or exceeds full-target baseline within CI.
- **Stability analysis**: variance across seeds. Do strategies differ in stability?
- **Regime matching effect**: does regime matching help at all N, or only at small N?

## §7 Discussion
- When few-shot suffices: scenarios where small N (e.g., 25–50) achieves near-full-target quality.
- When it doesn't: if calibration shift is non-linear or application-dependent, linear recalibration may plateau.
- Practical guidance for HPC sites: recommended strategy and minimum N for deployment.
- Cost–benefit: labeling cost (running N representative jobs to completion) vs prediction quality gain.

## §8 Threats to Validity
- Measurement non-equivalence: `memory_includes_cache` differs; few-shot MAY learn this shift, but application-dependent shifts may resist linear correction.
- Temporal drift: 2015 vs 2022 workloads differ beyond memory semantics.
- Covariate shift: even in matched regime, features encode cluster identity (domain AUC ≈ 0.93).
- Hidden confounding: application type and user behavior are unobserved.
- Sample selection bias: N calibration examples may not represent full target distribution.
- Overfitting at small N: calibration parameters (a, b) may overfit with few examples.
- Baseline fairness: target-only baseline disadvantaged at small N.
- See `THREATS_TO_VALIDITY.md` for full treatment.

## §9 Reproducibility
- All results reproducible from pinned code commit, config files, and environment locks.
- Every run produces manifests (input/output), run metadata, and validation reports.
- Dataset available on Gilbreth at `/depot/sbagchi/data/josh/FRESCO/chunks-v3/`.
- See `ARTIFACTS_AND_REPRO_GUIDE.md` for step-by-step instructions.

## §10 Conclusion
- Few-shot calibration is a practical and effective strategy for cross-cluster HPC memory prediction.
- Key practical takeaways: recommended strategy, minimum N, deployment workflow.
- Future work: non-linear calibration, active selection of calibration examples, extension to additional clusters and metrics.
