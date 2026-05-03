# FRESCO v2.0 Complete Schema Specification

**Last Updated**: 2026-02-01
**Status**: Proposed based on EXP-011/012/013 research findings

---

## Original Data Location

**Source Repository**: `/depot/sbasitory/`

**Structure**:
```
repository/
├── Anvil/
│   ├── JobAccounting/          # Monthly CSV files (job_accounting_*_anon.csv)
│   └── JobResourceUsage/       # Monthly time-series (job_ts_metrics_*_anon.csv)
├── Conte/
│   ├── AccountingStatistics/   # SLURM accounting data
│   ├── TACC_Stats/            # Monthly subdirs (2015-03 through 2017-12)
│   └── kickstand_2015.csv     # Outage/event data
├── Stampede/
│   ├── AccountingStatistics/   # SLURM accounting data  
│   └── TACC_Stats/            # Node subdirs (NODE1 through NODE6976)
└── FRESCO_Repository_Description.pdf  # Official documentation
```

**Key Observations**:
- **Anvil** (2022-2023): Modern format with separate accounting + time-series CSVs
- **Conte** (2015-2017): TACC_Stats monthly directories + accounting files
- **Stampede** (2013-2018): TACC_Stats by-node directories + accounting files
- Each cluster has distinct data organization reflecting different collection eras

**Current Combined Dataset**: `/depot/sbagchi/data/josh/FRESCO/chunks/` (hourly Parquet shards)

---

## Schema Overview

Total columns: **65** (organized into 9 categories)
- Core: Required for every job
- Normalized: Cross-site comparable values
- Original: Source-specific values for provenance
- Derived: Computed from other columns
- Metadata: Context and documentation

---

## CATEGORY 1: Job Identity (6 columns)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `jid` | string | ✓ | Original job ID from source cluster |
| `jid_global` | string | ✓ | Globally unique: `{cluster}_{jid}` |
| `cluster` | string | ✓ | Cluster identifier ("stampede", "conte", "anvil") |
| `array_job_id` | string | nullable | Parent array job ID if this is a task |
| `array_task_id` | int64 | nullable | Task index within array job |
| `job_name` | string | nullable | User-provided job name |

**Rationale**: 
- `cluster` must be explicit (not inferred from filename)
- `jid_global` ensures uniqueness across dataset
- Array job linkage enables workflow analysis

---

## CATEGORY 2: Hardware Context (10 columns) **[NEW - CRITICAL]**

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `node_memory_gb` | float64 | ✓ | Actual RAM per node for this job's allocation |
| `node_cores` | int32 | ✓ | Physical cores per node |
| `node_type` | string | ✓ | Node category ("standard", "largemem", "gpu") |
| `node_architecture` | string | nullable | CPU architecture ("x86_64", "arm64") |
| `node_cpu_model` | string | nullable | CPU model (e.g., "Xeon E5-2680") |
| `gpu_count_per_node` | int32 | nullable | GPUs per node (0 if CPU-only) |
| `gpu_memory_gb_per_device` | float64 | nullable | VRAM per GPU device |
| `gpu_model` | string | nullable | GPU model (e.g., "A100-40GB", "V100") |
| `hardware_generation` | string | ✓ | Hardware era ID (links to clusters.json) |
| `interconnect` | string | nullable | Network fabric ("InfiniBand EDR", "Ethernet") |

**Rationale**: 
- **Critical for normalization**: `node_memory_gb` enables `peak_memory_fraction`
- Hardware heterogeneity within clusters requires per-job tracking
- GPU fields support growing ML/AI workload analysis
- `hardware_generation` handles mid-dataset hardware refreshes

---

## CATEGORY 3: Time Fields (12 columns)

### 3.1 Normalized Timestamps (always UTC)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `submit_time` | timestamp[us, tz=UTC] | ✓ | When job was submitted to scheduler |
| `eligible_time` | timestamp[us, tz=UTC] | nullable | When job became eligible (dependencies met) |
| `start_time` | timestamp[us, tz=UTC] | ✓ | When job started executing |
| `end_time` | timestamp[us, tz=UTC] | ✓ | When job finished/terminated |

### 3.2 Derived Time Fields

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `wait_time_sec` | float64 | ✓ | `start_time - submit_time` |
| `runtime_sec` | float64 | ✓ | `end_time - start_time` (walltime) |
| `yearmonth` | int32 | ✓ | YYYYMM for temporal partitioning |

### 3.3 Time Limits (Normalized)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `timelimit_sec` | float64 | ✓ | Walltime limit in seconds (normalized) |
| `timelimit_original` | float64 | ✓ | Original value from source |
| `timelimit_unit_original` | string | ✓ | Unit in source ("seconds", "minutes") |

