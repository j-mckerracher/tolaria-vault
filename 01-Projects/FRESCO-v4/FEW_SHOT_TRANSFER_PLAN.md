# FRESCO v4: Few‑Shot Cross‑Cluster Memory Prediction

**Last Updated**: 2026-07-16
**Owner**: jmckerra
**Status**: Draft plan (ready to execute)

## Executive Summary

FRESCO v3 ran ~70 experiments attempting **zero‑shot cross‑cluster memory prediction** (train on Anvil labels, predict on Conte with *no labeled target*). Every design failed:

- **Measurement non‑equivalence**: Anvil's `peak_memory_gb` includes page cache; Conte's does not. This creates an irreducible offset that no feature‑space alignment can fix without labels.
- **Feature poverty**: only 6 features survive the strict safe‑feature filter (`ncores`, `nhosts`, `timelimit_sec`, `runtime_sec`, `runtime_fraction`, and optionally `queue_time_sec`). This is too impoverished for reliable prediction, let alone transfer.
- **Era gap**: Conte is a 2015 CPU cluster; Anvil is a 2022 GPU/AI‑era cluster. Even within the `hardware_cpu_standard` regime, workload mixes and resource scales differ substantially.

v3's best result (EXP‑044/045, R² = 0.0878 on one frozen universe) collapsed under repeated seeds, denser sampling, CORAL, and quantile‑output adaptation. The zero‑shot claim is dead.

**FRESCO v4 relaxes the constraint to few‑shot**: allow **N labeled target examples** (N = 10–500) to calibrate a source‑trained model. This is **practically realistic** — HPC sites *can* instrument a small sample of jobs — and directly addresses the root cause by letting the calibration absorb measurement‑semantic and scale differences.

---

## Definitions (to avoid ambiguity)

### What "few‑shot" means here

We allow **N labeled target‑cluster examples** to be used for **calibration only**, not for primary model training. The source cluster provides the bulk of the labeled training data.

- **N**: the number of labeled target jobs available for calibration. Sweep values: **10, 25, 50, 100, 200, 500**.
- **Calibration set**: the N labeled target jobs, drawn by stratified seeded sampling from the overlap cohort.
- **Evaluation set**: the remaining target jobs in the overlap cohort, strictly held out from all calibration and training.

### What is allowed

- All source cluster labels (train the primary model)
- N target cluster labels (calibration / fine‑tuning only)
- All unlabeled target features
- Hardware metadata from `clusters.json` (node_memory_gb, node_cores, etc.)
- Non‑label target distribution summaries (feature histograms, etc.)

### What is NOT allowed

- Using held‑out target labels for anything — calibration and evaluation sets must be strictly separated
- Treating target labels as training data in the same way as source labels (except in the fine‑tune strategy, where the N labels are explicitly upweighted relative to source)
- Any form of data leakage from the evaluation set into model fitting

### Success Criteria

- **Tier A (primary)**: R² > 0 on the matched target regime at N ≤ 100, **stable across 3+ seeds**. This proves that a tiny labeled sample is enough to calibrate source knowledge.
- **Tier B (transfer value)**: Few‑shot + source beats target‑only at the same N. This proves that source data adds value beyond what the N labels alone provide.
- **Tier C (sample efficiency)**: Clear sample‑efficiency curve showing diminishing returns — i.e., performance gain per additional label decreases, and the curve plateaus before N = 500.

---

## Root Cause Diagnosis (inherited from v3)

### Why zero‑shot failed

v3's evidence is comprehensive:

1. **Measurement non‑equivalence**: Anvil's `peak_memory_gb` includes page cache; Conte's does not. The label semantics differ across clusters. No amount of feature alignment can correct a systematic label offset without at least some labeled target examples. (v3 EXP‑056/057/058/059 post‑hoc analysis confirmed source‑like predicted medians ~0.21 vs true target medians ~0.08.)

2. **Covariate shift**: even within the `hardware_cpu_standard` regime, feature distributions differ (KS > 0.9 on many features). Overlap coverage rarely exceeds 40%.

3. **Conditional shift**: E[y|x] differs across clusters even within overlapping feature support, as shown by large signed biases and negative calibration slopes in all zero‑shot experiments.

4. **Frozen‑universe instability**: results flip sign depending on which sampling universe is used (EXP‑044/045 positive on universe 1, EXP‑071/072/073/074 negative on universe 2).

### Why few‑shot addresses the root cause

Labeled target examples **directly encode the measurement‑semantic shift**. If Anvil's memory = Conte's memory + page cache, then a linear recalibration y_corrected = a·y_pred + b can absorb this offset with as few as 10–50 labeled pairs. The few‑shot setting turns an impossible unsupervised problem into a straightforward supervised correction.

### References

- `FRESCO-v3/ZERO_SHOT_CROSS_CLUSTER_TRANSFER_PLAN.md` — full v3 evidence
- `FRESCO-v3/docs/WORKLOAD_TAXONOMY_AND_MATCHING.md` — regime definitions
- `FRESCO-v3/experiments/` — all v3 experiment configs and results

---

## Calibration Strategies

