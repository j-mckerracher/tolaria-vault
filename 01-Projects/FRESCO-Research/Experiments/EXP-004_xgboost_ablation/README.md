# Experiment: EXP-004 - XGBoost Ablation for Runtime Prediction

**Status**: Created  
**Date Created**: 2026-01-31  
**Last Updated**: 2026-01-31  
**Research Path**: PATH-B (Performance Prediction)  
**Directory**: Experiments/EXP-004_xgboost_ablation

---

## Objective

Test whether nonlinear models (XGBoost) can recover predictive signal from non-timelimit features that linear models missed. This addresses the key question: is timelimit dominance a limitation of linear models, or is it fundamental to the feature set?

## Hypothesis

**Primary**: XGBoost on no_timelimit features will achieve higher R² than Ridge Regression (0.15 for Stampede, -0.03 for Conte), potentially revealing nonlinear interactions.

**Secondary**: If XGBoost also fails on no_timelimit features, this confirms timelimit truly encodes most runtime information and richer features are needed.

---

## Methodology

### Models to Train

| Variant | Features | Purpose |
|---------|----------|---------|
| xgb_full | ncores, nhosts, log_timelimit, log_wait_sec | Full XGBoost model |
| xgb_no_timelimit | ncores, nhosts, log_wait_sec | Can XGBoost recover signal? |
| ridge_no_timelimit | ncores, nhosts, log_wait_sec | Baseline from EXP-003b |

### XGBoost Hyperparameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| n_estimators | 100 | Balance speed/accuracy |
| max_depth | 6 | Prevent overfitting |
| learning_rate | 0.1 | Standard default |
| subsample | 0.8 | Reduce variance |
| colsample_bytree | 0.8 | Feature bagging |
| early_stopping_rounds | 10 | Prevent overfitting |

### Evaluation

Same metrics as EXP-003b:
- R², MAE (log), MdAE (log), RMSE (log)
- MAE (sec), MdAE (sec), MAPE, MdAPE

---

## FRESCO Data Specification

| Parameter | Value |
|-----------|-------|
| Cluster(s) | All (S=Stampede, C=Conte, NONE=Anvil) |
| Source | Raw FRESCO chunks (source_token from filename) |
| Split | 80/20 time-based per cluster |

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

## Expected Outcomes

1. **If XGBoost >> Ridge on no_timelimit**: Nonlinear interactions exist, worth exploring deeper
2. **If XGBoost ≈ Ridge on no_timelimit**: Feature set is fundamentally limited, need richer features
3. **Comparison insight**: Quantify how much nonlinearity helps across clusters

---

## Dependencies

- None (reads raw FRESCO data directly)
- Reuses data loading from EXP-003b

---

## Execution Log

| Date | Action | Result/Notes |
|------|--------|--------------|
| 2026-01-31 | Created | Designed XGBoost ablation experiment |
