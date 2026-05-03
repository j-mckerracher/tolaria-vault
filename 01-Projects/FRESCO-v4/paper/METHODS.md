# Methods (Draft): Few-Shot Cross-Cluster Transfer for HPC Memory Prediction

**Last Updated**: 2026-03-13

## Overview
This section is written in a paper-ready style and must be kept synchronized with:
- code commit hashes (pinned via `capture-code-version`)
- configuration files (experiment configs under `config/`)
- run manifests (input/output manifests, run metadata)

All methods build on the FRESCO v3 pipeline. The novel contribution is the few-shot calibration framework layered on top of the v3 extraction, transformation, and regime-matching infrastructure.

---

## Pipeline (Inherited from v3)

The data pipeline follows five stages, unchanged from v3:

1. **Extraction**: Parse raw scheduler logs and telemetry shards into job-level records. Each cluster has a dedicated extractor that produces a standardized intermediate representation.
2. **Transformation**: Normalize time and memory measures, attach hardware metadata from `config/clusters.json`, enforce consistent units (GB for memory, seconds for time).
3. **Schema enforcement**: Union-by-name across clusters with explicit dtype casts. The canonical schema is defined in `config/canonical_schema.json` and enforced by validators.
4. **Validation**: Schema validation (dtype, nullability), sanity checks (non-negative values, plausible ranges), and cross-field consistency (e.g., runtime ≤ timelimit).
5. **Output**: Hourly parquet shards under a unified directory structure with provenance metadata.

Reference: See v3 `METHODS.md` and pipeline documentation for full details.

---

## Memory Normalization

We define the normalized memory target as:

```
peak_memory_fraction = peak_memory_gb / (node_memory_gb × nhosts)
```

Where:
- `peak_memory_gb`: peak memory usage in GB, derived from `value_memused_max` in the production parquet (already GB-scale).
- `node_memory_gb`: per-node physical memory capacity, recovered at analysis time from `config/clusters.json` keyed by cluster and partition.
- `nhosts`: number of nodes allocated to the job.

This normalization maps memory usage to the fraction of total allocated memory, making values comparable across hardware configurations with different node capacities.

**Provenance metadata**: Each record carries `memory_includes_cache` (boolean), `memory_collection_method` (cgroup | accounting | metrics), and `partition` (recovered from the raw `queue` field). These fields enable downstream consumers to assess measurement comparability.

**Important caveat**: `memory_includes_cache` differs across clusters (Conte includes page cache; Anvil does not). This is a known measurement non-equivalence documented in `THREATS_TO_VALIDITY.md`.

---

## Regime Matching

Cross-cluster comparisons are restricted to matched regimes to reduce covariate shift:

1. **Hardware regime**: `hardware_cpu_standard` — CPU-only partitions with standard node configurations. GPU and high-memory partitions are excluded.
2. **Propensity overlap filter**: A domain classifier (logistic regression) is trained to distinguish source from target using the 5-feature set. Jobs with propensity scores in [0.2, 0.8] are retained; those outside this range are too easily identifiable as belonging to one cluster and are excluded.
3. **5-feature set**: The features used for regime matching and the domain classifier are:
   - `ncores` — number of CPU cores requested
   - `nhosts` — number of nodes allocated
   - `timelimit_sec` — walltime limit in seconds
   - `runtime_sec` — actual runtime in seconds
   - `runtime_fraction` — runtime / timelimit (resource utilization proxy)

Even after regime matching, domain classifier AUC ≈ 0.93 (from v3 EXP-001/002), indicating that features alone encode cluster identity. This motivates labeled calibration rather than zero-shot transfer.

---

## Few-Shot Transfer Formulation

### Setting
- **Source dataset S**: A fully labeled cluster (e.g., Conte) with features X_S and targets y_S.
- **Target dataset T**: A target cluster (e.g., Anvil) with N labeled examples T_N for calibration and |T| − N examples for evaluation.
- **Goal**: Learn a predictor that generalizes to the target evaluation set using the source model and N target labels.

### Procedure
1. Train base model f on source S (Ridge regression with pre-registered feature set).
2. Generate predictions f(x) for the N calibration examples from T.
3. Learn a calibration function g from the N (f(x), y) pairs (strategy-dependent; see below).
4. Apply g∘f to the held-out target evaluation set T \ T_N.
5. Report evaluation metrics on T \ T_N only (never on the calibration set).