### 3.4 Temporal Metadata

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `timed_out` | boolean | ✓ | Did job hit walltime limit? |
| `runtime_efficiency` | float64 | ✓ | `runtime_sec / timelimit_sec` (0-1) |

**Rationale**:
- All timestamps in `[us, tz=UTC]` eliminates ambiguity
- Preserve `timelimit_original` + unit for provenance
- `timed_out` directly computable but commonly needed

---

## CATEGORY 4: Resource Allocation (6 columns)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `nhosts` | int32 | ✓ | Number of nodes allocated |
| `ncores` | int32 | ✓ | Total cores allocated across all nodes |
| `cores_per_node` | int32 | ✓ | Cores per node (ncores / nhosts) |
| `gpus_allocated` | int32 | nullable | Total GPUs allocated (0 if none) |
| `memory_requested_gb` | float64 | nullable | Memory explicitly requested by user |
| `partition` | string | ✓ | Queue/partition name |

**Rationale**:
- `cores_per_node` enables node-type inference
- `memory_requested_gb` enables efficiency analysis (actual vs requested)

---

## CATEGORY 5: Memory Metrics (11 columns) **[IMPROVED - HIGH PRIORITY]**

### 5.1 Normalized Memory (Cross-Site Comparable)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `peak_memory_gb` | float64 | ✓ | Peak memory usage in GB (normalized) |
| `peak_memory_per_node_gb` | float64 | ✓ | Peak per single node (if multi-node) |
| `peak_memory_fraction` | float64 | ✓ | `peak_memory_per_node_gb / node_memory_gb` |
| `avg_memory_gb` | float64 | nullable | Time-averaged memory usage |

### 5.2 Original Memory (Provenance)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `peak_memory_original` | float64 | ✓ | Exact value from source system |
| `memory_unit_original` | string | ✓ | Unit in source ("bytes", "KB", "MB", "GB") |

### 5.3 Memory Metadata

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `memory_sample_count` | int32 | ✓ | Number of samples collected for this job |
| `memory_collection_method` | string | ✓ | Links to clusters.json ("slurm_jobacct", "cgroups") |
| `memory_includes_cache` | boolean | ✓ | Does measurement include page cache? |

### 5.4 Derived Memory Metrics

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `memory_efficiency` | float64 | nullable | `peak_memory_gb / memory_requested_gb` (if requested known) |
| `oom_killed` | boolean | ✓ | Job killed due to out-of-memory |

**Rationale**:
- **`peak_memory_fraction` is the key to cross-site comparison**
- Preserve original values + units for debugging
- Explicit metadata fields (`memory_includes_cache`) document measurement differences
- `oom_killed` extracted from exit code/signal

---

## CATEGORY 6: CPU Metrics (6 columns)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `cpu_time_sec` | float64 | ✓ | Total CPU seconds consumed (user + system) |
| `cpu_user_sec` | float64 | nullable | User-space CPU seconds |
| `cpu_system_sec` | float64 | nullable | Kernel-space CPU seconds |
| `cpu_efficiency` | float64 | ✓ | `cpu_time_sec / (runtime_sec * ncores)` |
| `cpu_peak_percent` | float64 | nullable | Peak CPU utilization across job (0-100 per core) |
| `cpu_avg_percent` | float64 | nullable | Time-averaged CPU utilization |

**Rationale**:
- `cpu_efficiency` is key metric for resource waste analysis
- Distinguish user vs system time for characterization

---

## CATEGORY 7: I/O Metrics (4 columns)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `io_read_gb` | float64 | nullable | Total data read (all filesystems) |
| `io_write_gb` | float64 | nullable | Total data written |
| `nfs_ops_count` | int64 | nullable | NFS operation count |
| `block_io_ops_count` | int64 | nullable | Block I/O operation count |

**Rationale**:
- Normalize to GB for cross-site comparison
- Operation counts useful for I/O pattern analysis
- Some clusters may not have all metrics (nullable)

---

## CATEGORY 8: Job Completion & Status (7 columns)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `exit_code` | int32 | ✓ | Numeric exit code |
| `exit_signal` | string | nullable | Signal name if killed (e.g., "SIGKILL", "SIGTERM") |
| `state` | string | ✓ | Final state ("COMPLETED", "FAILED", "TIMEOUT", "CANCELLED") |
| `failed` | boolean | ✓ | Did job fail? (exit_code != 0 or abnormal termination) |
| `cancelled_by_user` | boolean | ✓ | User-initiated cancellation |
| `node_failure` | boolean | ✓ | Node/system failure during job |
| `preempted` | boolean | ✓ | Job preempted by scheduler |

