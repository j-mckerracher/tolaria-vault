# FRESCO v3: Path to Zero‑Shot Cross‑Cluster Memory Prediction

**Last Updated**: 2026-03-12
**Owner**: jmckerra  
**Status**: Draft plan (ready to execute)

## Executive Summary

EXP-014/015 show that **v2.0 fixed schema + normalization**, but **zero‑shot transfer** (train on cluster A labels, predict on cluster B with *no labeled target*) still fails badly (R² 
 0) because the clusters are not i.i.d.:

- **Severe covariate shift** (e.g., partition/node_type completely non‑overlapping; KS up to 1.0)
- **Conditional shift** (the mapping \(E[y|x]\) differs by cluster)
- **Era / workload regime shift** (Conte 2015 CPU era vs Anvil 2022 GPU/AI era)

A path forward exists, but it requires **changing the problem definition** from “global transfer across all jobs” to one of the following:

1. **Zero‑shot transfer within *matched regimes*** (CPU‑only ↔ CPU‑only; comparable partitions; overlapping feature support)
2. **Domain adaptation using unlabeled target data** (still zero‑label, but not zero‑data): distribution alignment / calibration
3. **Learning invariant representations** using richer signals (time‑series/perf metrics) rather than allocations only

This document provides a concrete execution plan to deliver **the strongest defensible version of zero‑shot cross‑cluster prediction**.

## Authoritative status update (2026-03-12)

The authoritative `chunks-v3` reruns are now complete enough to sharpen the plan:

