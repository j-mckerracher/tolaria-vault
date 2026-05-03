# Experiment: {experiment_id} - {title}

**Status**: {status}  
**Date Created**: {date_created}  
**Last Updated**: {date_updated}  
**Research Path**: {research_path}  
**Directory**: {directory_path}

---

## Objective

{objective}

## Hypothesis

**Prediction**: {What you expect to find}

**Null Hypothesis**: {What would indicate no effect}

---

## FRESCO Data Specification

| Parameter | Value |
|-----------|-------|
| Cluster(s) | Anvil / Conte / Stampede |
| Date Range | YYYY-MM-DD to YYYY-MM-DD |
| Total Jobs | {approximate count} |
| Query URL | {link to frescodata.xyz query if applicable} |

### Filters Applied

- Filter 1: {description}
- Filter 2: {description}

### Columns Used

```
submit_time, start_time, end_time, timelimit, nhosts, ncores, 
exitcode, value_cpuuser, value_memused, ...
```

---

## Methodology

### Approach

{Description of the analytical approach}

### Algorithm/Model

- **Type**: {Statistical analysis / ML model / etc.}
- **Details**: {Specific method}

### Hyperparameters (if applicable)

| Parameter | Value | Notes |
|-----------|-------|-------|
| | | |

---

## Reproducibility

### Environment

| Component | Version |
|-----------|---------|
| Python | {e.g., 3.10.12} |
| Key Package 1 | {version} |
| Key Package 2 | {version} |

### Code

- **Repository**: {git repo if applicable}
- **Commit Hash**: {full SHA}
- **Script(s)**: {relative path to main script}

### Random Seeds

- Seed: {value, or N/A if deterministic}

---

## Supercomputer Job

| Field | Value |
|-------|-------|
| Cluster | {Anvil / Negishi / etc.} |
| Scheduler | SLURM / PBS |
| Job ID | {job ID when submitted} |
| Partition/Queue | {partition name} |
| Nodes Requested | {count} |
| Cores Requested | {count} |
| Memory Requested | {e.g., 64GB} |
| Walltime Requested | {e.g., 04:00:00} |
| Submitted | {YYYY-MM-DD HH:MM:SS} |
| Started | {YYYY-MM-DD HH:MM:SS} |
| Ended | {YYYY-MM-DD HH:MM:SS} |
| Actual Runtime | {duration} |

### Job Script

```bash
# Paste or link to job script
```

---

## Execution Log

| Date | Action | Result/Notes |
|------|--------|--------------|
| {date_created} | Created | Initialized experiment |
| | | |

---

## Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Results Data | `results/output.csv` | {description} |
| Figures | `results/figures/` | {description} |
| Job Log | `logs/job.out` | {description} |
| Error Log | `logs/job.err` | {description} |

---

## Results & Analysis

### Summary Statistics

| Metric | Value | 95% CI | Notes |
|--------|-------|--------|-------|
| | | | |

### Key Observations

1. {Observation with supporting evidence}
2. {Another observation}
3. {Additional observations}

### Visualizations

{Include figures with captions}

![Figure 1: Description](results/figures/fig1.png)
*Caption explaining what the figure shows*

### Statistical Tests

| Test | Result | p-value | Interpretation |
|------|--------|---------|----------------|
| | | | |

---

## Discussion

### Interpretation

{What do these results mean in context of the hypothesis?}

### Limitations

- Limitation 1
- Limitation 2

### Comparison to Prior Work

{How do these results compare to literature?}

---

## Conclusion

- [ ] Hypothesis Confirmed
- [ ] Hypothesis Rejected  
- [ ] Inconclusive (needs more data/analysis)

**Key Takeaway**: {One-sentence summary of the finding}

### Next Steps

- [ ] {Follow-up action 1}
- [ ] {Follow-up action 2}
- [ ] Log to Findings Log: {Yes/No}

---

## Related Findings

| Finding ID | Link |
|------------|------|
| | |

---

## Notes

{Additional context, ideas, or considerations}
