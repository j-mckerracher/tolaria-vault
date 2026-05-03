# Experiment: EXP-001 - Baseline statistical analysis

**Status**: Completed  
**Date Created**: 2026-01-25  
**Last Updated**: 2026-01-31  
**Research Path**: PATH-A  
**Directory**: Experiments/EXP-001_baseline_statistical_analysis

---

## Objective

Establish a full-dataset baseline of workload and performance distributions (job-level rollups + monthly aggregates) to support anomaly detection research (and downstream EXP-002).

## Hypothesis

**Prediction**: Baseline distributions of runtime, wait time, and resource-usage aggregates will show clear regime shifts across eras and source tokens (e.g., `_S`, `_C`, none), and a small number of job subpopulations will dominate extreme tails.

**Null Hypothesis**: Distributions are stable across time and source tokens within statistical uncertainty, with no meaningful tail-driving subpopulations.

---

## FRESCO Data Specification

| Parameter | Value |
|-----------|-------|
| Cluster(s) | All available in FRESCO (multi-institution; treat `_S`, `_C`, none as observed source tokens until verified) |
| Date Range | Full observed coverage (2013–2018, 2022–2023; verify per shards) |
| Total Jobs | ~20.9M (dataset-level) |
| Query URL | N/A (filesystem shards) |

### Columns Used

See `scripts/exp001_baseline.py` (`ATTR_COLS` + `METRIC_COLS`).

---

## Methodology

Run a three-stage pipeline:
1. Stage 1: scan shard files → write temporary per-job partials partitioned by job start month.
2. Stage 2: reduce partials → write per-job rollup table (one row per `jid`).
3. Stage 3: aggregate rollups → write monthly summary tables (CSV+Parquet) and plots.

### Ensuring all output goes to `/depot/...`
All pipeline stages accept explicit output roots:
- `--tmp-root` controls temporary partials
- `--out-root` controls final outputs (`job_rollup/`, `monthly_summary.*`, figures)

In `scripts/exp001_full.slurm`, `EXP_DIR` is set to:
`/depot/sbagchi/data/josh/FRESCO-Research/Experiments/EXP-001_baseline_statistical_analysis`
so logs + results always land under that directory.

### Local run (small test)
If you have a local mirror of the shards, you can sanity-check with:
```powershell
cd Experiments\EXP-001_baseline_statistical_analysis
python -m pip install -r scripts\requirements.txt
python scripts\exp001_baseline.py stage1 --input-root "C:\Users\jmckerra\Documents\FRESCO-Dataset\all-data\fresco_data" --tmp-root results\tmp --out-root results --max-files 5 --verbose-every 1
python scripts\exp001_baseline.py stage2 --tmp-root results\tmp --out-root results --threads 8
python scripts\exp001_baseline.py stage3 --tmp-root results\tmp --out-root results --threads 8
python scripts\plot_monthly.py
```

---

## Reproducibility

### Code

- Script: `scripts/exp001_baseline.py`
- SLURM job: `scripts/exp001_full.slurm`

> Fill in commit hash and environment details when executed.

---

## Output Artifacts (expected)

| Artifact | Path |
|----------|------|
| Per-job rollup (partitioned) | `results/job_rollup/` |
| Monthly summary (Parquet) | `results/monthly_summary.parquet` |
| Monthly summary (CSV) | `results/monthly_summary.csv` |
| Figures | `results/figures/*.png` |

---

## Execution Log

| Date | Action | Result/Notes |
|------|--------|--------------|
| 2026-01-25 | Created | Initialized experiment skeleton + pipeline code |
| 2026-01-30 | Stage 1 complete | Processed 67,046 shard files |
| 2026-01-31 | Stage 2+3 complete | Job rollups + monthly summary generated |

---

## Results Summary

### Dataset Coverage

| Source Token | Months | Total Jobs | Notes |
|--------------|--------|------------|-------|
| S (Stampede) | 2013-02 to 2018-04 | ~3.5M | Primary dataset |
| C (Conte) | 2015-04 to 2017-06 | ~1.5M | Overlaps with S |
| NONE (Anvil) | 2022-06 to 2023-06 | ~0.5M | Modern era |

### Key Statistics (all months)

| Metric | Stampede (S) | Conte (C) | Anvil (NONE) |
|--------|--------------|-----------|--------------|
| Median runtime (sec) | 300-3,600 | 200-10,000 | 200-220,000 |
| Mean cores per job | 150-300 | 1.0 | 60-200 |
| Peak memory (GB) | 5-10 | 5-10 | 50-100 |
| GPU telemetry | 0% | 0% | 0-4% (2023 only) |

### Key Findings

1. **FIND-001**: Clusters differ dramatically in job structure (Conte = serial, Stampede = parallel)
2. **FIND-002**: No GPU telemetry available before Feb 2023
3. **FIND-003**: Anvil shows 10× higher memory usage than older clusters
4. **FIND-004**: Wait times spiked 10× on Stampede in Feb-Apr 2015

See [Findings Log](../../Documentation/Findings_Log.md) for details.

---

## Output Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Per-job rollup (partitioned) | `results/job_rollup/` | ✅ Generated |
| Monthly summary (Parquet) | `results/monthly_summary.parquet` | ✅ Generated |
| Monthly summary (CSV) | `results/monthly_summary.csv` | ✅ Generated |
| Figures | `results/figures/*.png` | ✅ Generated |

---

## Next Steps

- [ ] Use baselines in EXP-002 (Isolation Forest) for anomaly thresholds
- [ ] Investigate FIND-004 (2015 wait time spike) further
- [ ] Correlate memory patterns with node specs per cluster
