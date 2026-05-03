# FRESCO Dataset Reconstruction Recommendations

**From**: Research findings (EXP-011, EXP-012, EXP-013)
**To**: Dataset Creator
**Date**: 2026-02-01

---

## Executive Summary

Our research discovered that **memory metrics are non-comparable across clusters** due to systematic 6-9× offsets. This causes catastrophic cross-site prediction failures (R² = -24). We identified the problem but couldn't definitively diagnose the root cause from the transformed data alone.

With access to the original untransformed data, you can **fix this at the source**.

---

## Critical Additions

### 1. Memory Measurement Metadata (HIGHEST PRIORITY)

For each cluster, add explicit documentation/columns for:

| Field | Why It Matters |
|-------|----------------|
| `memory_unit` | "bytes", "KB", "MB", "GB" — we *think* it's GB but can't confirm |
| `memory_source` | "cgroups", "SLURM_jobacct", "proc_meminfo", "custom" — each measures differently |
| `memory_includes_cache` | boolean — does `memused` include page cache/buffers? (can be 2-5× difference) |
| `memory_aggregation` | "max_per_node", "sum_across_nodes", "max_per_process" — we inferred max_per_node but want confirmation |
| `memory_sampling_interval_sec` | 60, 300, etc. — affects peak detection |

**Why**: We saw Anvil report 9× higher memory than Conte. Without metadata, we can't tell if this is:
- Real workload difference (AI/ML jobs use more memory)
- Measurement difference (Anvil includes cache, others don't)
- Unit difference (unlikely but possible)
- Aggregation difference (we ruled this out, but confirmation helps)

### 2. Hardware Context Per Job

| Field | Why It Matters |
|-------|----------------|
| `node_memory_gb` | Actual RAM per node for this job's allocation |
| `node_type` | "standard", "largemem", "gpu", etc. |
| `gpu_memory_gb` | If applicable — GPU memory is separate from host memory |

**Why**: We used approximate node RAM (32/128/256 GB) for sanity checks. Actual values per job would enable:
- Normalization: `memory_fraction = peak_memused / node_memory_gb`
- Cross-site comparability: Compare memory *efficiency*, not absolute values
- Anomaly detection: Jobs using >90% of node RAM

### 3. Standardized Derived Columns

Add these pre-computed, documented columns:

```
peak_memory_bytes       -- Absolute peak, always in bytes
peak_memory_per_node_gb -- MAX(per-node peaks), always in GB  
peak_memory_fraction    -- peak_memory_per_node_gb / node_memory_gb
memory_efficiency       -- peak / (requested or allocated)
```

**Why**: Let users choose their normalization. Some analyses need absolute values; others need fractions. Currently we have to guess.

---

## Schema Improvements

### 4. Explicit Cluster Identifier Column

Currently we infer cluster from filename suffix (`_S`, `_C`, no suffix). Add explicit column:

```
cluster_id     -- "stampede", "conte", "anvil" (not tokens)
cluster_era    -- "stampede1", "stampede2" if hardware changed
```

**Why**: Filename parsing is fragile. Hardware refreshes mid-dataset (new nodes, new OS) should be trackable.

### 5. Timelimit Units Consistency

We discovered timelimit is in **minutes** for Stampede but **seconds** for Conte/Anvil. Add:

```
timelimit_seconds  -- Always seconds, normalized at source
timelimit_original -- Original value as submitted
timelimit_unit     -- "seconds" or "minutes" (for provenance)
```

**Why**: We had to apply cluster-specific transforms. This should be done once, correctly, at dataset creation.

### 6. Timestamp Standardization

We observed type inconsistencies:
- Older shards: `timestamp[us]` without timezone
- 2022 shards: `timestamp[ns, tz=UTC]`

Recommendation: **All timestamps in `timestamp[us, tz=UTC]`** with explicit documentation.

---

## Structural Recommendations

### 7. Cluster-Level Metadata File

Create `clusters.json` or `clusters.parquet`:

```json
{
  "stampede": {
    "institution": "TACC",
    "years_active": [2013, 2018],
    "node_types": {
      "standard": {"memory_gb": 32, "cores": 16},
      "largemem": {"memory_gb": 128, "cores": 32}
    },
    "memory_collection": {
      "source": "SLURM_jobacct_gather",
      "unit": "KB",
      "includes_cache": false,
      "sampling_interval_sec": 60,
      "aggregation": "max_per_node"
    },
    "timelimit_unit": "minutes"
  },
  "conte": { ... },
  "anvil": { ... }
}
```

**Why**: This single file would have answered 80% of our diagnostic questions immediately.

### 8. Versioning and Changelog

```
FRESCO_v2.0/
├── CHANGELOG.md        -- What changed from v1
├── SCHEMA.md           -- Column definitions, units, transforms
├── clusters.json       -- Per-cluster metadata
├── chunks/             -- Parquet files
└── validation/         -- Scripts to verify consistency
```

---

## Validation Scripts to Include

### 9. Cross-Cluster Consistency Checks

Provide scripts that verify:

```python
# 1. Memory sanity: no job uses more than node RAM
assert (df.peak_memory_gb <= df.node_memory_gb * 1.1).all()

# 2. Timelimit consistency: all in seconds
assert df.timelimit_seconds.min() > 0
assert df.timelimit_seconds.max() < 365 * 86400

# 3. Cross-cluster distribution check
for cluster in clusters:
    print(f"{cluster}: memory p50={df[df.cluster==cluster].peak_memory_gb.median()}")
# Flag if any cluster is >3× different from others
```

### 10. Reproducibility Manifest

For each Parquet file, provide:
- Original source (which SLURM database, which monitoring system)
- Transforms applied (unit conversions, filtering, anonymization)
- MD5 hash for integrity

---

## Optional Enhancements

### 11. Job-Level Features We Wished We Had

| Feature | Use Case |
|---------|----------|
| `requested_memory_gb` | Compare actual vs requested (efficiency analysis) |
| `partition` | Already present, but ensure consistency |
| `executable_hash` | Anonymized hash of job command (for workload clustering) |
| `user_job_count` | How many jobs has this user run? (for user-level modeling) |
| `array_job_id` | Link array job tasks together |

### 12. Failure Information

Expand exitcode semantics:
```
exit_code_raw        -- Original value
exit_signal          -- If killed by signal
oom_killed           -- boolean, was this OOM?
timeout_killed       -- boolean, hit walltime limit?
```

**Why**: We found anomalies predict failures at 1.6-3.7× baseline (FIND-008). Richer failure info would enable deeper analysis.

---

## Summary: The Minimum Viable Fix

If you do **only three things**, do these:

1. **Add `clusters.json`** with memory measurement methodology per cluster (source, units, includes_cache, aggregation)

2. **Add `node_memory_gb`** per job so we can compute `peak_memory_fraction`

3. **Normalize timelimit to seconds** at the source, with documentation

These three changes would have:
- Eliminated 2 days of diagnostic work (EXP-012)
- Enabled immediate recalibration without guessing
- Made the 9× offset interpretable (real workload difference vs measurement artifact)

---

## Offer to Collaborate

I would be happy to:
- Run validation scripts on a test dataset
- Write the SCHEMA.md documentation
- Design the consistency checks
- Test cross-site prediction on v2.0 to verify improvements

This research has generated publication-ready findings. A v2.0 dataset with these fixes would be a significant contribution to the HPC research community.

---

**Contact**: Ready to help rebuild FRESCO with these improvements.
