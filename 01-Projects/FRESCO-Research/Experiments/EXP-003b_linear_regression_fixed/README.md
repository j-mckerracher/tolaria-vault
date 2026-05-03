# Experiment: EXP-003b - Linear Regression (Fixed + Ablation)

**Status**: Created  
**Date Created**: 2026-01-31  
**Last Updated**: 2026-01-31  
**Research Path**: PATH-B (Performance Prediction)  
**Directory**: Experiments/EXP-003b_linear_regression_fixed

---

## Objective

Fix the source_token extraction bug from EXP-003 (Conte was missing) and conduct rigorous ablation studies to understand feature contributions to runtime prediction.

## Changes from EXP-003

1. **Bug Fix**: Extract source_token from filename (not jid) to correctly identify Conte cluster
2. **Ablation**: Train models with and without timelimit to measure true predictive contribution
3. **Baselines**: Compare against trivial predictors (median runtime, timelimit-only)
4. **Better Metrics**: Report median-based metrics (MdAE, MdAPE) alongside mean metrics

## Hypothesis

**Primary**: After fixing source_token, all 3 clusters (Stampede, Conte, Anvil) will show in results.

**Secondary**: Removing timelimit will significantly reduce R², revealing that timelimit encodes "user knows best" rather than system-derived insights.

**Null**: System features (ncores, nhosts, wait_sec) provide no predictive value beyond timelimit.

---

## FRESCO Data Specification

| Parameter | Value |
|-----------|-------|
| Cluster(s) | All (S=Stampede, C=Conte, NONE=Anvil) |
| Date Range | Full dataset (2013-2023) |
| Source Token | Extracted from **filename** (e.g., `00_C.parquet` → `C`) |

---

## Methodology

### Models to Train

For each cluster, train 3 model variants:

| Variant | Features | Purpose |
|---------|----------|---------|
| Full | ncores, nhosts, log_timelimit, log_wait_sec, month dummies | Original model |
| No-Timelimit | ncores, nhosts, log_wait_sec, month dummies | Ablation: what do system features add? |
| Timelimit-Only | log_timelimit | Baseline: how good is user estimate alone? |

### Baselines

| Baseline | Description |
|----------|-------------|
| Median | Predict median log(runtime) per cluster |
| Mean | Predict mean log(runtime) per cluster |

### Evaluation Metrics

| Metric | Description |
|--------|-------------|
| R² | Variance explained |
| MAE (log) | Mean Absolute Error on log scale |
| MdAE (log) | **Median** Absolute Error on log scale |
| RMSE (log) | Root Mean Squared Error |
| MAPE | Mean Absolute Percentage Error (original scale) |
| MdAPE | **Median** Absolute Percentage Error |

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

- **Script(s)**: `scripts/exp003b_linear_regression.py`
- **SLURM Job**: `scripts/exp003b.slurm`

---

## Supercomputer Job

| Field | Value |
|-------|-------|
| Cluster | Gilbreth |
| Partition | (auto-selected via sbbest) |
| Nodes | 1 |
| CPUs | 16 |
| Memory | 64GB |
| Walltime | 04:00:00 |

---

## Execution Log

| Date | Action | Result/Notes |
|------|--------|--------------|
| 2026-01-31 | Created | Fixed EXP-003 bugs, added ablation |

---

## Output Artifacts (Expected)

| Artifact | Path | Description |
|----------|------|-------------|
| Metrics (all variants) | `results/metrics_comparison.csv` | R², MAE, MdAE per cluster/variant |
| Coefficients | `results/coefficients.csv` | Feature importance |
| Ablation summary | `results/ablation_summary.csv` | With vs without timelimit |
| Diagnostic plots | `results/figures/` | Actual vs predicted, residuals |

---

## Dependencies

- None (reads raw FRESCO data directly)

---

## Notes

- EXP-003 had Conte missing due to extracting source_token from jid (which lacks `_C` suffix)
- GPT-5.2 review noted timelimit dominance may just reflect "users estimate well"
- Ablation will reveal true contribution of system features
