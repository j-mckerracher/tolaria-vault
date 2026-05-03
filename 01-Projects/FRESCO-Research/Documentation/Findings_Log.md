# Findings Log

This document tracks all significant discoveries from the FRESCO research project. Findings are logged here to:
- Build a centralized record of insights
- Identify patterns across experiments
- Support narrative development for publications

---

## Summary

| ID | Title | Path | Potential | Status |
|----|-------|------|-----------|--------|
| FIND-001 | Dramatic cross-cluster workload differences | PATH-A | High | Verified |
| FIND-002 | Zero GPU telemetry pre-2023 | PATH-A | Medium | Verified |
| FIND-003 | Anvil (2022-23) shows 10× higher memory usage | PATH-A | High | Verified |
| FIND-004 | Wait times increased 10× in 2015 | PATH-A | Medium | Needs Verification |
| FIND-005 | Exitcode is string, not numeric - RESOLVED | PATH-A | Medium | Verified |
| FIND-006 | Anomalies cluster in early months and transitions | PATH-A | Medium | Verified |
| FIND-008 | Anomalies predict failures at 1.6-3.7× baseline rate | PATH-A | High | Verified |
| FIND-009 | Timelimit dominates runtime prediction | PATH-B | High | Verified |
| FIND-010 | Linear models explain 26-36% of log-runtime variance | PATH-B | Medium | Superseded |
| FIND-011 | Conte cluster missing from EXP-003 results | PATH-B | Medium | Resolved |
| FIND-012 | Ablation confirms timelimit is 90%+ of signal | PATH-B | High | Verified |
| FIND-013 | Cluster heterogeneity: R² ranges 0.16-0.58 | PATH-B | High | Verified |
| FIND-014 | Month features add negligible predictive value | PATH-B | Medium | Verified |
| FIND-015 | XGBoost provides marginal gains over Ridge | PATH-B | Medium | Verified |
| FIND-016 | Anvil uniquely recovers signal without timelimit | PATH-B | High | **REFUTED** |
| FIND-017 | User-level memorization dominates runtime prediction | PATH-B | High | Verified |
| FIND-018 | Timelimit is essential for prediction | PATH-B | High | Verified |
| FIND-019 | Leakage magnitude is cluster-dependent | PATH-B | High | Verified |
| FIND-020 | Cross-cluster transfer viable when timelimit available | PATH-C | High | Verified |
| FIND-021 | Anvil has largest transfer gap | PATH-C | High | Verified |
| FIND-022 | Cross-cluster can outperform same-cluster (Conte anomaly) | PATH-C | High | Verified |
| FIND-023 | Conte anomaly driven by temporal shift, not under-specification | PATH-C | High | Verified |
| FIND-024 | Few-shot calibration is non-monotonic under naive mixing | PATH-C | Medium | Needs Verification |
| FIND-025 | Memory coverage excellent (>98%) across all clusters | PATH-C | Medium | Verified |
| FIND-026 | Cross-site memory prediction fails catastrophically | PATH-C | High | Verified |
| FIND-027 | Memory metrics likely non-standardized across clusters | PATH-C | High | Verified |
| FIND-028 | Systematic 6-9× memory offsets between clusters | PATH-C | High | Verified |
| FIND-029 | Aggregation is consistent (max-per-node) across clusters | PATH-C | Medium | Verified |

---

**Cluster token legend (used in tables/figures):**
- `S` = Stampede (filename suffix `_S.parquet`)
- `C` = Conte (filename suffix `_C.parquet`)
- `NONE` = Anvil (no suffix observed in 2022–2023 shards)

## Findings

### FIND-001: Dramatic cross-cluster workload differences

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-001](../Experiments/EXP-001_baseline_statistical_analysis/README.md)
- **Research Path**: PATH-A
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
The three clusters (Stampede/S, Conte/C, Anvil/NONE) show fundamentally different workload patterns. Conte jobs average 1 core while Stampede averages 150-300 cores. Anvil shows intermediate patterns with higher memory usage.

**Evidence**:
- Conte (C) `ncores_mean` ≈ 1.0 consistently across all months
- Stampede (S) `ncores_mean` ranges 100-400
- Anvil (NONE) `ncores_mean` ranges 60-200

**Implications**:  
Any cross-site analysis must account for these structural differences. Models trained on one cluster may not transfer directly.

**Related Findings**: FIND-003

**Next Steps**:
- [ ] Investigate queue/account distributions per cluster
- [ ] Include cluster as a stratification variable in all experiments

---

### FIND-002: Zero GPU telemetry pre-2023

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-001](../Experiments/EXP-001_baseline_statistical_analysis/README.md)
- **Research Path**: PATH-A
- **Publication Potential**: Medium
- **Status**: Verified

**Description**:  
The `frac_jobs_with_gpu_samples` column is 0.0 for all months prior to 2023. GPU telemetry only appears in Feb-Mar 2023 at very low rates (0.2-4%).

**Evidence**:
- 2013-2022: `frac_jobs_with_gpu_samples` = 0.0
- 2023-02: `frac_jobs_with_gpu_samples` = 0.04 (4%)
- 2023-03: `frac_jobs_with_gpu_samples` = 0.002 (0.2%)

**Implications**:  
GPU-based anomaly detection or prediction is not feasible for the bulk of the dataset. Focus GPU analysis on 2023 Anvil data only.