**Rationale**:
- Rich failure categorization enables targeted failure analysis
- Distinguish user actions from system issues
- `state` is human-readable summary

---

## CATEGORY 9: User & Accounting (3 columns)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `username_hash` | string | ✓ | Anonymized, consistent within cluster |
| `account` | string | ✓ | Allocation/project account |
| `qos` | string | nullable | Quality of Service class |

**Rationale**:
- `username_hash` preserves user consistency for user-level modeling
- Consistent hashing within cluster, different salt across clusters for privacy
- `account` enables group-level analysis

---

## Summary Table: Column Counts by Category

| Category | Core | Normalized | Original | Derived | Metadata | Total |
|----------|------|-----------|----------|---------|----------|-------|
| 1. Job Identity | 6 | - | - | - | - | 6 |
| 2. Hardware Context | - | 10 | - | - | - | 10 |
| 3. Time Fields | 4 | 3 | 2 | 3 | - | 12 |
| 4. Resource Allocation | 6 | - | - | - | - | 6 |
| 5. Memory Metrics | - | 4 | 2 | 2 | 3 | 11 |
| 6. CPU Metrics | 1 | - | - | 5 | - | 6 |
| 7. I/O Metrics | - | 4 | - | - | - | 4 |
| 8. Job Status | 7 | - | - | - | - | 7 |
| 9. User/Accounting | 3 | - | - | - | - | 3 |
| **TOTAL** | **27** | **21** | **4** | **10** | **3** | **65** |

---

## Required vs. Nullable Breakdown

| Status | Count | Notes |
|--------|-------|-------|
| Required (✓) | 48 | Must be present for every job |
| Nullable | 17 | May be NULL if unavailable in source |

**Nullable columns by reason**:
- Hardware details may be unavailable for older jobs
- Some metrics not collected by all clusters (GPU, I/O)
- Optional user-provided fields (job_name, memory_requested)

---

## Companion Metadata: clusters.json

In addition to per-job columns, provide cluster-level metadata:

```json
{
  "clusters": {
    "stampede": {
      "institution": "TACC",
      "location": "Austin, TX",
      "operational_period": {
        "start": "2013-01-01",
        "end": "2018-04-30"
      },
      "hardware_generations": {
        "stampede_gen1": {
          "start": "2013-01-01",
          "end": "2015-06-30",
          "node_types": {
            "standard": {
              "memory_gb": 32,
              "cores": 16,
              "cpu_model": "Xeon E5-2680",
              "count": 6400
            },
            "largemem": {
              "memory_gb": 256,
              "cores": 32,
              "cpu_model": "Xeon E5-4650",
              "count": 128
            }
          }
        },
        "stampede_gen2": { ... }
      },
      "memory_collection": {
        "method": "slurm_jobacct_gather",
        "source_field": "JobAcctRaw.MaxRSS",
        "includes_cache": true,
        "unit_in_source": "bytes",
        "aggregation": "max_per_node",
        "sampling_interval_sec": 60,
        "known_issues": [
          "Jobs <60s may have no samples",
          "Collection interrupted 2015-03-15 to 2015-03-20"
        ]
      },
      "timelimit_unit": "minutes",
      "timezone": "America/Chicago"
    },
    "conte": { ... },
    "anvil": { ... }
  }
}
```

---

## Data Types Specification

### Numeric Types

```python
int32:  Small integers (counts, IDs within cluster)
int64:  Large integers (global IDs, high counts)
float64: All floating-point (memory, time, fractions)
```

**Why float64 for everything numeric**: Avoids precision loss during normalization and unit conversion.

### String Types

```python
string: Variable-length UTF-8
```

**No dictionary encoding at schema level**: Let Parquet handle compression.

### Timestamp Types

```python
timestamp[us, tz=UTC]: Microsecond precision, UTC timezone
```

**Rationale**: Microseconds sufficient for HPC, UTC eliminates ambiguity.

---

## Partitioning Strategy

Recommend Hive-style partitioning by date:

```
fresco_v2/
  cluster=stampede/
    year=2013/
      month=02/
        *.parquet
      month=03/
        *.parquet
  cluster=conte/
    year=2015/
      month=01/
        *.parquet
```

**Benefits**:
- Enables cluster-specific queries without scanning all data
- Temporal queries leverage partition pruning
- Scales to additional clusters

---

## Validation Constraints

Every Parquet file should satisfy:

