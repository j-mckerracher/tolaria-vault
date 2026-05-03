# EXP-010: Few-shot calibration on target site (error vs label fraction)

- **Status**: Completed
- **Research Path**: PATH-C
- **Created**: 2026-02-01
- **Last Updated**: 2026-02-01

## Objective
Quantify how quickly we can close the cross-site runtime transfer gap using a small labeled sample from the target site (few-shot calibration).

## Hypotheses

- **H1 (calibration helps)**: For each target site, adding even a small number of target-labeled jobs will materially improve transfer performance (R² increases; sMAPE decreases), with diminishing returns.
- **H2 (Conte drift limits gains)**: Conte gains will be smaller under a time-based test split than under a random split, consistent with strong non-stationarity (FIND-023).

## Experimental Design

### Sites / Splits

- **Target site**: Conte (primary), also evaluate Stampede and Anvil for completeness.
- **Base split**: time-based within each target cluster (20% most recent months = test), matching EXP-007/008.
- **Optional diagnostic**: Conte random split (matched sizes) to contextualize drift sensitivity (as in EXP-009).

### Models

- **Base transfer model**: train on source site(s), test on target time-test.
- **Few-shot calibration**: augment the training set with a random sample of target-cluster training-period jobs.

Calibration regimes to include:
- **Anvil (`NONE`)→Conte (`C`) + k-shot** (primary): source=Anvil, target=Conte.
- **Stampede (`S`)→Conte (`C`) + k-shot** (secondary): source=Stampede, target=Conte.
- **pooled(all)+clusterID + k-shot** (optional): test whether pooled models need fewer target labels.

### k-shot schedule
Evaluate a log-spaced schedule and cap at available training jobs:
- k ∈ {0, 100, 300, 1k, 3k, 10k, 30k, 100k}

### Features / Label
- **Label**: `log(runtime_sec)` where `runtime_sec = end_time - start_time`.
- **Features**: `log1p(ncores)`, `log1p(nhosts)`, `log1p(timelimit_sec)`.
- **Timelimit normalization**: Stampede (S) timelimit minutes→seconds.

### Metrics
- R² (log-runtime)
- MAE(log)
- Median absolute error (log)
- Median sMAPE (percent)

### Uncertainty
Use bootstrap on the test set (e.g., 200 resamples) for CIs at each k.

## Supercomputer Job

- **Cluster**: Gilbreth
- **Scheduler**: SLURM
- **Submission**: `sbbest scripts/exp010.slurm`
- **Job ID**: 10244326

## Reproducibility

- **Code**: `scripts/exp010_few_shot_calibration.py`
- **SLURM**: `scripts/exp010.slurm`
- **Git commit**: `ff64283755370e1d7cd33967813bf966ef25161e`
- **Outputs**:
  - `results/exp010_results.csv` (long-form, all k/conditions)
  - `results/exp010_summary_table.csv`
  - `results/exp010_calibration_curves.png`
  - `logs/exp010_10244326.out`

## Results (Conte time-test)

Key rows (R² on log-runtime; 95% bootstrap CI over test set):

- Anvil (`NONE`)→Conte (`C`):
  - k=0: R²=0.143 [0.139, 0.147]
  - k=300: R²=0.095 [0.092, 0.098]
  - k=1k: R²=0.159 [0.157, 0.163]

- Stampede (`S`)→Conte (`C`):
  - k=0: R²=0.003 [-0.000, 0.007]
  - k=100: R²=0.162 [0.160, 0.164]
  - k=1k: R²=0.123 [0.120, 0.126]

**Interpretation**:
- Few-shot adaptation via naive uniform mixing is not reliably monotonic in k; some k values degrade performance substantially.
- Note: the `k=0` Anvil→Conte baseline in EXP-010 differs from EXP-008’s reported Anvil→Conte baseline, consistent with known XGBoost nondeterminism under multi-threading; treat comparisons as *within-EXP-010* unless re-run under controlled determinism.
- This result is **not** yet publishable without repeated k-sampling / multiple seeds (see FIND-024 caveats).

## Related Findings
- FIND-020 (timelimit essential for transfer)
- FIND-022 (Conte “better-than-self” anomaly)
- FIND-023 (Conte non-stationarity / time-split harshness)