- EXP-039 confirmed the authoritative strict safe-feature path and supports using:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`
- EXP-040/041 (alloc + perf overlap features) remained too separable and transferred very poorly:
  - overlap AUC = `0.9962`
  - target overlap coverage = `25.94%`
  - target `R^2 = -11.8921`
- EXP-042/043 (strict safe-feature overlap) improved the situation, but not enough:
  - overlap AUC = `0.9369`
  - target overlap coverage = `33.18%`
  - target `R^2 = -4.2053`
- We now recover hardware metadata at analysis time via `config/clusters.json`:
  - `partition := queue`
  - `node_type`, `node_cores`, `node_memory_gb`, `gpu_count_per_node`, `gpu_model` recovered from cluster defaults + Anvil partition mappings
  - `peak_memory_fraction := peak_memory_gb / (node_memory_gb * nhosts)`
- EXP-044/045 (hardware CPU-standard regime + normalized `peak_memory_fraction`) produced the first positive authoritative transfer baseline:
  - overlap AUC = `0.9398`
  - target overlap coverage = `33.04%`
  - target `R^2 = 0.0878`
  - bootstrap 95% CI = `[0.0556, 0.1132]`
- The no-queue-time follow-up is now staged locally with a shared frozen sampling plan but **not yet submitted**:
  - rationale: `queue_time_sec` appears to encode scheduler/cluster behavior rather than workload similarity, and it remained badly mismatched within overlap in EXP-044 even after the hardware CPU-standard regime filter
  - goal: keep the EXP-044/045 and EXP-046..051 baseline/repeat design fixed while dropping only `queue_time_sec` from both Phase 2 and Phase 3 `feature_columns`
  - frozen plan artifact: `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp044_hwcpu_standard_300k_24_seed1337.json`
  - frozen plan summary: reuse the EXP-044 `300k / 24` sampling regime with fixed row-group universes for Anvil (`286,843` raw rows -> `13,260` jobs) and Conte (`131,122` raw rows -> `7,383` jobs)
  - renumbering note: the originally requested EXP-052..059 range is already occupied by immutable committed dense-sampling and alloc-only diagnosis runs, so the planned family is staged as EXP-062..069 instead
  - runnable set: `EXP-062` plus `EXP-063/065/067/069`; `EXP-064/066/068` are retained only as provenance placeholders because the frozen plan makes the regime stage deterministic
- Repeated-seed validation then showed that this baseline is not yet stable:
  - EXP-046/047 (seed `2024`): overlap AUC `0.9394`, coverage `26.92%`, target `R^2 = -0.0346`, bootstrap 95% CI `[-0.0741, -0.0063]`
  - EXP-048/049 (seed `2025`): overlap AUC `0.9073`, coverage `58.89%`, target `R^2 = -2.1030`, bootstrap 95% CI `[-2.3111, -1.9280]`
  - EXP-050/051 (seed `2026`): overlap AUC `0.9271`, coverage `40.37%`, target `R^2 = -0.2882`, bootstrap 95% CI `[-0.3788, -0.2020]`
- Denser-sampling stabilization attempts also stayed negative:
  - EXP-052/053 (seed `1337`, `max_rows=600000`, `sample_n_row_groups_per_file=128`): overlap AUC `0.9378`, coverage `37.36%`, target `R^2 = -0.8817`, bootstrap 95% CI `[-0.9372, -0.8255]`
  - EXP-054/055 (seed `2024`, same dense-sampling controls): overlap AUC `0.9536`, coverage `24.25%`, target `R^2 = -0.1047`, bootstrap 95% CI `[-0.1272, -0.0881]`
- Simplifying to alloc-only overlap features plus Huber also failed:
  - EXP-056/057 (seed `1337`): overlap AUC `0.8571`, coverage `82.52%`, target `R^2 = -0.6492`, bootstrap 95% CI `[-0.6831, -0.6182]`
  - EXP-058/059 (seed `2024`): overlap AUC `0.8607`, coverage `83.03%`, target `R^2 = -1.4949`, bootstrap 95% CI `[-1.5563, -1.4371]`
- Post-hoc label-semantics diagnosis on the saved prediction artifacts showed why those dense alloc-only runs failed:
  - true Conte target medians were much lower (`0.074` / `0.086`) than the Anvil source-test median (`~0.205`)
  - alloc-only Huber still predicted source-like target medians (`0.209` / `0.259`)
  - a simple `log(4)` node-memory correction made target `R^2` much worse, so the error is not explained by a hidden constant denominator shift alone
- Decoupling Phase 2 and Phase 3 feature sets also failed to rescue transfer:
  - EXP-060 (seed `1337`, alloc-only overlap + restored safe-full Ridge model): source-test `R^2 = 0.0121`, target `R^2 = -1.5721`, bootstrap 95% CI `[-1.6360, -1.5091]`
  - EXP-061 (seed `2024`, same decoupled design): source-test `R^2 = 0.0359`, target `R^2 = -0.8824`, bootstrap 95% CI `[-0.9218, -0.8433]`

Conclusion: narrowing to safer overlap features alone was not enough, and adding recovered hardware metadata plus normalized `peak_memory_fraction` can produce a positive Anvil -> Conte split, but repeated-seed, denser-sampling, alloc-only/Huber, and decoupled-feature follow-ups all show that the current baseline is still too unstable for a claim.

---

## Definitions (to avoid ambiguity)

### What “zero‑shot” means here
- **Allowed**: 
  - Labeled source cluster data (train)
  - Unlabeled target cluster features (for adaptation/alignment)
  - Hardware metadata (node_memory_gb, node_type, gpu_count_per_node)
  - Non‑label target distribution summaries (e.g., feature histograms)
- **Not allowed**:
  - Using any labeled target jobs to fit parameters (no fine‑tuning, no calibration fit on target labels)

### Success Criteria
We should define tiered success metrics:

- **Tier A (realistic)**: R² > 0 on *matched* target regime (CPU↔CPU subset), stable across repeated splits, with uncertainty bounds.
- **Tier B (stretch)**: R² > 0 for broader target workloads but not necessarily the full distribution.
- **Tier C (unlikely)**: R² > 0 for the full Conte↔Anvil distribution without any regime matching.

---

## Root Cause Diagnosis (from EXP-015)

### Evidence of covariate shift
- partition KS = 1.00 (disjoint)
- node_type KS 
 0.999 (disjoint)
- log_ncores KS 
 0.88 (extreme)

**Implication**: models are extrapolating outside training support. Tree models in particular extrapolate poorly.

### Evidence of conditional / label shift
Transfer models show **large signed bias** in log space (e.g., +1.61, -2.31), and negative calibration slopes.

**Implication**: even within overlapping support, the mapping differs (measurement semantics and workload structure differ).

---

## Proposed v3 Strategy

We pursue three parallel tracks and merge outcomes:

### Track 1 — Regime‑Matched Zero‑Shot (high probability)
**Goal**: Make zero‑shot feasible by restricting evaluation to overlapping regimes.

Key idea: if Anvil contains CPU partitions and CPU‑like jobs comparable to Conte, transfer becomes an *inter‑site* problem rather than *inter‑era/architecture*.

Deliverables:
- A **workload taxonomy** shared across clusters (CPU, GPU, largemem, etc.)
- A **matched cohort builder** that constructs comparable train/test splits by *feature support overlap*.

### Track 2 — Unlabeled Domain Adaptation (medium probability)
**Goal**: Use unlabeled target features to align distributions (zero‑label).

Candidate methods:
- **CORAL** (covariance alignment) on standardized continuous features
- **MMD** minimization in latent space (kernel alignment)
- **Domain‑adversarial representation learning (DANN)** (requires NN)
- **Quantile mapping / distribution matching** of model outputs (unsupervised calibration)

### Track 3 — Richer Predictors (medium probability)
**Goal**: Use features that are more universal across clusters than scheduler metadata.

Candidate features (prefer those available in all clusters):
- value_cpuuser (and optionally nfs/block)
- runtime_fraction / runtime_efficiency
- failure/timed_out indicators

If available as time series/snapshots, derive robust aggregates:
- median/95p CPU usage
- I/O intensity bins
- “job signature” clusters via unsupervised embeddings

---

## Detailed Workplan

### Phase 0 — v3 Repo Structure & Baselines
- [x] Create `FRESCO-v3` workspace structure:
  - `experiments/`
  - `docs/`
  - `scripts/`
  - `results/`
- [x] Copy forward EXP-015 as baseline reference (frozen)
  - Snapshot copied to: `01-Projects/FRESCO-v3/experiments/EXP-015_baseline/source/`
  - Replay reproducer (single command): `python scripts\\reproduce_exp015_baseline.py --config experiments\\EXP-015_baseline\\config\\reproduce_exp015_baseline.json`
  - Limitations: this reproducer regenerates baseline *artifacts* from the frozen snapshot; it does not recompute EXP-015 from raw shards because the referenced scripts/logs are not present in the snapshot.
- [x] Define one canonical evaluation split protocol (seeded, reproducible)
  - Documented in: `paper/EXPERIMENTS_AND_EVAL.md` (“Canonical split protocol (v3 default)”).
- [x] Copied authoritative schema PDF from Gilbreth:
  - `docs/FRESCO_Repository_Description.pdf`
- [x] Sampled source data headers on Gilbreth (Action 2 in v2 quick start):
  - Anvil: JobAccounting + JobResourceUsage sample headers
  - Conte: `TACC_Stats/2015-03/cpu.csv` header
  - Stampede: `TACC_Stats/NODE1/cpu.csv` header

**Acceptance (Phase 0)**: EXP-015 baseline artifacts + summary can be regenerated from v3 with a single command, and the v3 evaluation split protocol is explicitly documented.

---

### Phase 1 — Feature Availability Matrix (All Clusters)
- [x] Build a script to compute:
  - intersection of columns across clusters
  - per‑cluster missingness rates for candidate features
  - type stability checks (parquet schema drift)
- [x] Produce `docs/feature_matrix.md` (run: `experiments\EXP-016_feature_matrix\`)

**Acceptance**: we have a vetted list of features safe for cross‑cluster modeling (see `docs\feature_matrix.md`).

---

### Phase 2 — Workload Taxonomy + Regime Matching
#### 2.1 Define a common taxonomy
- CPU vs GPU vs largemem vs unknown
- Derive from:
  - gpu_count_per_node, gpus_allocated, gpu_model
  - node_type
  - node_memory_gb / node_cores
  - partition (mapped per cluster into taxonomy)

#### 2.2 Overlap‑aware cohort construction
Implemented local-proxy overlap workflow:
- Script: `scripts\regime_matching.py`
- Run folder: `experiments\EXP-017_regime_matching\`
- Method: propensity (domain classifier) overlap with band **[0.2, 0.8]**
- Regime: `cpu_standard` (local proxy definition; see EXP-017 run log)

Key outputs:
- Overlap report: `experiments\EXP-017_regime_matching\results\overlap_report.json`
- Matched cohorts (indices):
  - `...\results\matched_source_indices.parquet`
  - `...\results\matched_target_indices.parquet`

**Acceptance**: cohort builder + overlap report exist and quantify coverage/shift (AUC, KS).

---

### Phase 3 — Modeling for Zero‑Shot
#### 3.1 Models to try (in order)
1. **Regularized linear / GAM** (better extrapolation than trees)
2. **Monotonic XGBoost** (constrain directions; improves stability)
3. **Quantile regression** (robust to heteroscedasticity)
4. **Neural net + DANN** (if Track 2 needed)

#### 3.2 Objective
Predict:
- \(y = \log(peak\_memory\_fraction)\)

#### 3.3 Report metrics
- R², MAE(log), MdAE(log), SMAPE
- Bias (mean residual)
- Calibration slope/intercept
- Uncertainty: bootstrap CI for R²

#### Phase 3 progress (local proxy)
- Baseline run (allocations-only, proxy label): `experiments\\EXP-019_modeling_alloc_only\\`
  - Repro: `python scripts\\model_transfer.py --config experiments\\EXP-019_modeling_alloc_only\\config\\exp019_modeling_alloc_only.json`
  - Result: Target (Conte) R² is strongly negative on proxy label; see `...\\results\\metrics.json`.

- Job-level rerun (allocations-only; fixes duplicate-jid weighting):
  - Phase 2 overlap: `experiments\\EXP-022_regime_matching_alloc_only_joblevel\\`
    - Key numbers: AUC≈0.8025, Conte overlap coverage=1.0.
  - Phase 3 modeling: `experiments\\EXP-023_modeling_alloc_only_joblevel\\`
    - Result: Target R²≈-30.21 on proxy label.

- Ablation run (alloc + perf aggregates, **exclude memused**; job-level aggregation):
  - Phase 2 overlap: `experiments\\EXP-020_regime_matching_alloc_perf_nomem\\`
    - Repro: `python scripts\\regime_matching.py --config experiments\\EXP-020_regime_matching_alloc_perf_nomem\\config\\exp020_regime_matching_alloc_perf_nomem.json`
    - Key numbers: AUC≈0.9895, Conte overlap coverage≈0.321 (see `...\\results\\overlap_report.json`).
  - Phase 3 modeling: `experiments\\EXP-021_modeling_alloc_perf_nomem\\`
    - Repro: `python scripts\\model_transfer.py --config experiments\\EXP-021_modeling_alloc_perf_nomem\\config\\exp021_modeling_alloc_perf_nomem.json`
    - Result: extremely negative target R² on proxy label (see `...\\results\\metrics.json`).

- Overlap-band sensitivity (alloc+perf, no memused; job-level):
  - Phase 2 overlap (band **[0.1,0.9]**): `experiments\\EXP-024_regime_matching_alloc_perf_nomem_band_01_09\\`
    - Key numbers: AUC≈0.9895, Conte overlap coverage≈0.416.
  - Phase 3 modeling (Ridge): `experiments\\EXP-025_modeling_alloc_perf_nomem_band_01_09\\`
    - Result: still catastrophic target R² on proxy label (~ -1.29e5).
  - Phase 3 modeling (HuberRegressor): `experiments\\EXP-026_modeling_alloc_perf_nomem_band_01_09_huber\\`
    - Result: target R²=-867.12 on proxy label (still negative, but far less extreme vs Ridge).

**Acceptance**: Tier A success remains only conditional. `EXP-063/065/067/069` were positive on the first frozen `EXP-062` universe, `EXP-071/072/073/074` were negative or near-zero on the second frozen universe, the reduced timing-only retry `EXP-076/078` split again (`+0.0502` on universe 1 vs. `-1.6086` on universe 2, roughly 16x worse than the prior worst second-universe result of `-0.0990`), the first authoritative CORAL attempt `EXP-079/080` did not rescue the design (`-46520.6724` on universe 1 and `-0.0613` on universe 2), the higher-regularization retry `EXP-081/082` still failed (`-59.6547` on universe 1 and `-0.0633` on universe 2), and the output-space quantile-matching follow-up `EXP-083/084` also failed to produce a general zero-label rescue (`-0.1026` on universe 1 and `-0.0285` on universe 2). The current evidence does not yet support a general matched-regime claim.

### Authoritative Phase 3 status
- [x] Rerun authoritative overlap/modeling on the raw `chunks-v3` parquet.
- [x] Confirm that alloc+perf overlap features are too separable for primary claims.
- [x] Confirm that the strict safe-feature overlap set improves transfer but still leaves target `R^2 < 0`.
- [x] Recover analysis-time hardware metadata needed to derive `peak_memory_fraction` and non-proxy workload regimes.
- [x] Re-run Phase 2/3 on normalized memory targets after that metadata recovery.
- [x] Repeat the normalized matched-regime baseline across additional seeds / splits and confirm whether it is stable.
- [x] Increase authoritative sampling depth (or otherwise reduce sampling variance) and confirm whether that alone stabilizes the normalized baseline.
- [x] Diagnose whether simple feature/model simplification (alloc-only + Huber) is enough to rescue the dense cohorts.
- [x] Diagnose whether label / measurement semantics are now the dominant source of failure on the dense cohorts.
- [x] Test a decoupled-feature dense rerun: safer Phase 2 overlap features with richer Phase 3 modeling features.
- [x] Stage (but do not submit) a no-queue-time matched-regime follow-up family as EXP-062..069 after confirming EXP-052..059 were already occupied by immutable historical runs.
- [x] Freeze the EXP-044-equivalent `300k / 24` sampling universe and retrofit EXP-062..069 to use the shared sampling-plan artifact.
- [x] Test explicit feature adaptation on the decoupled dense design (e.g. CORAL).
- [x] Execute `EXP-062` plus the frozen-cohort modeling repeats (`EXP-063/065/067/069`) and confirm that the queue-time-free frozen design yields stable positive target transfer on the shared cohort.
- [x] Quantify sensitivity to frozen-universe choice (for example, a second frozen sampling plan for the same regime).
- [x] Stage the reduced timing-block family `EXP-075..078` on both frozen universes, keeping only `ncores`, `nhosts`, and `runtime_sec`.
- [x] Execute the reduced timing-block family `EXP-075..078` on both frozen universes and re-test before broadening to new cluster pairs.
- [x] Stage the explicit CORAL adaptation modeling pair `EXP-079/080` on the stronger frozen no-queue design so both frozen universes can be evaluated without changing the matched cohorts again.
- [x] Test explicit adaptation on the frozen-universe normalized design after the runtime-sec-only ablation failed cross-universe robustness.
- [x] Stage the higher-regularization CORAL sensitivity pair `EXP-081/082` on the same frozen no-queue cohorts with `reg = 1e-3`.
- [x] Test a higher-regularization CORAL sensitivity on both frozen universes before abandoning linear covariance adaptation entirely.
- [x] Stage a materially different adaptation family (`EXP-083/084` quantile-output matching) after linear CORAL failed on both frozen universes.
- [x] Test the staged quantile-output family `EXP-083/084` on the same frozen no-queue cohorts.
- [ ] Decide whether the adaptation search should stop at the current negative result or justify a substantially different family with stronger guardrails than CORAL or direct quantile matching.
- [ ] Extend the normalized matched-regime design to the other cluster pairs.

---

### Phase 4 — Unlabeled Domain Adaptation (Zero‑Label)
#### 4.1 Domain classifier diagnostics
- Train a classifier to predict domain from features.
- If AUC 
 0.9, domains are highly separable → transfer will fail without matching/adaptation.

#### 4.2 CORAL baseline
- Align covariance of continuous features using unlabeled target.
- Train model on aligned source; evaluate on aligned target.
  - Proxy run: `experiments\\EXP-027_modeling_alloc_perf_nomem_band_01_09_coral\\`
    - Result: catastrophic negative target R² with severe numerical instability (proxy-only); see `...\\results\\metrics.json`.
  - Authoritative follow-up: `experiments\\EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral\\` and `experiments\\EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024\\`
    - Design: reuse the frozen `EXP-062` and `EXP-070` overlap cohorts, keep the stronger five-feature no-queue model space, and turn on `adaptation.type = coral`.
    - Result: `EXP-079` failed catastrophically on the previously positive first universe (`target R^2 = -46520.6724`), while `EXP-080` remained negative on the second universe (`target R^2 = -0.0613`, bootstrap CI fully below zero).
  - Staged regularization sensitivity: `experiments\\EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3\\` and `experiments\\EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024\\`
    - Design: keep the same frozen cohorts and five-feature no-queue model space, but increase `adaptation.reg` from `1e-6` to `1e-3`.
    - Result: `EXP-081` reduced the magnitude of the universe-1 blow-up but still remained catastrophically negative (`target R^2 = -59.6547`, slope `0.0091`), while `EXP-082` stayed effectively unchanged on the second universe (`target R^2 = -0.0633`).

#### 4.3 Output distribution matching (unsupervised)
- Fit a monotonic mapping on *predicted outputs* to match target’s predicted distribution to a reference distribution (careful: avoids using labels but can still distort semantics).
  - Authoritative follow-up: `experiments\\EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output\\` and `experiments\\EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024\\`
    - Design: keep the frozen `EXP-062` and `EXP-070` overlap cohorts plus the stronger five-feature no-queue model space fixed, then apply `adaptation.type = quantile_output` with `n_quantiles = 100` as a post-prediction monotone correction.
    - Result: `EXP-083` removed the catastrophic CORAL blow-up but still flipped the previously positive first universe negative (`target R^2 = -0.1026`, slope `0.8099`), while `EXP-084` improved the harder second universe relative to both no adaptation and CORAL (`target R^2 = -0.0285`, slope `0.6150`) but still remained fully below zero.
    - Interpretation: direct quantile matching trades off between the two frozen universes and therefore still fails the cross-universe acceptance bar for a general zero-label adaptation.

**Acceptance**: show measurable improvement over non‑adapted zero‑shot on matched cohorts; document failure modes clearly.

---

### Phase 5 — Rigor + Publication Readiness
- [ ] Repeat across multiple month pairs (not just one window; proxy single-month pairs EXP-033..EXP-038)
- [ ] Add ablations:
  - allocations only vs allocations+runtime vs allocations+perf metrics
  - with/without matching
  - with/without adaptation (proxy runs: EXP-027 CORAL vs EXP-028 no-adapt)
- [ ] Add sensitivity analysis to cohort overlap thresholds (proxy runs: EXP-029/030 [0.05,0.95], EXP-031/032 [0.2,0.8])

**Acceptance**: reproducible report with clear scope: “zero‑shot works for X% of target jobs under regime Y; fails elsewhere due to domain shift.”

---

## Risks & Mitigations

### Risk 1: True zero‑shot across full distributions is impossible
Mitigation: publish the **negative result** rigorously and pivot to *regime‑conditional transfer*.

### Risk 2: Feature semantics differ (measurement non‑equivalence)
Mitigation: stratify by `memory_includes_cache`, `memory_collection_method`; treat as separate domains.

### Risk 3: Partitions encode cluster identity
Mitigation: map partitions into a **shared taxonomy** and use only taxonomy labels (CPU/GPU/large) rather than raw partition strings.

---

## Concrete Next Steps (Immediate)

1. Record `EXP-062..069` as a **conditional** positive baseline on one frozen universe, not yet a general matched-regime success story.
2. Use `EXP-070..074` as evidence that frozen-universe sensitivity remains large: the second universe produced a substantially different overlap cohort and target `R^2` reverted to zero/negative.
3. `EXP-075..078` have now completed: the runtime-sec-only ablation stayed weakly positive on the first frozen universe (`EXP-076` target `R^2 = 0.0502`) but collapsed to `EXP-078` target `R^2 = -1.6086` on the second, roughly `16x` worse than the prior worst second-universe result (`EXP-072`, `-0.0990`). `EXP-078` also lost `765 / 12526` source overlap jobs and `51 / 4626` target overlap jobs at the positive-label filter, versus `0 / 7504` source and only `34 / 6031` target jobs in EXP-076, so timing-only pruning is not a robust fix and the comparison should keep that label-availability caveat explicit.
4. `EXP-079/080` have now completed, and the first authoritative CORAL attempt failed to rescue the frozen no-queue design: universe 1 collapsed catastrophically while universe 2 stayed negative.
5. `EXP-081/082` have now completed, and the higher-regularization CORAL retry still failed to rescue either frozen universe.
6. The most defensible next step is now to **pivot away from linear CORAL entirely** (or stop at the negative result) rather than spending more runs on the same covariance-alignment family.
7. Only after defining that different adaptation branch, continue the broader regime-matched v3 experiment plan:
   - Source: Conte (CPU)
   - Target: Anvil CPU partitions only
   - Model: regularized linear / GAM
   - Evaluate Tier A success.

---

## Why this can work

Zero‑shot transfer fails today because we’re trying to transfer across:
- different **eras** (2015 vs 2022)
- different **hardware regimes** (CPU vs GPU/AI)
- disjoint **scheduler partitions**

By (1) restricting to overlapping regimes and (2) using unlabeled adaptation + more universal signals, we can create a **defensible and useful** zero‑shot story.

---

## References (internal)
- `../FRESCO-v2/PROGRESS_TRACKER.md` (Phase 7 summary)
- `../FRESCO-Research/Experiments/EXP-015_enhanced_validation/EXP015_FINAL_REPORT.md` (rigorous results)