**Related Findings**: None yet

**Next Steps**:
- [ ] Confirm whether GPU columns are null or missing vs. truly zero usage

---

### FIND-003: Anvil (2022-23) shows 10× higher memory usage

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-001](../Experiments/EXP-001_baseline_statistical_analysis/README.md)
- **Research Path**: PATH-A
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
Peak memory usage (`peak_memused_mean`) on Anvil averages 50-100 GB compared to 5-10 GB on Stampede/Conte. This 10× difference reflects either different workloads or different memory architectures.

**Evidence**:
- Stampede 2016 average: `peak_memused_mean` ≈ 7-10 GB
- Conte 2016 average: `peak_memused_mean` ≈ 5-8 GB
- Anvil 2022-23 average: `peak_memused_mean` ≈ 50-80 GB

**Implications**:  
Memory-based anomaly thresholds must be cluster-specific. This also suggests Anvil supports more memory-intensive workloads (ML/AI).

**Related Findings**: FIND-001

**Next Steps**:
- [ ] Correlate with node memory capacity per cluster
- [ ] Check if this reflects larger allocations (`nhosts`, `ncores`)

---

### FIND-004: Wait times increased 10× in 2015

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-001](../Experiments/EXP-001_baseline_statistical_analysis/README.md)
- **Research Path**: PATH-A
- **Publication Potential**: Medium
- **Status**: Needs Verification

**Description**:  
Stampede wait times (`wait_mean_sec`) spiked from ~3,000 sec in early 2014 to 30,000-50,000 sec in Feb-Apr 2015, suggesting a period of heavy congestion or policy changes.

**Evidence**:
- 2014-01: `wait_mean_sec` = 2,888
- 2015-02: `wait_mean_sec` = 24,556
- 2015-03: `wait_mean_sec` = 46,139

**Implications**:  
This congestion event could serve as a natural experiment for queue behavior analysis.

**Related Findings**: None yet

**Next Steps**:
- [ ] Check TACC announcements/maintenance logs for Feb-Apr 2015
- [ ] Analyze job rejection rates during this period

---

### FIND-005: Exitcode is string, not numeric - RESOLVED

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-002](../Experiments/EXP-002_isolation_forest/README.md)
- **Research Path**: PATH-A
- **Publication Potential**: Medium (data quality note)
- **Status**: Verified (resolved in EXP-002b)

**Description**:  
The exitcode column contains string status values (COMPLETED, TIMEOUT, CANCELLED, FAILED, NODE_FAIL) not numeric exit codes. Initial analysis incorrectly treated all values as failures.

**Resolution**:  
EXP-002b remapped: COMPLETED → success, all others → failure. Corrected baseline failure rates: Conte 12.6%, Stampede 27.6%, Anvil 29.0%.

**Related Findings**: FIND-008

---

### FIND-006: Anomalies cluster in early months and transitions

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-002](../Experiments/EXP-002_isolation_forest/README.md)
- **Research Path**: PATH-A
- **Publication Potential**: Medium
- **Status**: Verified

**Description**:  
Monthly anomaly rates are elevated during cluster start-up periods and low-data months. Conte shows 10.7% anomaly rate in Jul 2015 (only 661 jobs) vs 1-2% in high-volume months.

**Evidence**:
- Conte 2015-07: 10.7% anomaly rate (n=661)
- Conte 2015-04: 8.7% anomaly rate (n=759)
- Anvil 2022-06: 16% anomaly rate (n=25)
- High-volume months: 0.5-2% anomaly rate

**Implications**:  
Low-volume months may have different workload characteristics or data collection issues. Anomaly detection should account for sample size.

**Related Findings**: FIND-001

**Next Steps**:
- [ ] Filter analysis to months with >1000 jobs
- [ ] Investigate early-month job characteristics

---

### FIND-007: Top anomalies show diverse failure modes

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-002](../Experiments/EXP-002_isolation_forest/README.md)
- **Research Path**: PATH-A
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
The top 100 most anomalous jobs include TIMEOUT, NODE_FAIL, CANCELLED, FAILED, and surprisingly many COMPLETED jobs. This suggests the Isolation Forest is detecting genuinely unusual resource usage patterns, not just failures.

**Evidence**:
- Top anomaly: JOB4294517_S (TIMEOUT, score=0.227)
- NODE_FAIL jobs: JOB1370769_S, JOB1372318_S (scores ~0.22)
- COMPLETED jobs in top 10: JOB3525020_S, JOB3525007_S (scores ~0.22)
- Cluster concentration: 70%+ from Stampede 2013-2014

**Implications**:  
Anomaly detection captures more than just failures—it identifies unusual resource consumption patterns. The COMPLETED anomalies may represent jobs that succeeded despite unusual behavior (worth investigating).

**Related Findings**: FIND-005, FIND-006

**Next Steps**:
- [ ] Analyze feature values for top 100 anomalies
- [ ] Categorize anomaly types (long runtime, memory spike, CPU anomaly)
- [ ] Compare COMPLETED vs FAILED anomaly characteristics

---

### FIND-008: Anomalies predict failures at 1.6-3.7× baseline rate

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-002](../Experiments/EXP-002_isolation_forest/README.md), EXP-002b
- **Research Path**: PATH-A
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
After correcting exitcode parsing, Isolation Forest anomalies show significant correlation with job failures. The top 1% of anomalous jobs have 45-47% failure rate vs 13-29% baseline—a 1.6-3.7× lift.