### Calibration Set Selection
The N calibration examples are drawn by stratified random sampling from T, stratified on `workload_regime` (if available) or uniformly at random. The seed is fixed and recorded in the run config. Multiple seeds (default: 3) are used to assess stability.

---

## Calibration Strategies

### Strategy 1: Output Recalibration (OLS)
The simplest approach: fit a linear correction to the source model's predictions.

```
ŷ_cal = a · f(x) + b
```

Where (a, b) are estimated by ordinary least squares on the N calibration pairs {(f(x_i), y_i) : i = 1..N}. This corrects systematic bias (b ≠ 0) and scale mismatch (a ≠ 1) but cannot reweight features or learn non-linear corrections.

**Degrees of freedom**: 2 (a and b). Applicable even at very small N (≥ 3).

### Strategy 2: Fine-Tuning (Weighted Ridge)
Retrain the Ridge model on the combined source and target calibration data with sample weights:

```
f_ft = Ridge(X_S ∪ X_{T_N}, y_S ∪ y_{T_N}, weights = [w_s, ..., w_s, w_t, ..., w_t])
```

Where w_t > w_s to upweight the target calibration examples. The weight ratio w_t/w_s is a hyperparameter (default: |S|/N to equalize effective sample sizes). This allows feature coefficients to shift toward the target distribution.

**Regularization**: Ridge penalty α is selected by cross-validation on the combined dataset.

### Strategy 3: Stacking (Ridge on Predictions + Features)
Train a second-level Ridge model that combines the source model's predictions with raw features:

```
ŷ_stack = Ridge([f(x), x], y)  fitted on N calibration pairs
```

This allows the stacker to (a) trust the source model where it's accurate, (b) override it using raw features where it's not, and (c) learn target-specific feature interactions.

**Risk**: At small N, the stacker has many features (1 + d) relative to N examples. Ridge regularization mitigates overfitting, but performance may degrade below N ≈ 50.

### Strategy 4: Target-Only Baseline (Ridge on T_N)
Train Ridge regression using only the N target calibration examples, ignoring the source model entirely:

```
f_target = Ridge(X_{T_N}, y_{T_N})
```

This is the lower bound on what N labels alone can achieve without transfer. At small N (< 50), this baseline is disadvantaged because Ridge needs N >> d features to fit reliably. At large N, it may match or exceed transfer strategies if the source model provides little useful signal.

**Regularization**: Strong Ridge penalty (large α) at small N to prevent overfitting. α selected by leave-one-out cross-validation.

---

## Evaluation Protocol

### Metrics
All metrics are computed on the held-out target evaluation set (T \ T_N):

- **R²**: Coefficient of determination. Primary metric for overall prediction quality.
- **MAE(log)**: Mean absolute error in log-transformed space. Robust to outliers, interpretable as multiplicative error.
- **Bootstrap 95% CI**: 1000 bootstrap resamples of the evaluation set. Reported for both R² and MAE(log).
- **Calibration slope**: Slope of predicted vs actual in log-space. Ideal = 1.0. Deviations indicate systematic miscalibration.

### Baselines
Every few-shot result is reported alongside:
- **Zero-shot (N = 0)**: Source model applied directly to target without calibration (v3 regime-matched transfer).
- **Target-only at same N**: Ridge on T_N alone (Strategy 4).
- **Full-target upper bound**: Ridge trained on the full target train split.

### Reporting Requirements
Every result table entry must include:
- N (calibration set size)
- Strategy name
- Calibration parameters learned (a, b for OLS; α for Ridge variants)
- Held-out evaluation metrics (R², MAE(log), bootstrap CI)
- Zero-shot baseline metrics
- Target-only baseline metrics at the same N

---

## Reproducibility

Every experiment run produces:
- **Input manifest** (`input_manifest.jsonl`): lists all input files with SHA-256 hashes.
- **Output manifest** (`output_manifest.jsonl`): lists all output files with SHA-256 hashes.
- **Run metadata** (`run_metadata.json`): config, git commit, environment lock, timestamps.
- **Validation report**: schema conformance and sanity check results.
- **Environment lock**: `pip freeze` and conda export for exact package versions.

This enables full third-party reproduction. See `ARTIFACTS_AND_REPRO_GUIDE.md` for step-by-step instructions.
