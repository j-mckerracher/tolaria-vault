# Experiments & Evaluation Protocol (Publication Required)

**Last Updated**: 2026-02-03

## Goals
1. Demonstrate pipeline correctness and stability.
2. Quantify where cross-cluster insights are valid.
3. Quantify where naive transfer fails and why.

## Standard evaluation protocol
- Fixed random seed(s)
- Pre-registered feature sets
- Pre-registered cohort matching rules
- Bootstrap confidence intervals

## Canonical split protocol (v3 default)
This is the default split protocol to use unless an experiment explicitly documents a different protocol.

### Within-cluster (E1)
- Time-based holdout split by `yearmonth` within a cluster:
  - sort unique `yearmonth`
  - choose cutoff so last 20% of months are test (min 1 month)
  - train = months < cutoff; test = months >= cutoff
- Metrics computed in log space for the target (and also report bias + calibration slope/intercept).

### Cross-cluster transfer (E2)
- Train on source cluster *train split* (as above) and evaluate on target cluster *test split*.
- Always report shift diagnostics (KS or equivalent) and domain classifier AUC.

### Balanced subsampling (when needed)
To avoid dominance by a single cluster in pooled or comparative experiments, use deterministic subsampling:
- Set fixed `seed` and record it in run config.
- Sample up to `train_n_per_cluster` and `test_n_per_cluster` per cluster *after* the split.
- If stratifying, stratify on `workload_regime` (and optionally `failed/timed_out`) and document the strata.

## Required experiments

### E1: Within-cluster prediction sanity
- Train/test splits within each cluster
- Report R², MAE, bias, calibration, CI

### E2: Cross-cluster transfer baseline (expected to fail)
- Train on A, test on B without labels
- Document failure modes (bias, calibration slope, covariate shift)

### E3: Regime-matched zero-shot transfer
- Define regime (CPU-only, similar node_type)
- Build overlap cohort
- Evaluate as in E1

### E4: Unlabeled domain adaptation (optional)
- CORAL or representation alignment using unlabeled target features

## Reporting requirements
For every cross-cluster result:
- overlap coverage
- KS statistics for key features
- domain classifier AUC
- residual bias + calibration slope

## Artifacts
- Store all results tables + plots + configs in a versioned run folder.
