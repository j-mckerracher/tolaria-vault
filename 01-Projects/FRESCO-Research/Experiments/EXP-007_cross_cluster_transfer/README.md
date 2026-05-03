# EXP-007: Cross-cluster transfer matrix

- **Status**: Completed
- **Research Path**: PATH-C

## Objective

Measure zero-shot cross-cluster transfer for runtime prediction (train on one cluster, test on the others), and compare performance with and without timelimit.

## Data / Label

- **Source**: FRESCO Parquet shards under `/depot/sbagchi/data/josh/FRESCO/chunks`
- **Unit of analysis**: job (`jid`) aggregated across snapshots
- **Label**: `runtime_sec = end_time - start_time` (seconds), modeled as `log(runtime_sec)`
- **Clusters**: `S` (Stampede), `C` (Conte), `NONE` (Anvil)
- **Timelimit normalization**: Stampede timelimit is in minutes; normalized to seconds before modeling.

## Method

- Time-based split by `yearmonth` within each cluster (most recent 20% months as test)
- Model: XGBoost regressor
- Features:
  - `log1p(ncores)`, `log1p(nhosts)`
  - `log1p(timelimit_sec)` (optional ablation)

## Outputs

- Results CSV: `results/transfer_matrix.csv`
- Run log: `logs/exp007_<jobid>.out`

## Key Result (high-level)

Cross-cluster transfer is viable *only when timelimit is included*; without timelimit, transfer R² becomes negative in all cases.
