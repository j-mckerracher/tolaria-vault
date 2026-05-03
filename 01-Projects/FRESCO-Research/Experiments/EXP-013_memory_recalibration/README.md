# Experiment: EXP-013 - Memory Recalibration

**Status**: Created  
**Date Created**: 2026-02-01  
**Last Updated**: 2026-02-01  
**Research Path**: PATH-C  
**Directory**: /mnt/c/Users/jmckerra/ObsidianNotes/Main/01-Projects/FRESCO-Research/Experiments/EXP-013_memory_recalibration

---

## Objective

Test whether simple affine calibration in log space can rescue the catastrophic cross-site memory transfer failures observed in EXP-011 (R² ≤ -21).

## Hypothesis

**Prediction**: If EXP-012 is correct (failures are due to systematic label offsets, not fundamental unpredictability), then affine calibration using a small target-site sample should dramatically improve transfer R²:
- Offset-only calibration (b): should improve R² by removing mean bias
- Affine calibration (a, b): should further improve by adjusting scale

Expected improvements:
- S → Anvil: R² from -21.3 to >0 (calibration should rescue completely)
- C → Anvil: R² from -7.7 to >0
- Other transfers: R² from negative to positive/moderate

**Null Hypothesis**: Calibration provides minimal improvement (ΔR² < 0.1), suggesting failures are due to fundamental unpredictability rather than systematic offsets.

---

## FRESCO Data Specification

| Parameter | Value |
|-----------|-------|
| Cluster(s) | Stampede (S) / Conte (C) / NONE |
| Date Range | Full FRESCO dataset range |
| Total Jobs | ~7M (after filtering) |
| Query URL | /depot/sbagchi/data/josh/FRESCO/chunks |

### Filters Applied

Same as EXP-011:
- Jobs with ≥1 memory sample and peak_memused > 0
- Runtime > 0 and < 30 days
- Timelimit > 0 and < 365 days
- ncores > 0 and nhosts > 0

### Columns Used

```
jid, timelimit_sec, nhosts, ncores, cluster, yearmonth, 
peak_memused
```

---

## Methodology

### Approach

1. **Train source models**: Use same setup as EXP-011 (XGBoost on source cluster)
2. **For each transfer scenario**:
   - Split target cluster into calibration + test sets
   - Fit affine calibration on calibration set: `log(y_true) = a * log(y_pred) + b`
   - Apply calibration to test set
   - Measure R² improvement
3. **Test three calibration sizes**: 1%, 5%, 10% of target data
4. **Focus on worst-case transfers**: S→Anvil (R²=-21.3), C→Anvil (R²=-7.7), etc.

### Algorithm/Model

- **Source model**: XGBoost (same hyperparameters as EXP-011)
- **Calibration**: Linear regression in log space (sklearn LinearRegression)
- **Features**: log1p(ncores), log1p(nhosts), log1p(timelimit_sec)
- **Label**: log(peak_memused)

### Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| XGBoost params | Same as EXP-011 | n=200, depth=6, lr=0.1 |
| calib_fracs | [0.01, 0.05, 0.10] | Calibration set sizes |
| test_frac | 0.2 | Temporal split fraction |
| seed | 42 | Random seed |

---

## Reproducibility

### Environment

| Component | Version |
|-----------|---------|
| Python | 3.x (Gilbreth system default) |
| pandas | Latest (via pip) |
| pyarrow | Latest (via pip) |
| duckdb | Latest (via pip) |
| numpy | Latest (via pip) |
| scikit-learn | Latest (via pip) |
| xgboost | Latest (via pip) |

### Code

- **Repository**: FRESCO-Research (local Obsidian vault)
- **Commit Hash**: (to be filled after commit)
- **Script(s)**: 
  - `scripts/exp013_recalibration.py` (main analysis)
  - `scripts/exp013.slurm` (SLURM job script)

### Random Seeds

- Seed: 42 (for XGBoost and sampling)

---

## Supercomputer Job

| Field | Value |
|-------|-------|
| Cluster | Gilbreth (Purdue) |
| Scheduler | SLURM |
| Job ID | (to be filled when submitted) |
| Partition/Queue | a30 |
| Nodes Requested | 1 |
| Cores Requested | 16 |
| Memory Requested | 64GB |
| Walltime Requested | 04:00:00 |
| QoS | standby |
| Account | sbagchi |
| Submitted | (to be filled) |
| Started | (to be filled) |
| Ended | (to be filled) |
| Actual Runtime | (to be filled) |

### Job Script

```bash
scripts/exp013.slurm
```

---

## Execution Log

| Date | Action | Result/Notes |
|------|--------|--------------|
| 2026-02-01 | Created | Initialized experiment |
| | | |

---

## Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Results Data | `results/exp013_recalibration_results.csv` | R² before/after calibration, slope/intercept, improvements |
| Job Log | `logs/exp013_*.out` | SLURM stdout |
| Error Log | `logs/exp013_*.err` | SLURM stderr |

---

## Results & Analysis

### Summary Statistics

| Transfer | R² Before | R² After (10% calib) | Improvement | Calibration (slope, intercept) |
|----------|-----------|---------------------|-------------|--------------------------------|
| | | | | |

### Key Observations

1. {Observation with supporting evidence}
2. {Another observation}
3. {Additional observations}

---

## Discussion

### Interpretation

{What do calibration results tell us about the nature of transfer failures?}

### Limitations

- Calibration requires labeled target data (not zero-shot)
- Linear calibration may not capture nonlinear distribution shifts
- Tested only on historical splits (not truly new sites)

### Comparison to EXP-011

{How much does calibration improve over uncalibrated transfer?}

---

## Conclusion

- [ ] Hypothesis Confirmed (calibration rescues transfer)
- [ ] Hypothesis Rejected (calibration doesn't help)
- [ ] Inconclusive (needs more analysis)

**Key Takeaway**: {One-sentence summary}

### Next Steps

- [ ] If calibration works: Document best practices for practitioners
- [ ] If calibration fails: Investigate nonlinear calibration or feature engineering
- [ ] Log to Findings Log: {Yes/No}

---

## Related Findings

| Finding ID | Link |
|------------|------|
| FIND-026 | Cross-site memory prediction fails catastrophically |
| FIND-027 | Memory metrics likely non-standardized across clusters |
| FIND-028 | Systematic 6-9× memory offsets between clusters |

---

## Notes

This experiment tests the practical viability of cross-site memory prediction with calibration. If successful, it provides a deployment strategy for practitioners. If unsuccessful, it suggests deeper issues (nonlinear shifts, feature inadequacy, or fundamental unpredictability).
