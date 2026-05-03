# FRESCO Dataset Combination: Agent Design Guide

**Purpose**: Instructions for an LLM agent tasked with designing the process of combining multi-institutional HPC job data into the FRESCO dataset.

**Context**: This guide is informed by extensive downstream research that revealed critical issues with cross-site data comparability. The agent should treat this as a **data engineering problem with scientific consequences**—decisions made during combination directly impact what analyses are possible.

---

## PART 0: Source Data Structure

**CRITICAL**: Before beginning any design work, the agent must understand the source data organization.

**Repository Location**: `/depot/sbagchi/www/fresco/repository/`

**Cluster-Specific Organization**:

### Anvil (2022-2023)
```
Anvil/
├── JobAccounting/
│   ├── job_accounting_jun2022_anon.csv
│   ├── job_accounting_jul2022_anon.csv
│   └── ... (monthly files through jun2023)
└── JobResourceUsage/
    ├── job_ts_metrics_jun2022_anon.csv
    ├── job_ts_metrics_jul2022_anon.csv
    └── ... (monthly time-series metrics)
```
- **Two-file format**: Accounting (job-level) + ResourceUsage (time-series metrics)
- **Modern era**: Likely SLURM-native collection
- **Temporal resolution**: Time-series suggests periodic sampling within jobs

### Conte (2015-2017)
```
Conte/
├── AccountingStatistics/  # SLURM sacct-style data
├── TACC_Stats/
│   ├── 2015-03/
│   ├── 2015-04/
│   └── ... (monthly subdirs through 2017-12)
├── kickstand_2015.csv     # System events/outages
└── liblist/               # Unknown purpose
```
- **TACC_Stats format**: Directory-per-month with internal structure TBD
- **Hybrid era**: SLURM accounting + TACC monitoring infrastructure
- **Outage tracking**: kickstand file documents downtime

### Stampede (2013-2018)
```
Stampede/
├── AccountingStatistics/  # SLURM sacct-style data
└── TACC_Stats/
    ├── NODE1/
    ├── NODE2/
    └── ... (6976 node directories)
```
- **TACC_Stats format**: Directory-per-node (6976 nodes)
- **Legacy era**: Earliest cluster, different monitoring conventions
- **Node-centric organization**: Stats likely partitioned by hardware

**Official Documentation**: `FRESCO_Repository_Description.pdf` (387KB) provides authoritative source schema.

**Combined Output** (v1.0): `/depot/sbagchi/data/josh/FRESCO/chunks/` (hourly Parquet shards by date/hour)

**Key Design Implications**:
1. **Format heterogeneity**: Three distinct collection systems (Anvil CSV pair, Conte hybrid, Stampede node-dirs)
2. **Temporal organization varies**: Anvil/Conte use monthly files; Stampede uses node partitioning
3. **Era effects matter**: 10-year span means changing SLURM versions, monitoring tools, hardware generations
4. **Join complexity**: Must correlate accounting data with time-series metrics across different granularities

---

## PART 1: Questions to Ask Before Designing

### 1.1 Memory Metrics (CRITICAL)

These questions are **blocking**—do not proceed without answers:

```
1. For each source cluster, what tool collects memory metrics?
   - SLURM jobacct_gather?
   - cgroups directly?
   - Custom monitoring daemon?
   - Node-level sampling (e.g., collectd, Prometheus)?

2. What exactly does "memory used" mean in each source?
   - RSS (Resident Set Size) only?
   - RSS + page cache + buffers?
   - cgroup memory.usage_in_bytes?
   - Something else?

3. What are the units in each source?
   - Bytes? KB? MB? GB?
   - Are they consistent within each source?

4. For multi-node jobs, how is memory aggregated?
   - Max across all nodes?
   - Sum across all nodes?
   - Max per-process?
   - Reported per-node (multiple rows)?

5. What is the sampling interval?
   - Every 60 seconds? 300 seconds? Variable?
   - Does this affect peak detection?

6. Are there known collection gaps or failures?
   - Certain partitions not monitored?
   - Collection failures during outages?
   - Jobs too short to sample?
```

**Why these matter**: Our research found 6-9× systematic offsets between clusters. Without answers to these questions, we cannot determine if offsets are real workload differences or measurement artifacts.