```python
# 1. Physical constraints
assert (df.peak_memory_per_node_gb <= df.node_memory_gb * 1.1).all()  # Allow 10% overhead
assert (df.runtime_sec > 0).all()
assert (df.ncores > 0).all()

# 2. Logical constraints
assert (df.end_time >= df.start_time).all()
assert (df.start_time >= df.submit_time).all()

# 3. Derived field consistency
assert np.allclose(df.peak_memory_fraction, 
                   df.peak_memory_per_node_gb / df.node_memory_gb)
assert np.allclose(df.runtime_sec, 
                   (df.end_time - df.start_time).dt.total_seconds())

# 4. Metadata consistency
assert df.memory_collection_method.isin(['slurm_jobacct', 'cgroups', 'custom']).all()
assert df.cluster.isin(['stampede', 'conte', 'anvil']).all()
```

---

## Migration from v1.0 to v2.0

### Column Mapping

| v1.0 Column | v2.0 Column(s) | Transform |
|-------------|----------------|-----------|
| `value_memused` | `peak_memory_gb`, `peak_memory_original` | Normalize units, preserve original |
| `timelimit` | `timelimit_sec`, `timelimit_original` | Convert to seconds, preserve original |
| (derived from filename) | `cluster` | Extract suffix → explicit column |
| N/A | `node_memory_gb` | NEW - map from node inventory |
| `time` | (removed) | Was individual sample timestamp; now job-level only |
| `exitcode` | `exit_code` | Parse to int32 |

### New Columns (No v1.0 Equivalent)

These require joining with external data sources:
- `node_memory_gb`: From node inventory
- `hardware_generation`: From timeline records
- `memory_collection_method`: From documentation
- `memory_includes_cache`: From SLURM config
- All derived metrics (`peak_memory_fraction`, etc.)

---

## Versioning

```
fresco_v2.0.0/
  CHANGELOG.md
  SCHEMA.md (this document)
  clusters.json
  validation_scripts/
  data/
```

**Semantic versioning**:
- Major: Breaking schema changes
- Minor: New columns added (backward compatible)
- Patch: Bug fixes in existing data

---

## Example Row (JSON representation)

```json
{
  "jid": "12345678",
  "jid_global": "stampede_12345678",
  "cluster": "stampede",
  "array_job_id": null,
  "array_task_id": null,
  "job_name": "my_simulation",
  
  "node_memory_gb": 32.0,
  "node_cores": 16,
  "node_type": "standard",
  "node_cpu_model": "Xeon E5-2680",
  "gpu_count_per_node": 0,
  "hardware_generation": "stampede_gen1",
  
  "submit_time": "2015-06-15T10:30:00.000000Z",
  "start_time": "2015-06-15T10:35:00.000000Z",
  "end_time": "2015-06-15T12:45:00.000000Z",
  "wait_time_sec": 300.0,
  "runtime_sec": 7800.0,
  "yearmonth": 201506,
  "timelimit_sec": 14400.0,
  "timelimit_original": 240.0,
  "timelimit_unit_original": "minutes",
  "timed_out": false,
  "runtime_efficiency": 0.54,
  
  "nhosts": 4,
  "ncores": 64,
  "cores_per_node": 16,
  "gpus_allocated": 0,
  "memory_requested_gb": null,
  "partition": "normal",
  
  "peak_memory_gb": 18.5,
  "peak_memory_per_node_gb": 18.5,
  "peak_memory_fraction": 0.578,
  "avg_memory_gb": 15.2,
  "peak_memory_original": 19862347776.0,
  "memory_unit_original": "bytes",
  "memory_sample_count": 130,
  "memory_collection_method": "slurm_jobacct",
  "memory_includes_cache": true,
  "memory_efficiency": null,
  "oom_killed": false,
  
  "cpu_time_sec": 425000.0,
  "cpu_user_sec": 420000.0,
  "cpu_system_sec": 5000.0,
  "cpu_efficiency": 0.85,
  "cpu_peak_percent": 95.2,
  "cpu_avg_percent": 85.0,
  
  "io_read_gb": 125.0,
  "io_write_gb": 45.0,
  "nfs_ops_count": 1250000,
  "block_io_ops_count": 5000,
  
  "exit_code": 0,
  "exit_signal": null,
  "state": "COMPLETED",
  "failed": false,
  "cancelled_by_user": false,
  "node_failure": false,
  "preempted": false,
  
  "username_hash": "a1b2c3d4e5f6",
  "account": "project123",
  "qos": "normal"
}
```

---

## Schema File Formats

Provide schema in multiple formats:

1. **schema.json**: JSON Schema for validation
2. **schema.parquet**: Parquet metadata
3. **schema.sql**: SQL DDL for database import
4. **SCHEMA.md**: Human-readable documentation (this file)

---

**This schema specification is ready for implementation. All 65 columns address issues discovered in EXP-011/012/013 research while maintaining compatibility with existing v1.0 analyses.**
