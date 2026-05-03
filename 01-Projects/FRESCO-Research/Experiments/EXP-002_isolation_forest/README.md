# Experiment: EXP-002 - Isolation Forest Anomaly Detection

**Status**: Created  
**Date Created**: 2026-01-31  
**Last Updated**: 2026-01-31  
**Research Path**: PATH-A  
**Directory**: Experiments/EXP-002_isolation_forest

---

## Objective

Train Isolation Forest models to detect anomalous jobs in the FRESCO dataset, using the per-job rollup from EXP-001. Evaluate whether anomalies correlate with job failures (non-zero exit codes) and identify the most discriminative features.

## Hypothesis

**Prediction**: Isolation Forest will identify 1-5% of jobs as anomalous, and anomaly scores will correlate with job failures (exitcode ≠ 0). The most discriminative features will be runtime extremes, memory spikes, and CPU underutilization.

**Null Hypothesis**: Anomaly scores are uncorrelated with exit codes, and flagged anomalies are uniformly distributed across job attributes.

---

## FRESCO Data Specification

| Parameter | Value |
|-----------|-------|
| Cluster(s) | All (S=Stampede, C=Conte, NONE=Anvil) |
| Date Range | Full dataset (2013-2023) |
| Total Jobs | ~5.5M (from EXP-001 job_rollup) |
| Input | EXP-001 `job_rollup/` partitioned parquet |

### Features Used

**Numeric features (for Isolation Forest):**
```
runtime_sec, wait_sec, ncores, nhosts, timelimit,
cpuuser_mean, memused_mean, memused_max,
nfs_mean, block_mean
```

**Stratification variables (for analysis):**
```
source_token, start_year, start_month, exitcode
```

### Preprocessing

1. Filter to jobs with valid runtime (runtime_sec > 0)
2. Log-transform skewed features (runtime, wait, memory)
3. Handle missing values (impute median per cluster)
4. Standardize features per cluster (Z-score)

---

## Methodology

### Approach

Train separate Isolation Forest models per cluster (S, C, NONE) due to FIND-001 showing fundamentally different workload patterns. Compare:
1. **Per-cluster models**: Train/predict within each cluster
2. **Global model**: Train on all clusters, evaluate transfer

### Algorithm/Model

- **Type**: Unsupervised Anomaly Detection
- **Algorithm**: Isolation Forest (scikit-learn)
- **Why**: Scales to millions of jobs, interpretable via feature importances, no labels required

### Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| n_estimators | 100 | Number of trees |
| max_samples | 10000 | Subsample size per tree |
| contamination | 0.01 | Expected anomaly fraction (1%) |
| max_features | 1.0 | Use all features |
| random_state | 42 | Reproducibility |

### Evaluation

Since this is unsupervised, evaluate via:
1. **Anomaly-Failure Correlation**: Spearman correlation between anomaly score and binary failure indicator
2. **Precision@K**: Of top-K most anomalous jobs, what fraction failed?
3. **Feature Analysis**: Which features drive high anomaly scores?
4. **Temporal Analysis**: Are anomalies clustered in time (system events)?

---

## Reproducibility

### Environment

| Component | Version |
|-----------|---------|
| Python | 3.10+ |
| scikit-learn | ≥1.3 |
| pandas | ≥2.0 |
| duckdb | ≥0.9 |
| matplotlib | ≥3.7 |

### Code

- **Script(s)**: `scripts/exp002_isolation_forest.py`
- **SLURM Job**: `scripts/exp002.slurm`

### Random Seeds

- Seed: 42

---

## Supercomputer Job

| Field | Value |
|-------|-------|
| Cluster | Gilbreth |
| Scheduler | SLURM |
| Job ID | (pending) |
| Partition | a30 or a100-80gb |
| Nodes Requested | 1 |
| CPUs Requested | 16 |
| Memory Requested | 64GB |
| Walltime Requested | 04:00:00 |

---

## Execution Log

| Date | Action | Result/Notes |
|------|--------|--------------|
| 2026-01-31 | Created | Designed experiment based on EXP-001 results |
| 2026-01-31 | Completed | Trained models, generated analysis |

---

## Results Summary

### Cluster Metrics

