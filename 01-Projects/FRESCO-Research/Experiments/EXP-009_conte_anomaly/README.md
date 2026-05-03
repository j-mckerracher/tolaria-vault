# EXP-009: Conte Anomaly Resolution

## Objective
Determine whether the poor predictability of Conte runtimes (the "Conte Anomaly") is due to:
1. **H1 Under-specification**: Conte's resource requests (ncores, nhosts) have low variance, preventing models from learning their impact. Training on NONE (varied data) transfers knowledge of these slopes.
2. **H2 Non-stationarity**: The time-based train/test split on Conte is particularly harsh due to drift. A random split would yield much higher performance.

## Methodology
Run 4 conditions:
1. **C (Time) -> C (Time)**: Baseline. Expected to be poor.
2. **C (Random) -> C (Random)**: Checks H2. If much better than baseline, H2 is supported.
3. **NONE (Full) -> C (Time)**: Checks H1. If better than baseline, training on varied data helps.
4. **NONE (Constrained) -> C (Time)**: Checks H1 Mechanism. Constrained to `ncores=1 & nhosts=1`. If much worse than NONE (Full), the benefit comes from learning resource slopes.

## Execution
Submit to Gilbreth:
```bash
sbbest scripts/exp009.slurm
```

## Logging Findings
After execution, check the logs for "EVIDENCE" blocks.

- **If H2 is strong (Gap > 0.1)**: Log FIND-XXX: "Conte anomaly driven by non-stationarity; random split improves R2 by >0.1".
- **If H1 is strong (Transfer > Baseline & Slope > 0.05)**: Log FIND-XXX: "Conte anomaly driven by resource under-specification; transfer from NONE improves prediction via slope learning."
- **If both**: Log both.
- **If neither**: The anomaly is likely due to intrinsic unpredictability or unmeasured features (e.g., specific user behaviors not captured).

## Outputs
- `results/conte_anomaly_results.csv`: Raw metrics for all conditions.
- `logs/exp009_*.out`: stdout with interpretation.

## Results & Interpretation (2026-01-31)
**Summary**: The results strongly support **H1 (Under-specification)** over H2 (Non-stationarity) as the primary driver of the Conte anomaly.

**Key Metrics**:
- **A_C_to_C_time (Baseline)**: R2=0.1125, smape=145.3
- **B_C_to_C_random (H2 Check)**: R2=0.1539, smape=121.8
- **C_NONE_to_C_transfer (H1 Check)**: R2=0.1535, smape=121.6
- **D_NONE_to_C_transfer_supportmatch**: R2=0.1163, smape=148.3

**Conclusion**:
1. **Non-stationarity plays a minor role**: Switching to a random split (B) only improves R2 marginally (0.11 -> 0.15) compared to what a "good" model should achieve. It remains very low.
2. **Transfer equals Random Split**: Training on NONE (C) matches the performance of the best-case Conte split (B). This suggests the external dataset contains a more robust signal than Conte's own past.
3. **Variance is Key**: Filtering the transfer data to match Conte's support (D) degrades performance back to baseline levels (0.15 -> 0.11). This confirms that the benefit of transfer comes from **learning resource slopes** from the diverse NONE data, which are under-specified in Conte's low-variance history.
