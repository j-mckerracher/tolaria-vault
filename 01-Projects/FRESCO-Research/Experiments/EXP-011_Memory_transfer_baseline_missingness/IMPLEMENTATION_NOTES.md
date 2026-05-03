# EXP-011 Implementation Notes

## Implementation Date
2026-01-31

## Overview
Implemented EXP-011_Memory_transfer_baseline_missingness following patterns from EXP-007/008/010.

## Files Created

### 1. `scripts/exp011_memory_transfer.py` (13,300 bytes)
Main analysis script that:
- Loads FRESCO chunks via DuckDB
- Computes job-level peak memory: `peak_memused = MAX(value_memused)` per jid
- Tracks missingness: counts jobs with ≥1 memory sample
- Features: `log1p(ncores)`, `log1p(nhosts)`, `log1p(timelimit_sec)` (NO runtime features)
- Label: `log(peak_memused)`
- Runs transfer matrix experiments (within-site + cross-site)
- Bootstrap confidence intervals (200 iterations) on R², MAE, MDAE, SMAPE
- Covariate shift metrics: SMD and JSD

### 2. `scripts/exp011.slurm` (1,173 bytes)
SLURM job script for Gilbreth:
- Resources: 1 node, 16 CPUs, 64GB RAM, 1 GPU, 4h walltime
- Account: sbagchi, QoS: standby, Partition: a30
- Dependencies: pandas, pyarrow, duckdb, numpy, scikit-learn, xgboost, matplotlib
- Paths: `/home/jmckerra/Experiments/EXP-011_Memory_transfer_baseline_missingness`

### 3. `scripts/exp011_make_figures.py` (6,155 bytes)
Figure/table generation script:
- R² bar plots with bootstrap CIs (per test cluster)
- Shift vs R² scatter plot (transfer cases)
- Missingness coverage bar plot (per cluster)
- Summary tables: pivot, missingness, transfer detail

### 4. `README.md` (updated)
Updated sections:
- Hypothesis: predictions about memory transfer performance
- FRESCO Data Specification: filters, columns, clusters
- Methodology: 8-step approach + XGBoost hyperparameters
- Reproducibility: environment, scripts, seeds
- Supercomputer Job: Gilbreth specs
- Output Artifacts: all expected files

## Key Design Decisions

### Memory Label
- Uses `MAX(value_memused)` per jid from raw snapshots
- Restricts to jobs with ≥1 memory sample (mem_sample_count > 0)
- Takes log transform for regression: `log(peak_memused)`

### Features
- **Included**: `log1p(ncores)`, `log1p(nhosts)`, `log1p(timelimit_sec)`
- **Excluded**: Runtime features (runtime_sec) - not available at job submission
- **Conditional**: Cluster one-hot encoding (only for pooled+conditioning models)

### Missingness Tracking
- Reports fraction with ≥1 memory sample BEFORE filtering
- Stores `train_mem_coverage` and `test_mem_coverage` in results CSV
- Prints coverage stats per cluster during loading

### Training Specifications
Follows EXP-008 pattern:
1. Single-cluster: S only
2. Single-cluster: C only
3. Single-cluster: NONE only
4. Pooled all clusters, no conditioning
5. Pooled all clusters, with cluster ID conditioning

### Evaluation Metrics
- R² (coefficient of determination on log scale)
- MAE (mean absolute error on log scale)
- MDAE (median absolute error on log scale)
- SMAPE (symmetric mean absolute percentage error, back-transformed)
- Bootstrap 95% CIs for all metrics (200 iterations)
- Covariate shift: SMD (standardized mean difference), JSD (Jensen-Shannon divergence)

## Output CSV Structure

`results/exp011_results.csv` contains:
- `train_spec`: training specification name
- `train_clusters`: cluster(s) used for training (joined by "+")
- `cluster_conditioning`: boolean, whether cluster ID features used
- `test_cluster`: target cluster for evaluation
- `n_train`: number of training jobs
- `n_test`: number of test jobs
- `train_mem_coverage`: fraction of train jobs with ≥1 mem sample
- `test_mem_coverage`: fraction of test jobs with ≥1 mem sample
- `r2`, `r2_ci_low`, `r2_ci_high`: R² and 95% CI
- `mae_log`, `mae_log_ci_low`, `mae_log_ci_high`: MAE and 95% CI
- `mdae_log`, `mdae_log_ci_low`, `mdae_log_ci_high`: MDAE and 95% CI
- `smape`, `smape_ci_low`, `smape_ci_high`: SMAPE and 95% CI
- `shift_smd_mean`: mean standardized mean difference
- `shift_smd_max`: max standardized mean difference
- `shift_jsd_mean`: mean Jensen-Shannon divergence

## Consistency with Prior Experiments

### EXP-008 Patterns Used
- DuckDB data loading with aggregation
- Time-based split (last 20% yearmonths per cluster)
- XGBoost hyperparameters (n=200, depth=6, lr=0.1)
- Bootstrap CI methodology
- Shift metrics (SMD, JSD)
- SLURM script template
- Figure generation style

### Differences from EXP-008
- Label: memory instead of runtime
- Features: no runtime features (submission features only)
- Additional tracking: memory sample missingness
- Additional columns: train_mem_coverage, test_mem_coverage

## Running the Experiment

### On Gilbreth (SLURM submission)
```bash
cd /home/jmckerra/Experiments/EXP-011_Memory_transfer_baseline_missingness
sbatch scripts/exp011.slurm
```

### After job completes (local figure generation)
```bash
cd /home/jmckerra/Experiments/EXP-011_Memory_transfer_baseline_missingness
python scripts/exp011_make_figures.py
```

### Local testing (optional)
```bash
python scripts/exp011_memory_transfer.py \
  --input-dir /depot/sbagchi/data/josh/FRESCO/chunks \
  --out-dir results \
  --threads 16 \
  --n-boot 200 \
  --test-frac 0.2 \
  --seed 42
```

## Data Requirements

Minimum per cluster:
- 2,000 total jobs after filtering
- 1,000 training jobs (pre-cutoff)
- 1,000 test jobs (post-cutoff)

If a cluster doesn't meet these thresholds, it's skipped with a warning.

## Expected Runtime

Based on EXP-008/010 timings:
- Data loading: ~10-20 minutes (depends on FRESCO chunk size)
- Training + evaluation: ~30-60 minutes (5 training specs × 3 test clusters × 200 bootstrap iterations)
- Total: ~1-2 hours (well within 4h walltime)

## Verification Checklist

- [x] Python scripts pass syntax check
- [x] SLURM script has all required directives
- [x] README.md updated with methodology
- [x] Features match requirements (no runtime)
- [x] Memory label matches requirements (log peak)
- [x] Missingness tracking implemented
- [x] Output columns include coverage fields
- [x] Paths use Linux format for SLURM
- [x] Consistent with EXP-008 patterns

## Notes

- The script prints detailed progress and missingness statistics
- Bootstrap iterations use seed=42 for reproducibility
- Cluster IDs derived from filename patterns: `*_S.parquet`, `*_C.parquet`, else "NONE"
- Stampede timelimit conversion: raw value × 60 (minutes → seconds)
- Filters jobs to runtime < 30 days and timelimit < 365 days (same as EXP-008)