### 1. Output Recalibration (primary)

Train the primary model on all source labels. Generate predictions ŷ for the N labeled target calibration jobs. Fit a linear correction:

    y_true = a · ŷ + b

Only **2 parameters** (slope a, intercept b) — works even at very small N.

**Variant**: Bayesian recalibration with informative prior a ≈ 1, b ≈ 0 (expect the source model to be approximately correct up to an offset). This regularizes the correction at very small N (10–25) where OLS may overfit.

### 2. Fine‑Tune

Train the primary model on source labels. Then re‑fit on the combined dataset {source ∪ N_target} with the target examples upweighted:

    w_target = len(source) / N

This gives the N target examples equal aggregate influence to the entire source dataset. The model retains source knowledge but adapts its coefficients to the target distribution.

### 3. Stacked / Blended

Use the source model's predictions as an additional feature for a second‑stage model trained on the N target labels:

    second_stage_features = [ŷ_source, x_features]
    second_stage_model.fit(second_stage_features[calibration], y_true[calibration])

This allows nonlinear corrections and feature reweighting, but requires more parameters — may need N ≥ 50.

### 4. Target‑Only Baseline (critical control)

Train a model on the N target labels alone. No source data. This is the **essential control** for measuring whether transfer adds value. If target‑only at N = 50 beats few‑shot + source at N = 50, then source data is hurting, not helping.

### 5. Zero‑Shot Baseline (N = 0)

Same as v3's best design (regime‑matched, safe features, `peak_memory_fraction`, Ridge). Provides the reference point that few‑shot must beat.

### 6. Full‑Target Upper Bound (ceiling)

Train on the full target training set (all target labels in the overlap cohort except the evaluation holdout). This is the ceiling that no few‑shot method should exceed.

---

## Detailed Workplan

### Phase 0 — Inherit v3 Infrastructure

**Goal**: reuse all v3 data, scripts, and frozen artifacts without modification.

