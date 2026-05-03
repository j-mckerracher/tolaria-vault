# EXP-009: Conte anomaly resolution

## Goal
Resolve and interpret the Conte anomaly (NONE→C outperforming C→C) as either:

- **H2: Non-stationarity** (drift makes Conte’s time split unusually hard)
- **H1: Under-specification** (Conte’s resource requests have too little support/variance to learn slopes)

## Data / Label / Features
- **Source**: FRESCO parquet shards (`read_parquet(..., filename=true)`), aggregated to **job (`jid`)**.
- **Label**: `log(runtime_sec)` where `runtime_sec = end_time - start_time`.
- **Features (with timelimit)**: `log1p(ncores)`, `log1p(nhosts)`, `log1p(timelimit_sec)`.
- **Timelimit normalization**: Stampede (`S`) timelimit minutes→seconds (implemented for consistency with EXP-007/008).
- **Filters**: runtime > 0, runtime < 30 days, timelimit_sec in (0, 365 days), ncores/nhosts > 0.

## Conditions (with timelimit)
All evaluations are **tested on Conte only**.

A) **C→C time split** (baseline)
- Train on older Conte months, test on most recent 20% months.

B) **C→C random split** (same train size as A)
- Randomly sample train/test from Conte using the same train+test sizes as (A).

C) **NONE→C transfer** (baseline)
- Train on NONE (time-train split), test on Conte time-test set.

D) **NONE→C transfer (support match)**
- Train on NONE time-train but filtered to `ncores=1` and `nhosts=1`, test on Conte time-test set.

## Hypothesis readout (printed by script)
- **H2 supported** if **B >> A** (by default: `R2(B) - R2(A) >= 0.10`).
- **H1 supported** if **C > D and C > A**.

## Results (Gilbreth job `10244237`)

With timelimit (log-runtime metrics):
- A) **C→C time split**: R²=0.114, sMAPE=145%
- B) **C→C random split** (matched sizes): R²=0.472, sMAPE=106%
- C) **NONE→C transfer**: R²=0.156, sMAPE=122%
- D) **NONE→C (support-match: ncores=1, nhosts=1)**: R²=0.186, sMAPE=123%

Interpretation:
- **H2 (non-stationarity / time-split harshness) is strongly supported**: B ≫ A (+0.359 R²).
- **H1 (under-specification via slope learning) is not supported** under this test (C is not > D).

## Run (Gilbreth)
```bash
sbbest scripts/exp009.slurm
```

## Outputs
- `results/exp009_conte_anomaly_results.csv`: per-condition metrics + counts (and optional variants if enabled).
- `logs/exp009_<jobid>.out`: includes the **HYPOTHESIS READOUT** block for quick interpretation.

## Logging findings
When reviewing the log output, record:
- `R2(A), R2(B), R2(C), R2(D)` and deltas `B-A`, `C-A`, `C-D`.
- A short statement consistent with the printed hypothesis booleans:
  - **H2**: “Random split improves Conte a lot ⇒ non-stationarity.”
  - **H1**: “NONE transfer helps, but not when support-matched ⇒ under-specification via slope learning.”