### 1.2 Time-Related Fields

```
7. What unit is timelimit stored in for each source?
   - Seconds? Minutes? Hours?
   - Is it the user-requested value or scheduler-adjusted?

8. What timezone are timestamps in?
   - UTC? Local time? Mixed?
   - Are they consistent within each source?

9. What precision are timestamps?
   - Seconds? Milliseconds? Microseconds?
   - Do they need alignment?

10. How are submit/start/end times recorded for array jobs?
    - Per-task times? Parent job times? Both?
```

**Why these matter**: We discovered timelimit was in minutes for one cluster and seconds for others. This required cluster-specific transforms that should be done once at source.

### 1.3 Hardware Context

```
11. Can you provide node memory size for each job?
    - From allocation records?
    - From node inventory matched by hostname?

12. Do node configurations change over time?
    - Hardware refreshes?
    - Memory upgrades?
    - Need version tracking?

13. Are there different node types per cluster?
    - Standard vs large-memory vs GPU nodes?
    - How to identify which type a job used?

14. For GPU jobs, is GPU memory tracked separately?
    - Different field? Same field?
    - Different collection mechanism?
```

**Why these matter**: Without node memory size, we cannot compute memory efficiency (peak/capacity). This is the key to cross-site normalization.

### 1.4 Job Identity and Relationships

```
15. How are job IDs structured in each source?
    - Unique within cluster?
    - Need cluster prefix for global uniqueness?

16. How are array jobs represented?
    - Parent job + tasks?
    - Separate job IDs with linkage?
    - Need to preserve relationships?

17. Are there job dependencies to track?
    - Job chains?
    - Workflow DAGs?

18. How is user identity handled?
    - Already anonymized?
    - Need consistent anonymization across clusters?
    - Preserve user consistency within clusters for analysis?
```

### 1.5 Failure and Exit Information

```
19. What exit code semantics are used?
    - SLURM standard codes?
    - Custom codes?
    - String descriptions?

20. Can you distinguish failure modes?
    - OOM kills (SIGKILL with specific reason)?
    - Timeouts (hit walltime)?
    - User cancellation?
    - Node failures?

21. Are there job state transitions available?
    - PENDING → RUNNING → COMPLETED timeline?
    - Preemption events?
```

### 1.6 Source Provenance

```
22. What is the authoritative source for each cluster?
    - SLURM database exports?
    - Monitoring system archives?
    - Multiple sources needing reconciliation?

23. What date ranges are available per cluster?
    - Any gaps?
    - Any overlaps with other clusters?

24. Have there been schema changes over time in sources?
    - Column additions/removals?
    - Semantic changes to existing columns?

25. Is there documentation for the original data collection?
    - SLURM configuration files?
    - Monitoring setup documents?
    - Institutional policies?
```

---

## PART 2: Critical Design Factors

### 2.1 The Normalization vs. Preservation Tradeoff

**Core tension**: Should you transform values to a common scale, or preserve originals with metadata?

**Recommendation**: Do both.

```
# For each metric with variation, provide:
peak_memory_original    # As recorded in source
peak_memory_unit        # "bytes", "KB", etc.
peak_memory_gb          # Normalized to GB
peak_memory_fraction    # Normalized to node capacity (0-1)
```

**Rationale**: 
- Researchers doing cross-site studies need normalized values
- Researchers debugging cluster-specific issues need originals
- Metadata enables verification and custom normalization

### 2.2 The Documentation Imperative

**Every transformation must be documented**. Create a manifest:

```yaml
columns:
  peak_memory_gb:
    description: "Peak memory usage in gigabytes"
    derived_from: "value_memused (source-specific)"
    transforms:
      stampede: "value_memused / 1024 / 1024 / 1024"  # was bytes
      conte: "value_memused / 1024 / 1024"            # was KB
      anvil: "value_memused"                          # already GB
    aggregation: "MAX per job across all samples"
    caveats:
      - "Stampede includes page cache; others do not"
      - "Anvil sampling interval is 5min; others are 1min"
```

**Why this matters**: Our research spent days inferring what could have been documented in hours.

### 2.3 Cluster Metadata as First-Class Data

