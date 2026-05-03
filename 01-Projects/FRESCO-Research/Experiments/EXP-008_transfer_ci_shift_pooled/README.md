# EXP-008: Transfer matrix w/ bootstrap CIs + shift metrics + pooled training

- **Status**: Completed
- **Research Path**: PATH-C
- **Run**: Gilbreth job `10244070`
- **Goal**: Add confidence intervals, quantify covariate shift, and test pooled training with cluster conditioning.

## Hypotheses (Outcome)

1. **CIs**: Confirmed. The Conte “better-than-self” result is statistically robust (non-overlapping 95% bootstrap CIs).
2. **Shift**: Partially informative. JSD behaves sensibly; SMD can be unstable when the source feature variance is near-zero (Conte).
3. **Pooled**: Confirmed. Pooled training with cluster conditioning improves Anvil materially and modestly improves Conte.

## Method

- **Label**: `log(runtime_sec)`.
- **Features**: `log1p(ncores)`, `log1p(nhosts)`, optionally `log1p(timelimit_sec)`.
- **Splits**: time-based within each cluster (20% most recent months as test).
- **Models**: XGBoost regression (fixed params for comparability).
- **Bootstrap**: 200 resamples of the *test set* per evaluation cell.
- **Shift metrics**: mean/max standardized mean difference (SMD) and mean per-feature Jensen–Shannon divergence (JSD) using fixed histograms.

## Outputs

- `results/exp008_results.csv`: metrics + 95% bootstrap CIs + shift metrics for:
  - single-cluster training (S/C/NONE)
  - pooled training (all clusters), with and without cluster one-hot conditioning
  - both with_timelimit and no_timelimit variants

## Key Results (log-runtime R², 95% bootstrap CI)

From `results/exp008_r2_ci_table.csv`:

- **Conte anomaly**: `train=NONE → test=C` is better than `train=C → test=C`:
  - `NONE→C`: 0.153 [0.150, 0.157]
  - `C→C`: 0.113 [0.110, 0.115]

- **Pooled + cluster ID** improves Anvil beyond Anvil-only training:
  - `pooled(all)+clusterID → NONE`: 0.752 [0.747, 0.756]
  - `NONE→NONE`: 0.710 [0.704, 0.714]

## Artifacts

- Metrics + CIs: `results/exp008_results.csv`
- Paper table: `results/exp008_r2_ci_table.csv`
- Conte detail: `results/exp008_conte_test_detail.csv`
- Figures:
  - `results/exp008_r2_with_timelimit.png`
  - `results/exp008_r2_no_timelimit.png`
  - `results/exp008_shift_vs_r2.png`

## Run (Gilbreth)

Submitted with: `sbbest scripts/exp008.slurm`.
