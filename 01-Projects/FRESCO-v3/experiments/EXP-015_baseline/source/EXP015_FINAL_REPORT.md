# EXP-015: Enhanced Cross-Cluster Validation - Final Report

**Date**: 2026-02-03  
**Status**: COMPLETE  
**Conclusion**: v2.0 normalization enables **within-cluster** prediction but NOT cross-cluster transfer

---

## Executive Summary

EXP-015 addressed EXP-014's critical review concerns with:
- **Balanced test sets**: 2,000 per cluster (vs 62/72k imbalance)
- **Enhanced features**: partition, node_type, runtime_efficiency, cores_per_node
- **Robust analysis**: Bootstrap CI, residual analysis, covariate shift metrics

**Key Finding**: Cross-cluster transfer remains catastrophically negative (R²=-4 to -9) due to **severe covariate shift** and **systematic calibration failure**. Pooled models work well (R²=0.5-0.65) but show NO benefit from explicit cluster_id.

---

## Results Comparison

### EXP-014 (Baseline - Small/Imbalanced)
| Model | Test Cluster | R² | Test N |
|-------|-------------|-----|---------|
| conte | conte | -0.04 | 72,364 |
| anvil | anvil | 0.68 | 62 |
| conte→anvil | anvil | **-4.04** | 62 |
| pooled_with_id | conte | 0.26 | 72,364 |
| pooled_with_id | anvil | 0.69 | 62 |

### EXP-015 (Enhanced - Balanced)
| Model | Test Cluster | R² | 95% CI | MAE | Bias | Test N |
|-------|-------------|-----|---------|-----|------|---------|
| conte | conte | **0.646** | [0.604, 0.685] | 0.284 | +0.011 | 2,000 |
| anvil | anvil | **0.493** | [0.446, 0.536] | 0.349 | -0.007 | 2,000 |
| conte→anvil | anvil | **-4.33** | [-4.63, -4.04] | 1.609 | **+1.609** | 2,000 |
| anvil→conte | conte | **-9.31** | [-10.34, -8.53] | 2.325 | **-2.307** | 2,000 |
| pooled_no_id | conte | **0.646** | [0.604, 0.684] | 0.290 | +0.007 | 2,000 |
| pooled_no_id | anvil | **0.496** | [0.453, 0.537] | 0.354 | -0.005 | 2,000 |
| pooled_with_id | conte | **0.646** | [0.604, 0.684] | 0.290 | +0.007 | 2,000 |
| pooled_with_id | anvil | **0.496** | [0.453, 0.537] | 0.354 | -0.005 | 2,000 |

---

## Critical Findings

### 1. Within-Cluster Performance is Good ✅
- Conte: R²=0.646 [0.604, 0.685] - **Credible and reproducible**
- Anvil: R²=0.493 [0.446, 0.536] - **Credible and reproducible**
- **Conclusion**: v2.0 enables reliable within-cluster memory prediction