Don't just document clusters in README—make metadata queryable:

```python
# clusters.parquet or clusters.json
{
  "cluster_id": "stampede",
  "institution": "TACC",
  "hardware_generations": [
    {
      "start_date": "2013-01-01",
      "end_date": "2015-06-30",
      "node_types": {
        "normal": {"memory_gb": 32, "cores": 16},
        "largemem": {"memory_gb": 256, "cores": 32}
      }
    },
    {
      "start_date": "2015-07-01",
      "end_date": "2018-04-30",
      "node_types": { ... }  # After hardware refresh
    }
  ],
  "memory_collection": {
    "method": "slurm_jobacct_gather",
    "includes_cache": true,
    "unit": "bytes",
    "sampling_interval_sec": 60,
    "aggregation": "max_per_node"
  },
  "timelimit_unit": "minutes"
}
```

### 2.4 Handling Incomparability Explicitly

Some things may be fundamentally incomparable. **That's okay—document it.**

```python
# Add a comparability matrix
cross_site_comparability:
  runtime_sec: 
    comparable: true
    notes: "Walltime is standardized across SLURM installations"
  
  peak_memory_gb:
    comparable: false
    reason: "Different collection methods (cache inclusion varies)"
    mitigation: "Use peak_memory_fraction for cross-site analysis"
  
  cpu_efficiency:
    comparable: true
    notes: "Computed consistently from CPU time / walltime / cores"
```

### 2.5 Temporal Alignment Considerations

```
Design question: Should rows from different clusters be directly joinable?

Options:
1. Fully aligned: All timestamps in UTC, all intervals in seconds
2. Source-preserving: Keep original formats, document conversions
3. Hybrid: Normalized columns + original columns

Recommendation: Hybrid (option 3)
- submit_time, start_time, end_time: Always timestamp[us, tz=UTC]
- submit_time_original: Preserve source format for debugging
```

---

## PART 3: Information the Agent Needs

### 3.1 Source Data Samples

Request samples from each source to:
- Verify column presence and types
- Check value ranges and distributions
- Identify nulls, outliers, anomalies
- Test parsing and transformation logic

```
For each source cluster, provide:
- 1000 random jobs from early period
- 1000 random jobs from late period
- 100 known "interesting" jobs (failures, long-running, multi-node)
- Schema/column definitions
```

### 3.2 Institutional Knowledge

```
For each cluster, interview someone who knows:
- How was monitoring configured?
- Were there known issues or outages?
- Did collection methods change over time?
- What do operators consider "normal" behavior?
```

### 3.3 Use Case Requirements

```
Ask: What analyses should this dataset enable?

Must support:
- [ ] Cross-site workload comparison
- [ ] Runtime prediction
- [ ] Memory prediction
- [ ] Failure analysis
- [ ] User behavior studies
- [ ] Anomaly detection
- [ ] Resource efficiency studies
- [ ] Scheduling optimization research

For each, verify the schema supports it.
```

### 3.4 Downstream Validation Data

```
If available, collect "ground truth" for validation:
- Known OOM-killed jobs (to verify memory metrics)
- Known timeout failures (to verify timelimit/runtime)
- Jobs with known resource usage (from manual profiling)
- Synthetic benchmark jobs with predictable behavior
```

---

## PART 4: Lessons from Downstream Research

### 4.1 What Broke in Practice

| Issue | Impact | Prevention |
|-------|--------|------------|
| Memory offsets (6-9×) | Cross-site prediction failed (R²=-24) | Document measurement methodology; provide normalized columns |
| Timelimit unit variation | Required reverse-engineering | Normalize at source; document original units |
| Inferred cluster from filename | Fragile, error-prone | Add explicit cluster column |
| Missing node RAM size | Couldn't normalize memory | Add hardware context per job |
| Type inconsistencies (int32 vs int64) | Ingestion warnings | Standardize types across all files |
| Timestamp precision variation | Potential alignment issues | Use consistent precision (us, UTC) |

### 4.2 What Worked Well

| Feature | Benefit |
|---------|---------|
| Parquet format | Fast queries, schema enforcement |
| Partitioning by date | Enables time-range queries |
| Rich job attributes | Enabled diverse analyses |
| Raw time-series samples | Could compute custom aggregations |

