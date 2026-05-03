# FRESCO v4 Few-Shot Cross-Cluster Transfer Methodology

**Last Updated**: 2026-03-13

## 1. Problem Formulation

### Setting
- **Source cluster** (e.g., Anvil): Fully labeled. All jobs have observed `peak_memory_fraction`.
- **Target cluster** (e.g., Conte): A small number **N** of jobs are labeled for calibration; the remaining target jobs form the evaluation set.

### Goal
Predict `peak_memory_fraction` on the target cluster by leveraging a model trained (primarily) on the source cluster, using N labeled target observations to calibrate predictions.

### Motivation
FRESCO v3 demonstrated that zero-shot cross-cluster transfer of memory usage predictions is unstable across different sampled universes. The primary failure mode is **source-centered prediction collapse**: the source model predicts source-like memory fractions for target jobs, failing to capture systematic differences in measurement semantics (e.g., `memory_includes_cache` differs between Anvil and Conte/Stampede). Few-shot calibration provides direct signal about the target distribution, enabling correction of this systematic bias.

## 2. Target Label Sampling

### Sampling procedure
1. Start with the **overlap cohort**: target jobs whose propensity score falls within the overlap band (e.g., [0.2, 0.8]).
2. Compute `peak_memory_fraction` quartile bins (Q1-Q4) within the overlap cohort.
3. Sample N jobs **stratified by quartile** (equal allocation per bin, with remainders assigned round-robin to lower bins).
4. Sampling is **without replacement** using a fixed seed (`few_shot.target_label_seed`).
5. The N sampled jobs form the **calibration set**.
6. All remaining overlap cohort jobs form the **evaluation set**.

### Stratification rationale
Stratified sampling ensures the calibration set covers the full range of the target label distribution. Without stratification, random sampling at small N risks concentrating all calibration points in a narrow band, producing poor calibration estimates.

### Determinism
Given the same overlap cohort, N, and seed, the calibration/evaluation split is fully deterministic. The sampled job IDs must be recorded in `manifests/calibration_job_ids.json` for reproducibility.

When comparing label-sampling seeds across reruns, keep `data_seed` and `split.seed` fixed so only `few_shot.target_label_seed` changes.

## 3. Calibration Strategies

### 3.1 Output Recalibration (`output_recal`)

**Concept**: Train the source model normally on source data. Generate predictions for the N calibration target jobs. Fit a linear correction mapping predicted values to actual values.

**Procedure**:
1. Train Ridge regression on source training data using the safe feature set.
2. Generate source model predictions for the N calibration jobs: `y_pred_cal`.
3. Observe the true labels for the N calibration jobs: `y_true_cal`.
4. Fit OLS linear regression: `y_true = a * y_pred + b` on the N (predicted, actual) pairs.
5. Apply the correction to all target predictions: `y_corrected = a * y_pred + b`.

**Bayesian variant**: Instead of unconstrained OLS, place priors on the calibration parameters:
- `a ~ N(1, 0.5)` (prior belief: slope near identity)
- `b ~ N(0, 0.5)` (prior belief: intercept near zero)

The Bayesian variant provides regularization at very small N (e.g., N < 10) where OLS may overfit. Configure via `few_shot.recal_prior`:
```json
{
  "a_mean": 1.0, "a_std": 0.5,
  "b_mean": 0.0, "b_std": 0.5
}
```

**Strengths**: Simple, interpretable, minimal risk of catastrophic failure. Only two parameters to estimate.
**Weaknesses**: Assumes the source model's prediction errors are linearly related to the true values. Cannot correct feature-level misalignment.

### 3.2 Fine-Tune (`fine_tune`)

**Concept**: Concatenate source training data with the N labeled target jobs and re-fit the model, upweighting target rows to compensate for the source/target size imbalance.

**Procedure**:
1. Construct training set: `X_train = concat(X_source_train, X_target_cal)`.
2. Construct label vector: `y_train = concat(y_source_train, y_true_cal)`.
3. Construct sample weights: source rows get weight 1.0; target rows get weight `w = len(X_source_train) / N`.
4. Fit weighted Ridge regression on the combined training set.
5. Generate predictions for all target evaluation jobs.

**Weight rationale**: The weight `w = len(source_train) / N` ensures that the total influence of the N target rows equals the total influence of the source rows. This can be adjusted via `few_shot.target_weight`.

**Strengths**: Allows the model to jointly learn from both domains. The feature-level coefficients shift toward the target distribution.
**Weaknesses**: At very small N with large weight, the model may overfit to the few target examples. The source data still dominates feature-level patterns.

### 3.3 Stacked (`stacked`)

**Concept**: Use the source model's prediction as an additional feature in a second-stage model trained only on the N target calibration jobs.

**Procedure**:
1. Train the source Ridge model on source training data.
2. Generate source model predictions for the N calibration jobs and for all target evaluation jobs.
3. Construct second-stage features: `X_stage2 = [source_pred, original_features]`.
4. Train second-stage Ridge regression on the N calibration jobs using `X_stage2` as input and `y_true_cal` as labels.
5. Apply the second-stage model to generate final predictions for all target evaluation jobs.