### 2. Cross-Cluster Transfer Still Fails ❌
- conte→anvil: R²=-4.33 (no improvement from EXP-014's -4.04)
- anvil→conte: R²=-9.31 (even worse)
- **Massive systematic bias**: +1.61 (Conte predicting Anvil), -2.31 (Anvil predicting Conte)
- **Conclusion**: Normalization reduces scale but doesn't solve fundamental domain shift

### 3. Severe Covariate Shift Detected 🚨
Kolmogorov-Smirnov test results (conte vs anvil):

| Feature | KS Statistic | P-value | Interpretation |
|---------|-------------|---------|----------------|
| partition_encoded | **1.00** | 0.0 | **Completely non-overlapping** |
| node_type_encoded | **0.999** | 0.0 | **Almost completely different** |
| log_ncores | **0.88** | 0.0 | **Extreme difference** |
| log_cores_per_node | **0.88** | 0.0 | **Extreme difference** |
| log_timelimit | 0.45 | ~0 | Major difference |
| runtime_efficiency | 0.27 | ~0 | Moderate difference |

**Implication**: Conte (2015 CPU cluster) and Anvil (2022 GPU/AI cluster) have **fundamentally different workload distributions**. Models trained on one cluster are extrapolating far outside their training support when applied to the other.

### 4. cluster_id Has Zero Effect 🤔
- pooled_with_id and pooled_no_id produce **IDENTICAL** results (R²=0.646/0.496)
- **Hypothesis** (GPT-5.2): partition/node_type already encode cluster membership perfectly
- Feature importance shows: partition_encoded, log_nhosts, log_ncores (NOT cluster_id)
- **Conclusion**: Explicit cluster_id is **redundant** given rich metadata features

### 5. Balanced Sampling Fixed Pooled Models ✅
- EXP-014 pooled: R²=0.26 (Conte) - bad due to 111k Anvil vs 3k Conte imbalance
- EXP-015 pooled: R²=0.646 (Conte) - good with balanced 8k/8k sampling
- **Conclusion**: Domain imbalance was masking pooled model potential

---

## Calibration Analysis

### conte→anvil (Transfer Failure)
- **Calibration R²**: 0.088 (predicted vs actual almost uncorrelated)
- **Slope**: -0.317 (negative! predicting opposite relationship)
- **Intercept**: -0.317
- **Mean residual (bias)**: +1.609 (systematic over-prediction in log space)

### anvil→conte (Worse Transfer Failure)
- **Calibration R²**: 0.065 (even worse calibration)
- **Slope**: -0.412 (stronger negative slope)
- **Intercept**: -4.540 (massive intercept shift)
- **Mean residual (bias)**: -2.307 (systematic under-prediction)

**Interpretation**: Models aren't just miscalibrated, they're learning **opposite relationships** when transferred. This suggests fundamental conditional distribution differences, not just offset/scale issues.

---

## Feature Importance

### Conte Model (Within-Cluster)
1. log_nhosts
2. partition_encoded  
3. failed

### Anvil Model (Within-Cluster)
1. log_cores_per_node
2. partition_encoded
3. runtime_efficiency

**Key Insight**: Different features matter in different clusters, consistent with conditional distribution shift.

---

## Publication-Readiness Assessment

### What v2.0 DOES Enable ✅
1. **Within-cluster memory prediction**: R²=0.5-0.65 with credible confidence intervals
2. **Unified schema**: All clusters represented in single parquet format
3. **Reproducible results**: Bootstrap CI shows stable estimates
4. **Normalized fractions**: peak_memory_fraction computed consistently

### What v2.0 DOES NOT Enable ❌
1. **Zero-shot cross-cluster transfer**: R² remains severely negative
2. **Cross-cluster generalization**: Requires cluster-aware calibration
3. **Unified prediction model**: Conditional relationships differ by cluster

### Defensible Publication Claims
**GOOD**: "FRESCO v2.0 enables reliable within-cluster memory prediction through normalized memory fractions and rich hardware metadata."

**BAD**: "FRESCO v2.0 solves cross-cluster prediction" (false - transfer still fails)

**NUANCED**: "FRESCO v2.0 reduces extreme scale mismatches (R²: -21→-4) but cross-cluster prediction requires explicit domain modeling due to workload distribution shifts between CPU-era (Conte 2015) and GPU/AI-era (Anvil 2022) clusters."

---

## Recommendations

### For Production (Phase 6)
**PROCEED** - v2.0 is ready for production with clear scope:
- Unified schema validated across all three clusters
- Within-cluster prediction works reliably
- Cross-cluster limitations documented and understood

**Note for users**: Cross-cluster models require cluster-specific calibration or pooled training with cluster indicators.

### For Future Research
1. **Per-cluster calibration**: Test simple intercept/scale corrections
2. **Hierarchical modeling**: Mixed-effects or domain-adaptation approaches
3. **Workload characterization**: Can we identify "GPU jobs" vs "CPU jobs" to enable better transfer?
4. **Temporal analysis**: Is cross-cluster failure due to era (2015 vs 2022) or hardware?

---

## Conclusion

EXP-015 provides **rigorous validation** that v2.0 normalization achieves its primary goal: enabling **within-cluster** prediction through proper memory fraction normalization and hardware metadata. 

Cross-cluster transfer remains unsuccessful, but this is now understood as a **feature distribution shift problem** (severe covariate shift: KS=0.88-1.0 for key features) rather than a schema/normalization problem. Clusters represent fundamentally different workload eras and hardware contexts.

**Verdict**: v2.0 is **production-ready** for its intended use case (enabling within-cluster analysis with cross-cluster metadata consistency), but **not** for zero-shot cross-cluster prediction without domain-specific modeling.

---

## Files

**Results**:
- `results/exp015_results.csv` - Full metrics table (18 rows × 19 columns)
- `results/exp015_covariate_shift.json` - KS test statistics for all feature pairs

**Scripts**:
- `scripts/exp015_enhanced_validation.py` - 17KB comprehensive experiment
- `scripts/exp015.slurm` - SLURM job script

**Job Details**:
- Job ID: 10249227
- Runtime: 25 seconds
- Partition: v100 (auto-selected by sbbest)
- Status: COMPLETED successfully