### 4.3 The Key Insight

**Cross-site comparability is not automatic**. Just because two clusters both have a "memory" column doesn't mean the values are comparable. The combination process must either:

1. **Ensure comparability** through normalization and documentation
2. **Explicitly flag non-comparability** so researchers don't make invalid comparisons

---

## PART 5: Recommended Design Process

### Phase 1: Discovery (Before Any Code)

```
1. Collect source schemas from all clusters
2. Interview operators about collection methodology
3. Get sample data from each source
4. Document known issues and caveats
5. Define target use cases
```

### Phase 2: Schema Design

```
1. Design unified schema with:
   - Normalized columns for cross-site analysis
   - Original columns for provenance
   - Metadata columns for context
   
2. Create clusters.json with per-cluster metadata

3. Design comparability matrix

4. Review with domain experts
```

### Phase 3: Transformation Pipeline

```
1. Build per-cluster extraction scripts
2. Build normalization transforms (with tests!)
3. Build validation checks:
   - Value range checks
   - Null rate checks
   - Cross-cluster distribution comparisons
4. Build manifest generation (what transforms were applied)
```

### Phase 4: Validation

```
1. Run cross-site memory prediction (should work with R² > 0)
2. Check that peak_memory_fraction distributions are similar
3. Verify timelimit/runtime relationships are consistent
4. Spot-check known jobs against source records
```

### Phase 5: Documentation

```
1. README with quick start
2. SCHEMA.md with column definitions
3. METHODOLOGY.md with collection details per cluster
4. CHANGELOG.md for version tracking
5. VALIDATION.md with test results
```

---

## PART 6: Red Flags to Watch For

### During Discovery

- ⚠️ "We're not sure how memory is collected" → Investigate before proceeding
- ⚠️ "The collection method changed in 2016" → Need hardware_generation versioning
- ⚠️ "That cluster uses a custom monitoring stack" → Get detailed documentation

### During Transformation

- ⚠️ Memory values differ by >3× between clusters after normalization → Investigate methodology
- ⚠️ Large fraction of nulls in one cluster but not others → Collection difference
- ⚠️ Value ranges don't make physical sense → Unit or aggregation issue

### During Validation

- ⚠️ Cross-site prediction fails badly → Comparability issue not resolved
- ⚠️ Distribution shapes differ dramatically → May be valid (workload difference) or invalid (measurement difference)

---

## PART 7: Minimum Viable Metadata

If nothing else, the combined dataset **must** include:

```yaml
# PER-CLUSTER METADATA (clusters.json)
required:
  - cluster_id
  - memory_collection_method
  - memory_includes_cache (boolean)
  - memory_unit_in_source
  - timelimit_unit_in_source
  - typical_node_memory_gb
  - date_range_covered
  - known_collection_gaps

# PER-JOB COLUMNS (in parquet)
required:
  - cluster (explicit, not inferred)
  - node_memory_gb (actual or imputed with documentation)
  - peak_memory_gb (normalized)
  - timelimit_sec (normalized)
  - all_timestamps_in_utc (boolean or just make it true)
```

---

## Final Checklist for the Agent

Before finalizing the design, verify:

- [ ] Every column has a documented unit
- [ ] Every transformation is documented with source→target mapping
- [ ] Cluster metadata is queryable (not just in README)
- [ ] Memory metrics are either normalized OR explicitly flagged as non-comparable
- [ ] Hardware context (node RAM) is available per job
- [ ] Timestamps are in consistent format and timezone
- [ ] Validation scripts exist to verify comparability
- [ ] Known issues are documented, not hidden

---

## Contact for Questions

The research that informed this guide is available at:
- `Documentation/Master_Index.md` — Experiment overview
- `Documentation/Findings_Log.md` — Detailed findings
- `Experiments/EXP-011_*` through `EXP-013_*` — Specific studies

Key findings to review:
- FIND-027: Memory metrics non-standardized
- FIND-028: Systematic 6-9× offsets
- FIND-029: Aggregation is consistent (max-per-node)
- FIND-030: Calibration can rescue but requires target data

---

*This guide was generated from empirical research on FRESCO v1. Following these recommendations should prevent the comparability issues discovered in that research.*