- Reuse authoritative `chunks-v3` dataset on Gilbreth: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/`
- Reuse `config/clusters.json` hardware metadata
- Copy core scripts from v3:
  - `fresco_data_loader.py` — data loading, job‑level aggregation, safe‑feature filtering
  - `regime_matching.py` — overlap cohort construction, domain classifier
  - `freeze_sampling_plan.py` — frozen‑universe sampling
  - `model_transfer.py` — source model training and evaluation
- Reuse v3 frozen sampling plans where applicable (e.g., `frozen_sampling_plan_exp044_hwcpu_standard_300k_24_seed1337.json`)
- Retain v3's canonical evaluation split protocol and metrics

**Acceptance**: v3 scripts run unmodified in the v4 environment. Data paths resolve. Frozen plans load without error.

---

### Phase 1 — Reproduce v3 Zero‑Shot Negative (sanity check)

**Goal**: confirm that the v4 environment reproduces v3 results before adding anything new.

- **EXP‑001**: Regime matching
  - Regime: `hardware_cpu_standard`
  - Features: `[ncores, nhosts, timelimit_sec, runtime_sec, runtime_fraction]` (no `queue_time_sec`)
  - Direction: Anvil → Conte
  - Seed: 1337
  - Overlap band: [0.2, 0.8]
  - Expected: overlap AUC ~0.94, coverage ~33%

- **EXP‑002**: Zero‑shot transfer (N = 0 baseline)
  - Model: Ridge
  - Label: `peak_memory_fraction`
  - Expected: target R² near 0.09 ± tolerance (matching v3 EXP‑062/063)

**Acceptance**: metrics match v3 within tolerance (R² within ±0.02, AUC within ±0.01). If they do not match, diagnose before proceeding.

---

### Phase 2 — Few‑Shot Calibration Sweep (main result)

**Goal**: the central experiment of v4. Sweep calibration strategies × N × seeds.

#### Design

For each **strategy** in {output_recal, fine_tune, stacked, target_only}:
  For each **N** in {10, 25, 50, 100, 200, 500}:
    For each **seed** in {1337, 2024, 2025}:

1. Load the frozen overlap cohort from Phase 1.
2. Draw N labeled target jobs by **stratified seeded sampling** from the overlap cohort (stratify on `peak_memory_fraction` quartiles).
3. Hold out all remaining target jobs in the overlap cohort for evaluation.
4. Train the source model on all Anvil labels (Ridge on safe features, same as v3).
5. Apply the calibration strategy using the N labeled target jobs.
6. Evaluate on the held‑out target evaluation set.
7. Report:
   - R² (primary metric)
   - MAE(log), MdAE(log)
   - Bootstrap 95% CI for R²
   - Calibration slope and intercept
   - Strategy, N, seed as metadata

#### Run budget

- 4 strategies × 6 N‑values × 3 seeds = **72 runs**
- Plus 3 zero‑shot baselines (N = 0, 3 seeds) = **3 runs**
- Plus 3 full‑target upper bounds (3 seeds) = **3 runs**
- **Total: 78 runs**

#### Implementation

- Script: `scripts/few_shot_transfer.py`
  - Accepts a JSON config specifying strategy, N, seed, data paths, feature set, label
  - Outputs: `results/metrics.json`, `results/predictions.parquet`, `results/calibration_params.json`
- Config generator: `scripts/generate_sweep_configs.py`
  - Produces all 78 configs in `experiments/EXP-003_few_shot_sweep/configs/`
- SLURM batch: `scripts/submit_sweep.sh`
  - Submits all configs as a job array

**Acceptance**: all 78 runs complete. All metrics computed (no NaN). Results saved to `experiments/EXP-003_few_shot_sweep/results/`.

---

### Phase 3 — Analysis

**Goal**: synthesize the sweep into clear conclusions.

#### 3.1 Sample Efficiency Curve

- Plot: N (x‑axis) vs R² (y‑axis), one curve per strategy.
- Include: zero‑shot baseline as horizontal line at N = 0; full‑target upper bound as ceiling.
- Error bars: bootstrap 95% CI.

#### 3.2 Break‑Even Analysis

- At what N does **few‑shot + source** beat **target‑only**?
- If no break‑even exists (target‑only always wins), document this clearly — source data has no value.

#### 3.3 Stability Analysis

- Variance of R² across seeds at each N.
- Are results seed‑stable at all N, or only at large N?
- Compare to v3's instability (where different frozen universes flipped the sign).

#### 3.4 Regime Matching Value

- Compare matched (overlap cohort) vs unmatched (all target jobs) at the same N.
- Does regime matching still help in the few‑shot setting, or do the N labels make it unnecessary?

#### 3.5 Calibration Diagnostics

- Inspect learned (a, b) parameters from output recalibration across N.
- Do they converge to stable values as N increases?
- Is the correction roughly what we'd expect from the measurement non‑equivalence (page cache offset)?

**Acceptance**: clear figures, tables, and statistical conclusions for each of 3.1–3.5. At minimum, produce the sample‑efficiency curve plot and the break‑even table.

---

### Phase 4 — Second Cluster Pair + Publication

**Goal**: test generalization beyond Anvil → Conte and prepare for publication.

- Identify a second cluster pair with sufficient overlap (candidates: temporal split within Anvil, or Stampede → Conte if data quality supports it).
- Repeat Phase 2 sweep on the second pair (or a reduced version: best strategy only, N ∈ {25, 100, 500}, 3 seeds).
- If second pair confirms the pattern: write up as a general few‑shot calibration result.
- If second pair shows different behavior: document the conditions under which transfer succeeds/fails.

#### Publication Artifacts

- Final tables: strategy × N × metric (R², MAE, CI)
- Final plots: sample efficiency curves, break‑even plots, calibration diagnostics
- Paper draft: extend v3 narrative ("zero‑shot fails → few‑shot rescues transfer with N ≤ 100 labels")
- Reproducibility: all configs, frozen plans, scripts, SLURM logs archived

**Acceptance**: paper‑ready results with full reproducibility artifacts. All claims backed by experiments across at least 2 cluster pairs (or temporal splits) with 3+ seeds each.

---

## Risks & Mitigations

### Risk 1: N target labels is still not enough

**Scenario**: even at N = 500, few‑shot + source doesn't reach R² > 0.

**Mitigation**: the sample efficiency curve is itself the result — even a negative result at small N with positive at larger N is informative. If N = 500 still fails, the problem is not calibration but fundamental model inadequacy. Document and publish as a negative result.

### Risk 2: Target‑only beats transfer at all N

**Scenario**: source data actively hurts. Target‑only at N = 50 outperforms few‑shot + source at N = 50.

**Mitigation**: document this honestly — it means source data has no value for cross‑cluster transfer. This is still a publishable and practically important finding. Consider whether richer features or different source models could reverse this.

### Risk 3: Results are seed‑unstable (again)

**Scenario**: R² varies wildly across seeds at the same N, as in v3.

**Mitigation**: use 3+ seeds per data point and report confidence intervals. If instability persists even at N = 200+, the underlying overlap cohort may be too small or too heterogeneous — investigate cohort size and composition.

### Risk 4: Measurement semantics gap is nonlinear

**Scenario**: the page cache offset is not a simple a·ŷ + b correction — it depends on workload type, memory pressure, or I/O intensity in nonlinear ways.

**Mitigation**: this is the key test of the output recalibration strategy. If linear (a, b) fails but the stacked/blended strategy (which allows nonlinear correction) succeeds, that confirms the nonlinearity. If both fail, the measurement gap is more fundamental than expected. Either way, it's a clear research finding.

---

## Concrete Next Steps

1. ✅ Set up FRESCO‑v4 folder structure
2. ⬜ Write `scripts/few_shot_transfer.py` — core calibration script
3. ⬜ Write `scripts/generate_sweep_configs.py` — config generator for all 78 runs
4. ⬜ Run Phase 1 sanity check (EXP‑001 regime matching, EXP‑002 zero‑shot baseline)
5. ⬜ Run Phase 2 sweep (72 + 6 = 78 runs on Gilbreth)
6. ⬜ Run Phase 3 analysis and produce figures
7. ⬜ Identify second cluster pair and run Phase 4
8. ⬜ Write up results for publication