| Cluster | Jobs | Anomalies | Anomaly Rate | Baseline Failure Rate |
|---------|------|-----------|--------------|----------------------|
| S (Stampede) | 5,004,700 | 50,047 | 1.00% | 27.6% |
| C (Conte) | 1,820,388 | 18,204 | 1.00% | 12.6% |
| NONE (Anvil) | 466,344 | 4,664 | 1.00% | 29.0% |

### Anomaly-Failure Correlation (Corrected - EXP-002b)

| Cluster | Spearman ρ | p-value | Precision@1% | Precision@5% | Lift@1% |
|---------|------------|---------|--------------|--------------|---------|
| C (Conte) | 0.233 | <0.001 | 47.3% | 41.5% | **3.74×** |
| S (Stampede) | 0.146 | <0.001 | 45.7% | 41.3% | **1.65×** |
| NONE (Anvil) | 0.110 | <0.001 | 45.4% | 30.4% | **1.57×** |

**Key Result**: Anomaly scores are significantly correlated with job failures across all clusters. Top 1% of anomalies have 1.6-3.7× higher failure rate than baseline.

### Key Observations

1. **Strong Failure Signal (FIND-008)**: Isolation Forest identifies failure-prone jobs at 1.6-3.7× baseline rate using only resource features.

2. **Conte Has Strongest Signal**: 3.74× lift suggests cleaner workload patterns or more consistent resource usage.

3. **~30% of Top Anomalies Completed Successfully**: These "successful anomalies" represent unusual-but-working jobs worth investigating.

4. **Temporal Clustering (FIND-006)**: Low-volume months show elevated anomaly rates.

### Top Anomalies Sample (Corrected)

| Job ID | Cluster | Date | Exitcode | Score | Failed |
|--------|---------|------|----------|-------|--------|
| JOB4294517_S | Stampede | 2014-10 | TIMEOUT | 0.227 | ✓ |
| JOB3525020_S | Stampede | 2014-06 | COMPLETED | 0.224 | ✗ |
| JOB1370769_S | Stampede | 2013-08 | NODE_FAIL | 0.223 | ✓ |
| JOB1348580 | Anvil | 2023-05 | TIMEOUT | 0.222 | ✓ |

---

## Output Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Anomaly scores | `results/anomaly_scores.parquet` | ✅ Generated |
| Cluster metrics | `results/cluster_metrics.csv` | ✅ Generated |
| Monthly summary | `results/monthly_anomaly_summary.csv` | ✅ Generated |
| Top 100 anomalies | `results/top_100_anomalies.csv` | ✅ Generated |
| Score distributions | `results/figures/score_distributions.png` | ✅ Generated |
| Monthly rates | `results/figures/anomaly_rate_by_month.png` | ✅ Generated |

---

## Next Steps

- [ ] Fix exitcode parsing: remap COMPLETED → success, others → failure
- [ ] Re-run correlation analysis with corrected failure indicator
- [ ] Analyze feature values for top 100 anomalies
- [ ] Filter to high-volume months for cleaner signal

---

## Output Artifacts (Expected)

| Artifact | Path | Description |
|----------|------|-------------|
| Anomaly scores | `results/anomaly_scores.parquet` | Per-job scores and predictions |
| Model files | `results/models/` | Pickled Isolation Forest models |
| Summary stats | `results/anomaly_summary.csv` | Aggregate stats by cluster/month |
| Figures | `results/figures/` | Score distributions, correlations |

---

## Analysis Plan

### 1. Anomaly Distribution
- Plot anomaly score distribution per cluster
- Identify threshold for "anomalous" (default: contamination=1%)

### 2. Failure Correlation
- Compute Spearman ρ between anomaly_score and (exitcode ≠ 0)
- Precision@1%, Precision@5% of most anomalous jobs

### 3. Feature Importance
- Analyze which features contribute most to high anomaly scores
- Compare across clusters

### 4. Temporal Patterns
- Plot anomaly rate by month
- Look for spikes correlating with known system events

### 5. Case Studies
- Manually inspect top 100 most anomalous jobs
- Categorize anomaly types (long runtime, memory spike, etc.)

---

## Dependencies

- **EXP-001**: Requires `job_rollup/` output from EXP-001
- **FIND-001**: Justifies per-cluster modeling approach

---

## Notes

- Consider FIND-003 (Anvil 10× memory): May need different contamination rate for Anvil
- GPU features not usable (FIND-002: no telemetry pre-2023)
- Exit code mapping may vary across clusters; treat as binary (0 vs non-zero)