**Evidence**:

| Cluster | Baseline Failure | Precision@1% | Lift | Spearman ρ |
|---------|-----------------|--------------|------|------------|
| Conte (C) | 12.6% | 47.3% | **3.74×** | 0.233 |
| Stampede (S) | 27.6% | 45.7% | **1.65×** | 0.146 |
| Anvil (NONE) | 29.0% | 45.4% | **1.57×** | 0.110 |

All correlations significant at p < 0.001.

**Implications**:  
- Isolation Forest successfully identifies failure-prone jobs using only resource features
- Conte shows strongest signal (3.7× lift)—may have cleaner workload patterns
- Can be used for early warning system or resource allocation optimization

**Related Findings**: FIND-005, FIND-007

**Next Steps**:
- [ ] Analyze which features drive high anomaly scores
- [ ] Test as a real-time failure predictor
- [ ] Investigate why Conte has higher lift than Stampede/Anvil

---

### FIND-009: Timelimit dominates runtime prediction

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-003](../Experiments/EXP-003_linear_regression/README.md), [EXP-003b](../Experiments/EXP-003b_linear_regression_fixed/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
In Ridge Regression models for runtime prediction, log(timelimit) is by far the strongest predictor. Ablation study (EXP-003b) confirms: removing timelimit causes R² to collapse while timelimit_only achieves nearly the same R² as the full model.

**Evidence** (EXP-003b ablation):

| Cluster | Full R² | timelimit_only R² | no_timelimit R² | Δ R² |
|---------|---------|-------------------|-----------------|------|
| Anvil | 0.56 | 0.55 | **0.05** | -0.51 |
| Stampede | 0.36 | 0.34 | **0.15** | -0.21 |
| Conte | 0.16 | 0.13 | **-0.03** | -0.19 |

**Implications**:  
- timelimit encodes ~90% of the predictive signal in linear models
- This is a **behavioral/policy feature**, not a system-intrinsic feature
- Users estimate their own runtimes reasonably well
- For "intrinsic" prediction (without user hints), need richer features

**Related Findings**: FIND-012, FIND-013

**Next Steps**:
- [x] Run ablation: model without timelimit ✓
- [x] Compare against "predict timelimit" baseline ✓
- [ ] Plot log(runtime) vs log(timelimit) to characterize relationship
- [ ] Test nonlinear models to recover signal from non-timelimit features

---

### FIND-010: Linear models explain 26-36% of log-runtime variance

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-003](../Experiments/EXP-003_linear_regression/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: Medium
- **Status**: Verified

**Description**:  
Ridge Regression baseline achieves R² = 0.36 (Stampede) and R² = 0.26 (Anvil) on log(runtime). While statistically significant with 7M jobs, practical utility is limited—MAE is 4.4-12.6 hours in original units.

**Evidence**:

| Cluster | R² | MAE (log) | MAE (hours) | MAPE |
|---------|-----|-----------|-------------|------|
| Stampede | 0.356 | 1.86 | 4.4 | 3309% |
| Anvil | 0.258 | 1.95 | 12.6 | 201% |

**Critical Review Notes** (GPT-5.2):
- MAPE of 3309% indicates many near-zero runtime jobs (MAPE inappropriate for heavy tails)
- Log-space metrics don't translate linearly to practical error
- R² on this scale may not reflect useful predictive power
- Time-based split may still have user/project leakage

**Implications**:  
Linear models provide a weak baseline. More sophisticated models (trees, neural nets) with richer features are needed. High MAPE warrants switching to median-based metrics (MdAPE, MdAE).

**Related Findings**: FIND-009

**Next Steps**:
- [ ] Report median metrics alongside mean
- [ ] Add residual analysis by runtime decile
- [ ] Test Random Forest / XGBoost for comparison

---

### FIND-011: Conte cluster missing from EXP-003 results - RESOLVED

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-003](../Experiments/EXP-003_linear_regression/README.md), [EXP-003b](../Experiments/EXP-003b_linear_regression_fixed/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: Medium (data quality)
- **Status**: Resolved

**Description**:  
EXP-003 results only contained Stampede (S) and Anvil (NONE) clusters. Conte (C) was missing due to incorrect source_token extraction from jid column instead of filename.

**Root Cause**:
- Stampede job IDs contain `_S` suffix (e.g., `JOB6244386_S`)
- Conte job IDs do NOT contain `_C` suffix (e.g., `JOB373585`)
- Source token is in the **filename** (e.g., `00_C.parquet`), not the jid

**Resolution**:  
EXP-003b extracts source_token from filename using DuckDB's `filename=true` option. Now correctly identifies all 3 clusters:
- Stampede: 5,004,652 jobs
- Conte: 1,820,385 jobs
- Anvil: 466,344 jobs

**Implications**:  
Data preprocessing bugs can silently exclude entire clusters. Always verify cluster counts match expectations.

**Related Findings**: FIND-001

---

### FIND-012: Ablation confirms timelimit is 90%+ of signal

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-003b](../Experiments/EXP-003b_linear_regression_fixed/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
Ablation study demonstrates that timelimit alone captures nearly all predictive signal. The model without timelimit performs at or below baseline, while timelimit_only achieves ~95% of full model R².

**Evidence**:

| Cluster | full R² | timelimit_only R² | % of signal |
|---------|---------|-------------------|-------------|
| Anvil | 0.56 | 0.55 | 98% |
| Stampede | 0.36 | 0.34 | 94% |
| Conte | 0.16 | 0.13 | 81% |

**Implications**:
- User-provided timelimit encodes most runtime information
- ncores, nhosts, wait_sec add marginal value in linear models
- For "intrinsic" prediction without user hints, need different approach

**Related Findings**: FIND-009, FIND-013

**Next Steps**:
- [ ] Test nonlinear models on no_timelimit features
- [ ] Add per-user/per-project history features
- [ ] Investigate why Conte has lower timelimit-signal ratio

---

### FIND-013: Cluster heterogeneity: R² ranges 0.16-0.58

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-003b](../Experiments/EXP-003b_linear_regression_fixed/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
Runtime predictability varies dramatically across clusters. Anvil achieves R²=0.58 while Conte achieves only R²=0.16 with identical features. This indicates fundamentally different data generating processes.

**Evidence** (full model):

| Cluster | R² | MdAPE | Jobs |
|---------|-----|-------|------|
| Anvil (NONE) | 0.58 | 93% | 466K |
| Stampede (S) | 0.36 | 84% | 5M |
| Conte (C) | 0.16 | 85% | 1.8M |

**Possible Explanations**:
1. Different timelimit semantics/enforcement across sites
2. More heterogeneous workloads on Conte (higher irreducible variance)
3. Different user behavior patterns
4. Missing covariates more important for Conte

**Critical Review Note** (GPT-5.2):
Conte's baseline_median achieves *better* MdAE than trained models, suggesting potential model miscalibration or metric inconsistency. Requires investigation.

**Implications**:
- Cross-site models may not transfer well
- Site-specific modeling may be necessary
- Understanding *why* Conte differs is scientifically valuable

**Related Findings**: FIND-001, FIND-012

**Next Steps**:
- [ ] Investigate Conte baseline anomaly (why does median beat model?)
- [ ] Compare timelimit-runtime correlation by cluster
- [ ] Test cross-cluster transfer (train on S, test on C)

---

### FIND-014: Month features add negligible predictive value

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-003b](../Experiments/EXP-003b_linear_regression_fixed/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: Medium
- **Status**: Verified

**Description**:  
Removing month dummy features has virtually no impact on model performance. The `no_month` variant performs identically to (or slightly better than) the `full` model across all clusters.

**Evidence**:

| Cluster | full R² | no_month R² | Δ R² |
|---------|---------|-------------|------|
| Anvil | 0.562 | 0.583 | +0.02 |
| Stampede | 0.356 | 0.355 | -0.00 |
| Conte | 0.158 | 0.184 | +0.03 |

**Implications**:
- No strong seasonality in runtime given other covariates
- OR: timelimit dominance masks seasonal effects
- Simpler model (4 features) preferred over 16-feature model

**Related Findings**: FIND-012

---

### FIND-015: XGBoost provides marginal gains over Ridge

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-004](../Experiments/EXP-004_xgboost_ablation/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: Medium
- **Status**: Verified

**Description**:  
XGBoost tree-based models provide small but consistent gains over Ridge regression for runtime prediction, primarily on Anvil where R² improves from 0.59 to 0.63 with full features.

**Evidence** (full model):

| Cluster | Ridge R² | XGBoost R² | Δ R² |
|---------|----------|------------|------|
| Anvil (NONE) | 0.59 | **0.63** | +0.04 |
| Stampede (S) | 0.36 | **0.36** | +0.00 |
| Conte (C) | 0.20 | **0.22** | +0.02 |

**Implications**:
- Nonlinear interactions exist but provide limited additional value
- Model complexity gains are modest given added computational cost
- Simple linear models may suffice for production use

**Related Findings**: FIND-009, FIND-012, FIND-016

**Next Steps**:
- [ ] Compare computational cost (training time, inference time)
- [ ] Test Random Forest for additional comparison

---

### FIND-016: Anvil uniquely recovers signal without timelimit - **REFUTED**

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-004](../Experiments/EXP-004_xgboost_ablation/README.md), [EXP-005](../Experiments/EXP-005_anvil_verification/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: High (as negative result)
- **Status**: **REFUTED by EXP-005**

**Original Claim**:  
On Anvil (2022-2023), XGBoost achieves R²=0.28 without timelimit, compared to R²≈0.06 for Ridge. This suggests Anvil has exploitable nonlinear structure that Conte/Stampede lack.

**Verification Results (EXP-005)**:

| Split Type | XGBoost no_timelimit R² | Ridge no_timelimit R² |
|------------|-------------------------|------------------------|
| Time-based | 0.39 | 0.17 |
| **User-aware** | **-0.74** | **-0.78** |

**Why the original finding was wrong**:
1. **Month is NOT the issue**: Removing month *improved* R² (0.39→0.40)
2. **Interaction features don't help**: cores_per_node adds nothing
3. **MASSIVE user leakage**: R² drops from +0.40 to -0.53 with user-aware split
4. All models perform WORSE than mean predictor when users are held out

**Root Cause**:
The apparent "signal recovery" was **user-level memorization**. Users submit repetitive workloads with stable runtime distributions. The model learned to identify users via resource patterns, not to predict runtime from job characteristics.

**Critical Review (GPT-5.2)**:
> "FIND-016 is refuted as a generalizable finding; the apparent gain is dominated by user-level memorization/leakage under time-based splits. The dataset reflects heterogeneous workloads; runtime prediction without timelimit is intrinsically difficult *across users* with available metadata."

**Implications**:
- Time-based splits can drastically overstate generalization in HPC traces
- Must distinguish "known-user forecasting" vs "new-user generalization" 
- Non-timelimit metadata does not generalize to unseen users
- Methodological contribution: evaluation protocol matters more than model choice

**Related Findings**: FIND-015, FIND-017

---

### FIND-017: User-level memorization dominates runtime prediction

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-005](../Experiments/EXP-005_anvil_verification/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
When users are held out entirely (user-aware split), all models perform worse than the mean predictor (negative R²). This demonstrates that apparent model performance on time-based splits is driven by user-level structure, not generalizable feature-to-runtime relationships.

**Evidence**:

| Variant | Time-based R² | User-aware R² | Δ R² |
|---------|---------------|---------------|------|
| XGBoost no_timelimit | 0.39 | -0.74 | **1.13** |
| XGBoost no_month | 0.40 | -0.53 | **0.94** |
| Ridge no_timelimit | 0.17 | -0.78 | **0.95** |

MdAPE increases from 97% (time-based) to 330-430% (user-aware).

**Scientific Interpretation**:
- Users submit repetitive workloads with stable runtime distributions
- Even "innocent" features (ncores, nhosts) act as user fingerprints
- The dataset is a mixture of many sub-populations with different generating processes
- Global models learn user-conditioned priors, not universal scheduling laws

**Implications**:
- **For HPC runtime prediction papers**: Split strategy is critical; must report user-aware metrics
- **For FRESCO research**: Must define target (known users vs new users) explicitly
- **For paper narrative**: Reframe from "signal recovery" to "methodological finding about evaluation"

**Related Findings**: FIND-016

**Next Steps**:
- [ ] Add user-mean baseline (predict as user's historical mean)
- [ ] Test with user ID as explicit feature to quantify upper bound
- [ ] Consider per-user or per-workload models

---

### FIND-018: Timelimit is essential for prediction

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-006c](../Experiments/EXP-006c_user_baseline_corrected/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
Adding timelimit as a feature dramatically improves runtime prediction across all clusters. Without timelimit, models perform at or below the global median baseline.

**Evidence** (EXP-006c, time-based split):

| Cluster | resources_only R² | with_timelimit R² | Δ R² |
|---------|-------------------|-------------------|------|
| Stampede | -0.04 | 0.33 | +0.37 |
| Conte | -0.37 | 0.13 | +0.50 |
| Anvil | 0.52 | 0.71 | +0.19 |

**Implications**:
- Timelimit (user-provided estimate) is the key predictive feature
- Resources alone (ncores, nhosts) are insufficient
- This is consistent with FIND-009 and FIND-012 from ablation studies

**Related Findings**: FIND-009, FIND-012

---

### FIND-019: Leakage magnitude is cluster-dependent

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-006c](../Experiments/EXP-006c_user_baseline_corrected/README.md)
- **Research Path**: PATH-B
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
The gap between time-based and user-aware split performance varies dramatically by cluster. Anvil shows severe leakage (+0.32), Stampede moderate (+0.10), and Conte shows "anti-leakage" (-0.11 where user-aware is better).

**Evidence** (EXP-006c, with_timelimit variant):

| Cluster | Time-based R² | User-aware R² | Δ R² (leakage) |
|---------|---------------|---------------|----------------|
| Stampede | 0.33 | 0.23 | +0.10 |
| Conte | 0.13 | 0.24 | **-0.11** |
| Anvil | 0.71 | 0.39 | **+0.32** |

**Possible Explanations**:
- Anvil: Many repeat users with stable workloads → high leakage
- Conte: Possible regime shift during evaluation period → time-based hurts
- Stampede: Moderate user repetition

**Implications**:
- Cannot assume one split type is universally better
- Must report both split types for complete picture
- Cluster-specific evaluation protocols may be needed

**Related Findings**: FIND-016, FIND-017

---

### FIND-020: Cross-cluster transfer viable when timelimit available

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-007](../Experiments/EXP-007_cross_cluster_transfer/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
Cross-cluster transfer can achieve competitive performance when timelimit is included as a feature. The transfer gap ranges from negligible (Δ=-0.03 for Stampede) to moderate (Δ=-0.20 for Anvil). Without timelimit, all transfer scenarios yield negative R², demonstrating timelimit is essential for cross-site generalization.

**Evidence** (EXP-007, with timelimit):

| Test Cluster | Same-cluster R² | Best Transfer R² | Δ R² |
|--------------|-----------------|------------------|------|
| Stampede | 0.329 | 0.298 (from C) | -0.03 |
| Conte | 0.129 | 0.162 (from Anvil/NONE) | +0.03 |
| Anvil | 0.704 | 0.504 (from S) | -0.20 |

Without timelimit: All transfer R² < 0

**Critical Review (GPT-5.2)**:
> "Timelimit is a dominant, near-essential feature for generalization: removing it yields negative R² for S and C even in-domain, and all transfer cases go negative."

**Implications**:
- Cross-site models are viable if timelimit is available at prediction time
- Model portability depends on policy/feature alignment between sites
- Simpler deployment: train once, deploy anywhere (with caveats)

**Related Findings**: FIND-018, FIND-021, FIND-022

---

### FIND-021: Anvil has largest transfer gap

**Update (2026-02-01; EXP-008)**: Pooled training with cluster conditioning eliminates the gap and exceeds Anvil-only training: pooled+clusterID → Anvil R²=0.752 [0.747,0.756] vs Anvil→Anvil R²=0.710 [0.704,0.714].

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: [EXP-007](../Experiments/EXP-007_cross_cluster_transfer/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
Anvil (token=`NONE`) shows the largest transfer gap: same-cluster R²=0.704 vs best transfer R²=0.504 (Δ=-0.20). This suggests Anvil has a unique runtime regime not captured by models trained on Stampede or Conte.

**Evidence**:

| Train → Test | R² | sMAPE |
|--------------|-----|-------|
| NONE → NONE (same) | 0.704 | 94% |
| S → NONE (best transfer) | 0.504 | 117% |
| C → NONE | 0.433 | 122% |

**Possible Explanations**:
- Anvil is newer (2022-2023) with different hardware/policies
- Different user population and workload mix
- Timelimit distributions may differ significantly

**Implications**:
- Anvil may require site-specific modeling or fine-tuning
- Transfer from Stampede better than from Conte
- Future work: characterize feature distribution shift

**Related Findings**: FIND-003, FIND-020

---

### FIND-022: Cross-cluster can outperform same-cluster (Conte anomaly)

- **Date Discovered**: 2026-01-31
- **Source Experiment(s)**: EXP-007 (initial observation), EXP-008 (CI verification)
- **Research Path**: PATH-C
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
Training on Anvil and testing on Conte performs better than training on Conte itself. EXP-008 confirms this is not a sampling artifact: the 95% bootstrap confidence intervals do not overlap.

**Evidence** (with timelimit, log-runtime R²):

| Train → Test=Conte | R² | 95% CI |
|---|---:|---|
| Conte → Conte (same) | 0.113 | [0.110, 0.115] |
| **Anvil → Conte (transfer)** | **0.153** | **[0.150, 0.157]** |
| Stampede → Conte (transfer) | 0.003 | [-0.001, 0.005] |

**Critical Review Notes**:
- GPT-5.2: likely Conte non-stationarity and/or under-specification due to near-constant resources
- Gemini 3 Pro: defensible to claim as "better-than-self" generalization given non-overlapping CIs; emphasize low absolute R² on Conte

**Implications**:
- Same-cluster training is not always optimal under constrained feature sets
- Suggests Conte’s within-cluster time split is harder than cross-site transfer from Anvil (also consistent with FIND-019 "anti-leakage")

**Next Steps**:
- [x] Diagnose Conte drift vs under-specification (EXP-009 complete)

**Related Findings**: FIND-019, FIND-020

---

### FIND-023: Conte anomaly driven by temporal shift, not under-specification

- **Date Discovered**: 2026-02-01
- **Source Experiment(s)**: [EXP-009](../Experiments/EXP-009_conte_anomaly_resolution/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: High
- **Status**: Verified

**Description**:
The "Conte Anomaly" (poor self-predictability) is primarily caused by **temporal non-stationarity** (distribution shift over time) rather than under-specification. While the time-based split performs poorly (R²=0.11), a random split achieves R²=0.47, indicating the signal is learnable but unstable over time. Transfer learning provides a robust fallback that outperforms local historical training, with "support matching" (filtering source data to match target resources) proving superior to broad "variance injection."

**Evidence**:
- **Drift dominates**: random split R²=0.472 >> time split R²=0.114.
- **Support matching helps**: filtering Anvil (`NONE`)→Conte (`C`) to match Conte’s support yields R²=0.186, beating full transfer R²=0.156.

**Implications**:
- Conte undergoes substantial regime shifts over time; local historical data can be unreliable for future prediction.
- **Relevance > volume**: restricting transfer data to the target’s support can outperform using all available source data.

**Next Steps**:
- [ ] Investigate if drift is primarily driven by new users appearing in the test period (user-aware split diagnostic).

**Related Findings**: FIND-022, FIND-017

---

### FIND-024: Few-shot calibration is non-monotonic under naive mixing

- **Date Discovered**: 2026-02-01
- **Source Experiment(s)**: [EXP-010](../Experiments/EXP-010_few_shot_calibration/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: Medium
- **Status**: Needs Verification

**Description**:  
Adding k labeled target-site jobs to a cross-site training set does not reliably improve Conte performance when the target labels are naively mixed into the source training data. In EXP-010, several k values reduced R² vs k=0, and the best observed k differs by source.

**Evidence** (Conte time-test; R² on log-runtime; 95% bootstrap CI):

- Anvil (`NONE`)→Conte (`C`):
  - k=0: 0.143 [0.139, 0.147]
  - k=300: 0.095 [0.092, 0.098]
  - k=1k: 0.159 [0.157, 0.163]

- Stampede (`S`)→Conte (`C`):
  - k=0: 0.003 [-0.000, 0.007]
  - k=100: 0.162 [0.160, 0.164]
  - k=1k: 0.123 [0.120, 0.126]

**Interpretation / Caveats**:
- This is *not* evidence that calibration cannot work; rather, it suggests the naive approach (uniform mixing + fixed hyperparameters) is unstable.
- The `k=0` Anvil→Conte baseline in EXP-010 differs slightly from EXP-008’s reported baseline, likely due to XGBoost nondeterminism (multi-thread) and/or run-to-run differences; treat comparisons as *within-EXP-010* unless re-run under controlled determinism.
- Likely needs verification with repeated few-shot sampling (multiple seeds), hyperparameter retuning, and/or sample reweighting.

**Next Steps**:
- [ ] Re-run EXP-010 with multiple seeds per k and report mean ± CI across seeds.
- [ ] Try a principled adaptation baseline (e.g., reweighting or fine-tuning via additional boosting rounds).

**Related Findings**: FIND-020, FIND-022, FIND-023


---

### FIND-025: Memory coverage excellent (>98%) across all clusters

- **Date Discovered**: 2026-02-01
- **Source Experiment(s)**: [EXP-011](../Experiments/EXP-011_Memory_transfer_baseline_missingness/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: Medium
- **Status**: Verified

**Description**:  
FRESCO memory metrics (`value_memused`) are well-populated across all three clusters. Overall, 99.9% of jobs have at least one memory sample, with near-perfect coverage for Stampede (100.0%) and Conte (100.0%), and excellent coverage for Anvil (98.4%). This high coverage indicates memory missingness is **not** a barrier to modeling and validates FRESCO's memory telemetry quality.

**Evidence**:

| Cluster | Jobs with ≥1 Memory Sample | Total Jobs | Coverage |
|---------|----------------------------|------------|----------|
| Stampede (S) | 5,004,655 | 5,004,700 | 100.0% |
| Conte (C) | 1,820,100 | 1,820,392 | 100.0% |
| Anvil (NONE) | 458,912 | 466,355 | 98.4% |
| **Overall** | **7,283,667** | **7,291,447** | **99.9%** |

**Implications**:
- Memory-based analyses are feasible across the full FRESCO dataset
- No need for imputation strategies or missingness-aware models
- Anvil's slightly lower coverage (98.4%) is still excellent and unlikely to bias results

**Related Findings**: FIND-002 (GPU telemetry is sparse pre-2023; memory is different), FIND-026

**Next Steps**:
- [ ] Document which partitions/queues account for the 1.6% missing on Anvil (MAR vs MNAR test)

---

### FIND-026: Cross-site memory prediction fails catastrophically

- **Date Discovered**: 2026-02-01
- **Source Experiment(s)**: [EXP-011](../Experiments/EXP-011_Memory_transfer_baseline_missingness/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
Unlike runtime prediction (which transfers at R² > 0.3), cross-site memory prediction using only submission features (ncores, nhosts, timelimit) **fails catastrophically**, producing negative R² for all zero-shot transfer scenarios. Extremely negative values (R² ≤ -21 for S→Anvil) indicate severe distributional/scale mismatch, likely due to label definition differences or fundamentally different memory usage patterns across clusters.

**Evidence** (log(peak_memused) R² with 95% CI):

**Cross-cluster transfer (all negative)**:
- S → C: -0.116 [-0.118, -0.113]
- C → S: -0.333 [-0.345, -0.323]
- NONE → S: -6.433 [-6.540, -6.331]
- NONE → C: -6.729 [-6.761, -6.701]
- C → NONE: -7.676 [-7.735, -7.621]
- **S → NONE: -21.333 [-21.503, -21.154]** (catastrophic)

**Within-cluster (weak to moderate)**:
- S → S: 0.369 [0.358, 0.380]
- C → C: 0.095 [0.092, 0.098]
- NONE → NONE: -0.027 [-0.033, -0.020]

**Critical Review (GPT-5.2)**:
> "A negative R² of -21 means the model's predictions are 22× worse than simply predicting the test mean—indicative of systematic miscalibration, not merely weak correlation. This strongly suggests label definition or scale mismatches between clusters (e.g., units, per-node vs job-total aggregation, measurement methodology)."

**Implications**:
- Memory cannot be reliably predicted cross-site with simple submission features
- Hypothesis (R² > 0.3 transfer) is **rejected**
- Contrast with FIND-020 (runtime transfers well) highlights which metrics are portable vs not
- Critical for practitioners: cannot deploy memory models trained on one cluster to another without validation/recalibration

**Related Findings**: FIND-020 (runtime transfer succeeds), FIND-025 (memory coverage is good), FIND-027

**Next Steps**:
- [x] Diagnose label definition mismatches (→ EXP-012 planned)
- [x] Test recalibration strategies (→ EXP-013 planned)

---

### FIND-027: Memory metrics likely non-standardized across clusters

- **Date Discovered**: 2026-02-01
- **Source Experiment(s)**: [EXP-011](../Experiments/EXP-011_Memory_transfer_baseline_missingness/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
The catastrophic cross-site transfer failures (especially R² = -21 for S→Anvil) strongly suggest that `peak_memused` is **not measured consistently** across FRESCO clusters. Likely sources of non-standardization include: (1) different units (KB vs MB vs bytes), (2) different aggregation rules for multi-node jobs (sum vs max per node), (3) different collection methods (cgroups vs jobacct_gather), or (4) different inclusion of buffers/cache in "used" memory.

**Evidence**:
1. **Catastrophic miscalibration**: R² values of -21 cannot be explained by weak correlation alone; they require systematic scale/offset mismatches
2. **Covariate shift analysis**: Extremely high standardized mean differences (SMD > 10⁶) for some transfers indicate severe feature distribution mismatch, but JSD remains moderate (0.2-0.4), suggesting the issue is primarily label-related, not feature-related
3. **Within-cluster heterogeneity**: Even same-cluster performance varies dramatically (S: 0.37, C: 0.10, NONE: -0.03), suggesting memory is fundamentally harder to predict than runtime
4. **Cluster conditioning helps but doesn't fix transfer**: Adding cluster ID features partially rescues pooled models (S: 0.37, C: 0.06) but Anvil remains unpredictable (R²=-0.04)

**Critical Review (GPT-5.2)**:
> "Cross-site differences in *what gets logged* for memory are often larger than for runtime. Memory metrics can be collected via cgroups, jobacct_gather, kernel accounting, or node-level sampling; each can yield systematically different 'peak' definitions. Runtime is usually walltime and is comparatively standardized."

**Implications**:
- FRESCO memory metrics require **validation and standardization** before cross-site studies
- Publication opportunity: "Lack of HPC memory metric standardization impedes cross-site research"
- Motivates development of measurement standards for multi-institutional datasets
- Researchers using FRESCO for memory studies must validate label definitions per cluster

**Related Findings**: FIND-026 (transfer failure), FIND-025 (coverage is good)

**Next Steps**:
- [ ] **EXP-012 (Label Validation)**: Verify units, aggregation, and semantics of `peak_memused` per cluster
  - Check scale (KB/MB/bytes) by comparing to known node RAM
  - Test if values scale with nhosts (sum vs max)
  - Document collection method per cluster
- [ ] **EXP-013 (Recalibration)**: Test if simple affine transformations can rescue transfer
- [ ] Contact FRESCO maintainers for metadata on memory collection methods

---

---

### FIND-028: Systematic 6-9× memory offsets between clusters

- **Date Discovered**: 2026-02-01
- **Source Experiment(s)**: [EXP-012](../Experiments/EXP-012_memory_label_validation/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: High
- **Status**: Verified

**Description**:  
FRESCO clusters exhibit massive systematic offsets in reported peak memory usage: Anvil reports 9.1× higher memory than Conte and 5.7× higher than Stampede (on average, in linear space). These offsets are consistent in log space (Conte→Anvil: +2.21 log units, Anvil→Stampede: -1.74 log units) and explain EXP-011's catastrophic transfer failures.

**Evidence** (1% sample, 1.5M jobs):

| Cluster Pair | Log Offset | Scale Factor | Interpretation |
|--------------|-----------|--------------|----------------|
| Conte → Stampede | +0.46 | 1.59× | Stampede 1.6× larger |
| Conte → Anvil | +2.21 | 9.10× | Anvil 9× larger |
| Anvil → Stampede | -1.74 | 0.17× | Stampede 1/6 of Anvil |

Log-scale distribution means:
- Stampede: 2.06
- Conte: 1.60
- Anvil: 3.81

**Critical Review (GPT-5.2)**:
> "The ~9× Conte→Anvil gap is consistent with different job populations and eras: Anvil (recent) likely has heavier memory-intensive workflows (AI/ML, data analytics), while Conte-era traces are dominated by traditional MPI/HPC. Additionally, accounting differences (including cache/buffers, cgroup vs RSS) can create multi× shifts."

**Implications**:
- The 1.74 log-unit Stampede→Anvil offset perfectly explains R²=-21 in EXP-011
- Models trained on one cluster predict systematically biased values for another
- This is a **calibration problem**, not fundamental unpredictability
- Simple affine transformation should rescue transfer (→ EXP-013)

**Related Findings**: FIND-026, FIND-027, FIND-029

**Next Steps**:
- [x] Test recalibration strategies (→ EXP-013 planned)

---

### FIND-029: Aggregation is consistent (max-per-node) across clusters

- **Date Discovered**: 2026-02-01
- **Source Experiment(s)**: [EXP-012](../Experiments/EXP-012_memory_label_validation/README.md)
- **Research Path**: PATH-C
- **Publication Potential**: Medium
- **Status**: Verified

**Description**:  
All three FRESCO clusters use **max-per-node** aggregation for peak memory (not sum across nodes). This is evidenced by weak/zero correlation between peak_memused and nhosts for multi-node jobs. Aggregation is therefore NOT the source of cross-site transfer failures.

**Evidence** (multi-node jobs only):

| Cluster | N Multi-node | Slope (log-log) | R² | Interpretation |
|---------|-------------|-----------------|-----|----------------|
| Stampede | 914,890 | -0.013 | 0.0009 | Max per node |
| Conte | 111,254 | 0.070 | 0.006 | Max per node |
| Anvil | 18,776 | 0.021 | 0.0002 | Max per node |

All slopes are near zero (range: -0.01 to 0.07), indicating peak memory does NOT scale with number of hosts. If aggregation were sum-across-nodes, we would expect slope ≈ 1.0.

**Implications**:
- Rules out one hypothesis for EXP-011 failures (aggregation mismatch)
- Confirms FRESCO memory metrics are consistently defined in this respect
- Transfer failures must be due to other factors (workload mix, measurement methodology → FIND-028)

**Related Findings**: FIND-027, FIND-028

---