**Strengths**: The second-stage model can learn a nonlinear combination of source predictions and raw features. More flexible than output recalibration.
**Weaknesses**: More parameters to estimate from N examples. Risk of overfitting at small N due to the expanded feature space.

### 3.4 Target-Only (`target_only`)

**Concept**: Train a model using only the N target calibration jobs. No source data is used.

**Procedure**:
1. Train Ridge regression on the N calibration jobs using the safe feature set.
2. Generate predictions for all target evaluation jobs.

**Purpose**: This is a **baseline**, not a recommended strategy. It answers: "How well can we do with N target labels alone, ignoring the source?" Comparing few-shot+source strategies against target-only reveals whether leveraging source data actually helps.

**Strengths**: No domain shift issues. The model is native to the target distribution.
**Weaknesses**: At small N, severely underpowered. Cannot learn complex feature-label relationships.

### 3.5 Zero-Shot (`zero_shot`)

**Concept**: Train on source data only, predict on target with no calibration. Equivalent to the v3 baseline.

**Procedure**:
1. Train Ridge regression on source training data.
2. Generate predictions for all target overlap cohort jobs (no calibration split needed).

**Purpose**: Establishes the N=0 reference point. All few-shot strategies should be compared against this baseline.

## 4. Evaluation Protocol

### Evaluation set definition
The evaluation set is **strictly the complement of the calibration set within the overlap cohort**:
```
evaluation_set = overlap_cohort - calibration_set
```

For the zero-shot baseline (N=0), the evaluation set is the entire overlap cohort.

### Key constraint: no calibration leakage
The N calibration labels must **NEVER** appear in the evaluation set. This is a hard constraint, not a guideline. Violation invalidates all reported metrics.

Verification: `validation/split_integrity_check.json` must confirm zero intersection between calibration job IDs and evaluation job IDs.

### Metrics
All metrics are computed on the evaluation set. The metric suite matches v3 for comparability:

| Metric | Description |
|--------|-------------|
| R-squared | Coefficient of determination |
| MAE(log) | Mean absolute error on log-transformed predictions/labels |
| MdAE(log) | Median absolute error on log-transformed predictions/labels |
| SMAPE | Symmetric mean absolute percentage error |
| Bias | Mean signed error (predicted - actual) |
| Calibration slope | Slope of actual vs. predicted OLS fit |
| Bootstrap 95% CI | Percentile bootstrap confidence intervals for R-squared (n_boot iterations) |

### Bootstrap procedure
1. Resample the evaluation set with replacement (n_boot times).
2. Compute each metric on each bootstrap sample.
3. Report the 2.5th and 97.5th percentiles as the 95% CI.

## 5. Sample Efficiency Analysis

### N-curve protocol
For each calibration strategy, sweep N across a range (e.g., N = 5, 10, 20, 50, 100, 200, 500) and plot:
- R-squared vs. N
- MAE(log) vs. N
- Calibration slope vs. N

### Break-even N
The **break-even N** is the smallest N at which a few-shot+source strategy (e.g., output_recal) achieves higher R-squared than the target-only baseline at the same N.

Below break-even N: the source model's inductive bias helps more than it hurts.
Above break-even N: having enough target data makes source data unnecessary.

### Reference lines
Each N-curve plot should include:
- **Zero-shot baseline** (horizontal line at N=0 R-squared)
- **Target-only curve** (R-squared vs. N using only target data)
- **Full-target upper bound** (horizontal line: R-squared using all available target data for training)

## 6. Experimental Design Recommendations

### Recommended initial experiment matrix

| Source | Target | Regime | N values | Strategies |
|--------|--------|--------|----------|------------|
| Anvil | Conte | hardware_cpu_standard | 5, 10, 20, 50, 100, 200 | all five |
| Anvil | Conte | hardware_cpu_standard | 5, 10, 20, 50, 100, 200 | all five (second frozen universe) |

### Seed management
- `data_seed`: controls source/target data sampling when raw rows are loaded
- `split.seed`: controls the source train/test split
- `random_seed`: controls model/bootstrap/general RNG that is not part of data sampling
- `few_shot.target_label_seed`: controls which N target jobs are sampled for calibration
- Run each (N, strategy) combination with multiple `target_label_seed` values while holding `data_seed` and `split.seed` fixed to assess label-sampling sensitivity on a stable sampled universe

### Frozen overlap cohort
Reuse the overlap cohort from a fixed Phase 2 run (e.g., EXP-062 or EXP-070 from v3). Do not re-run Phase 2 for each few-shot experiment. This ensures all strategies and N values are evaluated on exactly the same target population.

## 7. Relationship to v3

### What v4 inherits from v3
- Dataset (chunks-v3)
- Feature engineering pipeline (analysis-time derivation)
- Regime matching framework (Phase 2)
- Base model architecture (Ridge regression)
- Evaluation metric suite
- Frozen sampling plans and overlap cohorts

### What v4 adds
- Target label sampling (Phase 3.5: calibration set construction)
- Four calibration strategies (output_recal, fine_tune, stacked, target_only)
- N-curve analysis framework
- Break-even N identification
- Calibration parameter logging and validation
