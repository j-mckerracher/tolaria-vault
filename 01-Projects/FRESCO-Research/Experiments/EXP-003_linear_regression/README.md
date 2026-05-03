# Experiment: EXP-003 - Linear Regression Baseline for Runtime Prediction

**Status**: Completed (Superseded by EXP-003b; cluster parsing bug)  
**Date Created**: 2026-01-31  
**Last Updated**: 2026-02-01  
**Research Path**: PATH-B (Performance Prediction)  
**Directory**: Experiments/EXP-003_linear_regression

---

## Objective

Establish a baseline linear regression model for predicting job runtime using pre-execution features. This serves as a benchmark for more complex models (EXP-004: Transformer).

## Hypothesis

**Prediction**: A linear model using job request features (ncores, nhosts, timelimit, queue) can explain 20-40% of runtime variance (R² = 0.2-0.4). Timelimit will be the strongest predictor.

**Null Hypothesis**: Pre-execution features have no linear relationship with runtime (R² ≈ 0).

---

## FRESCO Data Specification

| Parameter | Value |
|-----------|-------|
| Cluster(s) | All (S=Stampede, C=Conte, NONE=Anvil) |
| Date Range | Full dataset (2013-2023) |
| Total Jobs | ~7.3M (from EXP-001 job_rollup) |
| Input | EXP-001 `job_rollup/` partitioned parquet |

### Target Variable

- `runtime_sec` (log-transformed due to heavy skew)

### Features (Pre-Execution Only)

These features are known before the job runs:

| Feature | Type | Description |
|---------|------|-------------|
| `ncores` | Numeric | Number of cores requested |
| `nhosts` | Numeric | Number of nodes requested |
| `timelimit` | Numeric | Requested walltime (seconds) |
| `wait_sec` | Numeric | Queue wait time (proxy for system load) |
| `source_token` | Categorical | Cluster identifier (S/C/NONE) |
| `start_month` | Categorical | Month (1-12, seasonality) |
| `start_hour` | Numeric | Hour of day (if available) |

**Excluded** (post-execution / leakage):
- `value_cpuuser`, `value_memused`, etc. (runtime metrics)
- `exitcode` (outcome)

---

## Methodology

### Approach

1. Train/test split by time (80/20) to avoid temporal leakage
2. Per-cluster models + global model comparison
3. Log-transform runtime for better linearity
4. One-hot encode categorical features

### Algorithm/Model

- **Type**: Supervised Regression
- **Algorithm**: Ridge Regression (scikit-learn)
- **Why**: Simple baseline, handles multicollinearity, interpretable coefficients

### Evaluation Metrics

| Metric | Description |
|--------|-------------|
| R² | Variance explained |
| MAE | Mean Absolute Error (in log-seconds) |
| RMSE | Root Mean Squared Error |
| MAPE | Mean Absolute Percentage Error (on original scale) |

### Train/Test Split

- **Training**: Jobs from first 80% of time range per cluster
- **Testing**: Jobs from last 20% of time range per cluster
- **Rationale**: Simulates real-world deployment (predict future from past)

---

## Reproducibility

### Environment

| Component | Version |
|-----------|---------|
| Python | 3.10+ |
| scikit-learn | ≥1.3 |
| pandas | ≥2.0 |
| duckdb | ≥0.9 |

### Code

- **Script(s)**: `scripts/exp003_linear_regression.py`
- **SLURM Job**: `scripts/exp003.slurm`

### Random Seeds

- Seed: 42 (for Ridge CV)

---

## Supercomputer Job

| Field | Value |
|-------|-------|
| Cluster | Gilbreth |
| Scheduler | SLURM |
| Partition | (check traffic) |
| Nodes | 1 |
| CPUs | 16 |
| Memory | 64GB |
| Walltime | 02:00:00 |

---

## Execution Log

| Date | Action | Result/Notes |
|------|--------|--------------|
| 2026-01-31 | Created | Designed experiment for PATH-B |
| 2026-02-01 | Run (attempt 1) | Failed: job_rollup path missing on Gilbreth (`No files found .../EXP-001.../job_rollup/**/*.parquet`) |
| 2026-02-01 | Run (attempt 2) | Ran on raw FRESCO; clusters detected: S and NONE only (Conte missing due to source_token parsing from `jid`; see FIND-011, fixed in EXP-003b). |

---

## Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Model coefficients | `results/coefficients.csv` | Feature importance (S+NONE only; do not treat NONE as Anvil) |
| Metrics | `results/metrics.csv` | R²/MAE/etc. (S+NONE only; superseded by EXP-003b) |
| Predictions | `results/predictions.parquet` | Test set predictions (S+NONE only; superseded by EXP-003b) |
| Residual plots | `results/figures/` | Diagnostics (S+NONE only) |

**Warning**: EXP-003 is superseded by EXP-003b due to incorrect cluster identification from `jid` (Conte missing / misclassified). Use EXP-003b for any publication-facing numbers.

---

## Dependencies

- **EXP-001**: Requires `job_rollup/` output

---

## Notes

- Per FIND-001, clusters have very different workload patterns—per-cluster models may outperform global model
- Conte has ncores ≈ 1 (serial jobs), so ncores may not be predictive there
- Consider adding queue/account as categorical features if cardinality is manageable
