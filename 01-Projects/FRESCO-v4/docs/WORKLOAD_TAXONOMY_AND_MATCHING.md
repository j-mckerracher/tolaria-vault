# Workload Taxonomy & Regime Matching (v4 Context)

**Last Updated**: 2026-03-13

## Purpose
Summarize the workload taxonomy and regime matching framework inherited from FRESCO v3, and contextualize it for v4 few-shot calibration experiments.

See `FRESCO-v3/docs/WORKLOAD_TAXONOMY_AND_MATCHING.md` for the complete specification, including all EXP results, ablation history, and diagnostic interpretations.

## 1. Taxonomy (inherited from v3)
Shared taxonomy label `workload_regime`:
- `hardware_cpu_standard` (primary regime for v4 experiments)
- `hardware_cpu_largemem`
- `hardware_gpu_standard`
- `cpu_standard` (proxy-based fallback)
- `unknown`

Hardware-based regime labels are derived at analysis time from `config/clusters.json` metadata. The proxy fallback (`value_gpu_max <= 0`) is used only when hardware metadata is unavailable.

## 2. Recommended starting configuration for v4
Based on the v3 experimental record (EXP-062 through EXP-084), the recommended baseline configuration is:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Regime | `hardware_cpu_standard` | Explicit hardware filter; most data volume |
| Features | `ncores, nhosts, timelimit_sec, runtime_sec, runtime_fraction` | Safe set minus `queue_time_sec` |
| Overlap band | `[0.2, 0.8]` | Standard propensity-score overlap region |
| Label | `peak_memory_fraction` | Hardware-normalized memory usage |

This configuration is the no-queue-time, five-feature variant that demonstrated stable positive transfer on one frozen universe (EXP-063: target R-squared = 0.1070) but failed to generalize across alternate frozen universes in the zero-shot setting.

## 3. Domain separability context
With the recommended configuration, domain AUC is approximately **0.93**, meaning the source and target clusters remain **highly separable** even within the matched regime.

This is acceptable for few-shot calibration because:
- High domain AUC indicates systematic distributional differences that a global model cannot capture.
- Few-shot calibration provides direct access to the target distribution through labeled examples, allowing the model to correct for systematic prediction bias.
- The v3 zero-shot experiments showed that the failure mode is primarily a **level shift** in predicted vs. actual target values (source-centered prediction collapse), which is exactly what output recalibration and fine-tuning are designed to fix.

## 4. Overlap-aware cohort builder (inherited from v3)
For any cross-cluster experiment comparing source A vs. target B:

1. Choose feature set F (the five safe features above).
2. Standardize continuous features.
3. Compute overlap score via domain classifier propensity:
   - Train logistic classifier to predict domain (A vs. B) using F.
   - Define overlap as samples with P(domain=A|x) in the overlap band.
4. Few-shot calibration labels are sampled from **within the overlap cohort only**.
5. Evaluate models on the held-out portion of the overlap cohort.

## 5. Reporting requirements (inherited from v3)
Every cross-cluster claim must report:
- Regime definition
- Overlap coverage (% of target jobs)
- Feature support diagnostics (KS stats, domain classifier AUC)
- Residual bias and calibration
- (v4 addition) Number of target labels used (N) and calibration strategy

## 6. Key v3 findings informing v4

### What worked in v3
- Hardware-normalized `peak_memory_fraction` changed target transfer from clearly negative to modestly positive.
- Removing `queue_time_sec` and freezing the sampling plan stabilized within-universe results.
- On one frozen universe, four modeling seeds all produced positive target R-squared with bootstrap CIs above zero.

### What did not work in v3
- Zero-shot transfer did not generalize across frozen universes (EXP-071 through EXP-074 all negative on the second universe).
- CORAL adaptation failed catastrophically on one universe (EXP-079: target R-squared = -46521).
- Quantile output adaptation improved slightly but still did not produce a robust positive result across both universes.
- The remaining failure mode is dominated by **source-centered prediction collapse**: the source model predicts source-like memory fractions for target jobs, failing to capture the lower Conte median.

### Why few-shot is the natural next step
- The v3 evidence says that no zero-label adaptation family (none, CORAL, quantile output) is robust across both frozen universes.
- A small number of labeled target observations directly reveals the target distribution's location and scale.
- Even a simple linear recalibration (y_true = a * y_pred + b) fitted on N target (predicted, actual) pairs can correct the systematic level shift.
