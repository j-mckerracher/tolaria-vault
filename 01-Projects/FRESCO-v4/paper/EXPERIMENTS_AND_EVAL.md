# Experiments & Evaluation Protocol (Publication Required)

**Last Updated**: 2026-03-13

## Goals
1. Reproduce the v3 zero-shot transfer failure as a baseline (E0).
2. Quantify how few-shot calibration recovers prediction quality as a function of N.
3. Compare four calibration strategies across the sample efficiency curve.
4. Determine the minimum N for practical deployment at new HPC sites.

---

## Standard Evaluation Protocol
- **Fixed seeds**: all random operations (calibration sampling, bootstrap) use recorded seeds. Default seeds: {42, 123, 456}.
- **Bootstrap confidence intervals**: 1000 resamples of the evaluation set for all reported metrics.
- **Stratified target sampling**: calibration set T_N is drawn by stratified random sampling (stratified on `workload_regime` when available) to ensure representativeness.
- **Pre-registered feature set**: the 5-feature set (ncores, nhosts, timelimit_sec, runtime_sec, runtime_fraction) is fixed before experiments begin.

---

## Canonical Split Protocol

### Within Source (for base model training)
- **80/20 random split**: 80% of source data for training the base model f, 20% for source validation.
- Split is deterministic given the seed and recorded in the run config.
- Source validation set is used only for hyperparameter selection (Ridge α), never for evaluation of transfer quality.

### Within Target (for calibration and evaluation)
- **N examples for calibration**: drawn by stratified random sampling from the full target dataset.
- **|T| − N examples for evaluation**: all remaining target examples form the held-out evaluation set.
- Evaluation metrics are computed exclusively on the evaluation set.
- The calibration set is never used for evaluation (strict separation).

### Important: No Time-Based Split for Target
Unlike v3's within-cluster experiments (which used time-based splits), few-shot experiments use random splits for the target calibration/evaluation partition. Rationale: the few-shot setting simulates a new site collecting a small representative sample, not a temporal forecasting task.

---

## Required Experiments

### E0: Reproduce v3 Zero-Shot Negatives
**Purpose**: Confirm that zero-shot cross-cluster transfer fails, establishing the baseline that motivates few-shot calibration.

- Reproduce v3 EXP-001 (Conte → Anvil zero-shot) and EXP-002 (Anvil → Conte zero-shot).
- Use identical regime matching, feature set, and evaluation protocol from v3.
- **Expected outcome**: R² < 0.3, calibration slope ≠ 1, large residual bias.
- **Reporting**: R², MAE(log), calibration slope, domain AUC, overlap coverage.

### E1: Few-Shot Sweep
**Purpose**: Systematic evaluation of all calibration strategies across the sample efficiency curve.

- **Design**: 4 strategies × 6 N-values × 3 seeds = **72 runs** per cluster pair.
- **N values**: {10, 25, 50, 100, 250, 500}.
- **Strategies**: output recalibration (OLS), fine-tuning (weighted Ridge), stacking, target-only baseline.
- **Per-run outputs**:
  - Calibration parameters (a, b for OLS; α, coefficients for Ridge variants).
  - Evaluation metrics: R², MAE(log), bootstrap 95% CI, calibration slope.
  - Zero-shot baseline comparison (from E0).
  - Target-only baseline at same N.
- **Primary analysis**:
  - Sample efficiency curves: R² vs N and MAE(log) vs N for each strategy.
  - Break-even N: smallest N where few-shot ≥ full-target upper bound (within CI).
  - Strategy ranking at each N.
  - Seed variance analysis (stability).

### E2: Regime Matching Ablation
**Purpose**: Determine whether regime matching helps at all N, or only at small N.

- **Design**: repeat E1 at key N-values {25, 100, 500} with and without regime matching.
- **Without regime matching**: use full source and target datasets (no propensity filter, no hardware regime restriction).
- **Comparison**: Δ(R²) and Δ(MAE) between matched and unmatched at each N.
- **Expected finding**: regime matching helps most at small N where calibration has fewer examples to learn the shift.

### E3: Second Cluster Pair (Conditional)
**Purpose**: Test generalizability of findings across a different cluster pair.

- **Prerequisite**: domain classifier propensity overlap exists for the second pair. Check overlap for Conte ↔ Stampede or Stampede ↔ Anvil.
- **Design**: if overlap is sufficient (coverage ≥ 20% of both clusters), repeat E1 at key N-values {25, 100, 500}.
- **If overlap is insufficient**: document the failure and explain why (e.g., disjoint hardware regimes, no matched partitions).

---

## Reporting Requirements

### Per-Result Entry (Table Row)
Every few-shot result must report all of the following:

| Field | Description |
|-------|-------------|
| `cluster_pair` | Source → Target (e.g., Conte → Anvil) |
| `strategy` | Calibration strategy name |
| `N` | Number of calibration examples |
| `seed` | Random seed used for calibration sampling |
| `regime` | Matched / Unmatched |
| `R²` | On held-out evaluation set |
| `R²_CI` | Bootstrap 95% CI |
| `MAE_log` | On held-out evaluation set |
| `MAE_log_CI` | Bootstrap 95% CI |
| `cal_slope` | Calibration slope (predicted vs actual) |
| `cal_params` | Strategy-specific parameters (a, b or α, etc.) |
| `zero_shot_R²` | R² of zero-shot baseline (from E0) |
| `target_only_R²` | R² of target-only baseline at same N |
| `full_target_R²` | R² of full-target upper bound |
| `n_eval` | Size of evaluation set |
| `n_source_train` | Size of source training set |
| `overlap_coverage` | Fraction retained after propensity filter |

### Per-Experiment Summary
Each experiment also produces:
- Sample efficiency curve figure (R² and MAE(log) vs N, all strategies, with CI bands).
- Strategy comparison table at each N (mean ± std across seeds).
- Break-even N identification (with CI).

---

## Expected Outputs

### Figures
1. **Sample efficiency curve** (primary figure): R² vs N for all 4 strategies + zero-shot + full-target. Error bars from bootstrap CI. One panel per cluster pair.
2. **MAE(log) efficiency curve**: same layout as above but for MAE(log).
3. **Strategy comparison heatmap**: strategies × N-values, colored by R², annotated with CI width.
4. **Regime matching ablation**: paired bar chart (matched vs unmatched) at key N values.

### Tables
1. **Full results table**: all 72+ runs with complete reporting fields (see above).
2. **Strategy summary table**: mean R² ± std across seeds, per strategy × N.
3. **Break-even analysis**: for each strategy, the smallest N where R² ≥ full-target R² − CI width.

### Artifacts per Run
- Run config JSON
- Input/output manifests
- Calibration parameters (serialized)
- Evaluation metrics (CSV)
- Bootstrap samples (for reproducible CI computation)
- Environment lock file
