# FRESCO v2.0 Schema Design - Phase 2 Output

**Status**: Ready for domain expert review  
**Last Updated**: 2026-02-01  
**Phase**: 2 of 5 (Schema Design)

---

## Design Philosophy

The v2.0 schema follows three core principles informed by downstream research failures:

### 1. **Explicit over Implicit**
Every piece of metadata that was previously inferred is now explicit:
- `cluster` column (not from filename)
- `node_memory_gb` (not looked up later)
- `memory_includes_cache` (not assumed)
- `timelimit_unit_original` (not guessed)

### 2. **Preserve + Normalize**
For every metric with unit/methodology variation:
- **Original value**: Raw from source (provenance)
- **Normalized value**: Standardized for cross-cluster use
- **Metadata**: Unit, method, notes

Example:
```
peak_memory_original_value: 34359738368
peak_memory_original_unit: "bytes"
peak_memory_gb: 32.0
memory_includes_cache: true
memory_collection_method: "tacc_stats_custom"
```

### 3. **Hardware as Context**
Node characteristics joined at ingestion time:
- Enables on-the-fly normalization (`peak_memory / node_memory`)
- Supports hardware-stratified analysis
- Documents what hardware jobs actually ran on

---

## Complete 65-Column Schema

### Category 1: Job Identity (6 columns)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `jid` | string | No | All: JobID | Original cluster job ID |
| `jid_global` | string | No | Derived | Format: `{cluster}_{jid}` |
| `cluster` | string | No | Derived | "stampede", "conte", "anvil" |
| `array_job_id` | string | Yes | All: ArrayJobID | Parent ID if array task |
| `array_task_id` | int64 | Yes | All: ArrayTaskID | Task index |
| `job_name` | string | Yes | All: JobName | User-provided name |

**Transformations**: None (direct mapping)

**Validation**: 
- `jid_global` must be unique across entire dataset
- `cluster` must be in {"stampede", "conte", "anvil"}

---

### Category 2: Hardware Context (10 columns) **[NEW - CRITICAL]**

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `node_memory_gb` | float64 | No | Join: clusters.json → partition specs | **Key for normalization** |
| `node_cores` | int32 | No | Join: clusters.json → partition specs | Physical cores per node |
| `node_type` | string | No | Join: partition mapping | "standard", "largemem", "gpu", "knl" |
| `node_architecture` | string | Yes | Join: clusters.json | "x86_64" (all current) |
| `node_cpu_model` | string | Yes | Join: clusters.json | e.g., "Xeon E5-2680", "EPYC 7763" |
| `gpu_count_per_node` | int32 | No | Join: clusters.json | 0 for CPU-only |
| `gpu_memory_gb_per_device` | float64 | Yes | Join: clusters.json | VRAM per GPU |
| `gpu_model` | string | Yes | Join: clusters.json | e.g., "K20", "A100" |
| `hardware_generation` | string | No | Join: clusters.json | Generation ID |
| `interconnect` | string | Yes | Join: clusters.json | e.g., "Mellanox FDR IB" |

**Transformations**:
```python
def get_hardware_context(row):
    """Join job with hardware specs from clusters.json"""
    cluster = row['cluster']
    partition = row['partition']
    submit_date = row['submit_time'].date()
    
    # Find applicable hardware generation
    for gen in clusters[cluster]['hardware_generations']:
        if gen['start_date'] <= submit_date <= gen['end_date']:
            partition_spec = gen['partitions'][partition]
            return {
                'node_memory_gb': partition_spec['node_memory_gb'],
                'node_cores': partition_spec['node_cores'],
                'node_type': partition_spec['node_type'],
                'node_cpu_model': partition_spec.get('cpu_model'),
                'gpu_count_per_node': partition_spec.get('gpu_count_per_node', 0),
                'gpu_memory_gb_per_device': partition_spec.get('gpu_memory_gb_per_device'),
                'gpu_model': partition_spec.get('gpu_model'),
                'hardware_generation': gen['generation_id'],
                'interconnect': partition_spec.get('interconnect')
            }
```

**Validation**:
- `node_memory_gb` > 0 for all rows
- `node_cores` > 0 for all rows
- `gpu_count_per_node` >= 0
- Stampede partitions: {normal: 32GB, largemem: 256GB, gpu: 32GB}
- Conte partitions: {shared: 128GB, debug: 128GB, knl: 96GB}
- Anvil partitions: {gpu: 256GB, wide: 256GB, debug: 256GB, highmem: 1024GB}

---

### Category 3: Time Fields (12 columns)

#### 3.1 Normalized Timestamps (UTC, microsecond precision)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `submit_time` | timestamp[us, tz=UTC] | No | All: Submit | Converted to UTC |
| `eligible_time` | timestamp[us, tz=UTC] | Yes | All: Eligible (if available) | Dependencies met |
| `start_time` | timestamp[us, tz=UTC] | No | All: Start | Execution began |
| `end_time` | timestamp[us, tz=UTC] | No | All: End | Completion |

**Transformations** (timezone conversion):
```python
# Stampede: US/Central → UTC
# Conte/Anvil: US/Eastern → UTC
def normalize_timestamp(value, cluster):
    tz_map = {
        'stampede': 'US/Central',
        'conte': 'US/Eastern',
        'anvil': 'US/Eastern'
    }
    local = pd.to_datetime(value, tz=tz_map[cluster])
    return local.tz_convert('UTC')
```

#### 3.2 Normalized Time Durations (seconds)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `timelimit_sec` | int64 | No | All: Timelimit + transform | **Normalized to seconds** |
| `runtime_sec` | int64 | No | Derived: end - start | Actual runtime |
| `queue_time_sec` | int64 | No | Derived: start - submit | Wait time |

**Transformations** (THE CRITICAL FIX):
```python
def normalize_timelimit(value, cluster):
    """Fix the minutes vs seconds issue"""
    if cluster == 'stampede':
        # Stampede stores in MINUTES
        return int(value) * 60
    else:
        # Conte and Anvil already in seconds
        return int(value)
```

#### 3.3 Original Values (provenance)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `timelimit_original` | string | No | All: Timelimit (raw) | Exact source value |
| `timelimit_unit_original` | string | No | Derived from cluster | "minutes" or "seconds" |

#### 3.4 Derived Time Metrics

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `submit_hour` | int8 | No | Derived: submit_time.hour | [0-23] |
| `submit_dow` | int8 | No | Derived: submit_time.dayofweek | [0-6], Monday=0 |
| `runtime_fraction` | float64 | No | Derived: runtime / timelimit | How much of limit used |
| `timed_out` | boolean | No | Derived: runtime >= timelimit | Hit walltime limit? |

---

### Category 4: Resource Allocation (6 columns)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `nhosts` | int32 | No | All: NNodes | Allocated nodes |
| `ncores` | int32 | No | All: NCPUS | Allocated cores |
| `memory_requested_gb` | float64 | Yes | All: ReqMem (if available) | User-requested memory |
| `account` | string | No | All: Account | Anonymized |
| `qos` | string | Yes | All: QOS | Quality of service |
| `reservation` | string | Yes | All: Reservation | Named reservation |

**Transformations**:
- Memory request units vary; normalize to GB:
  ```python
  def parse_memory_request(value):
      if value.endswith('M'):
          return float(value[:-1]) / 1024
      elif value.endswith('G'):
          return float(value[:-1])
      elif value.endswith('T'):
          return float(value[:-1]) * 1024
      else:
          return None  # Unknown format
  ```

---

### Category 5: Memory Metrics (11 columns) **[HEAVILY REVISED]**

#### 5.1 Normalized Memory Values

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `peak_memory_gb` | float64 | Yes | Metrics: MAX(memory) → GB | Normalized to GB |
| `peak_memory_fraction` | float64 | Yes | Derived: peak / node_mem | **Key cross-cluster metric** |
| `mean_memory_gb` | float64 | Yes | Metrics: MEAN(memory) → GB | If time-series available |
| `memory_efficiency` | float64 | Yes | Derived: peak / requested | If requested known |

**Transformation** (unit normalization):
```python
def normalize_memory(value, unit):
    """Convert to GB"""
    unit_multipliers = {
        'bytes': 1 / (1024**3),
        'kilobytes': 1 / (1024**2),
        'megabytes': 1 / 1024,
        'gigabytes': 1,
        'KB': 1 / (1024**2),
        'MB': 1 / 1024,
        'GB': 1
    }
    return value * unit_multipliers.get(unit, 1)
```

**Aggregation** (time-series → job-level):
```python
def aggregate_memory_timeseries(job_metrics):
    """Compute job-level memory from time-series samples"""
    if job_metrics.empty:
        return {
            'peak_memory_gb': None,
            'mean_memory_gb': None
        }
    
    # All clusters use MAX aggregation (FIND-029)
    peak = job_metrics['memory'].max()
    mean = job_metrics['memory'].mean()
    
    return {
        'peak_memory_gb': normalize_memory(peak, source_unit),
        'mean_memory_gb': normalize_memory(mean, source_unit)
    }
```

#### 5.2 Original Values (provenance)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `memory_original_value` | float64 | Yes | Metrics: memory (raw) | Exact source value |
| `memory_original_unit` | string | Yes | From clusters.json | "bytes", "KB", "GB" |

#### 5.3 Metadata (THE GAME-CHANGER)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `memory_includes_cache` | boolean | No | From clusters.json | **Critical for interpretation** |
| `memory_collection_method` | string | No | From clusters.json | "slurm_jobacct", "cgroups", "tacc_stats" |
| `memory_aggregation` | string | No | From clusters.json | "max_per_node_then_max" |
| `memory_sampling_interval_sec` | int32 | No | From clusters.json | Sampling rate |

**Population**:
```python
def add_memory_metadata(row):
    cluster = row['cluster']
    mem_config = clusters[cluster]['memory_collection']
    
    return {
        'memory_includes_cache': mem_config['includes_cache'],
        'memory_collection_method': mem_config['method'],
        'memory_aggregation': mem_config['aggregation'],
        'memory_sampling_interval_sec': mem_config['sampling_interval_sec']
    }
```

#### 5.4 Derived Flags

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `oom_killed` | boolean | No | Derived: exit_code in OOM_CODES | Out-of-memory kill |

```python
OOM_EXIT_CODES = {137, 247, 9}  # SIGKILL-related codes

def detect_oom(exit_code, state):
    if exit_code in OOM_EXIT_CODES and state == 'OUT_OF_MEMORY':
        return True
    # Additional heuristics based on cluster-specific patterns
    return False
```

**Validation**:
- `peak_memory_fraction` ∈ [0, 2] (allow >1 for overcommit, but warn if >2)
- `memory_efficiency` ∈ [0, 2] (similar reasoning)
- If `oom_killed=True`, expect `peak_memory_fraction` near 1.0

---

### Category 6: CPU Metrics (6 columns)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `cpu_time_sec` | float64 | Yes | All: CPUTime | Total CPU-seconds |
| `cpu_efficiency` | float64 | Yes | Derived: cpu_time / (runtime * ncores) | Percentage [0-100] |
| `value_cpuuser` | float64 | Yes | Metrics: CPU% (raw) | Source-specific % |
| `cpu_aggregation` | string | Yes | From clusters.json | Aggregation method |
| `idle_cores_fraction` | float64 | Yes | Derived: 1 - cpu_efficiency/100 | Waste metric |
| `cpu_throttled` | boolean | Yes | Metrics: throttle indicators | Detected throttling |

**Transformations**:
```python
def compute_cpu_efficiency(cpu_time_sec, runtime_sec, ncores):
    """Compute CPU efficiency as percentage"""
    if runtime_sec == 0 or ncores == 0:
        return None
    
    max_possible_cpu_sec = runtime_sec * ncores
    efficiency = (cpu_time_sec / max_possible_cpu_sec) * 100
    
    # Cap at 100% (accounting for minor timing variations)
    return min(efficiency, 100.0)
```

**Validation**:
- `cpu_efficiency` ∈ [0, 100]
- Warn if `cpu_efficiency` < 5% (likely idle job)
- Warn if `cpu_efficiency` > 100% (accounting error)

---

### Category 7: I/O Metrics (4 columns)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `io_read_gb` | float64 | Yes | Metrics: read bytes → GB | Total data read |
| `io_write_gb` | float64 | Yes | Metrics: write bytes → GB | Total data written |
| `value_nfs` | float64 | Yes | Metrics: NFS ops (raw) | Source-specific |
| `value_block` | float64 | Yes | Metrics: block ops (raw) | Source-specific |

**Transformations**: Unit normalization (bytes → GB, same as memory)

---

### Category 8: GPU Metrics (5 columns)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `gpu_utilization_mean` | float64 | Yes | Metrics: GPU% → mean | Average utilization [0-100] |
| `gpu_memory_used_gb` | float64 | Yes | Metrics: GPU memory → GB | Peak GPU memory |
| `gpu_memory_fraction` | float64 | Yes | Derived: gpu_mem / gpu_mem_capacity | Normalized |
| `gpu_efficiency` | float64 | Yes | Derived: gpu_util / 100 | Decimal [0-1] |
| `value_gpu` | float64 | Yes | Metrics: GPU metric (raw) | Source-specific |

**Note**: GPU data primarily from Anvil. Stampede GPU partition has limited monitoring.

---

### Category 9: Job Status (7 columns)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `exit_code` | int32 | No | All: ExitCode | Numeric exit code |
| `state` | string | No | All: State | SLURM state |
| `exit_code_category` | string | No | Derived: categorize(exit_code) | "success", "failure", "oom", "timeout" |
| `failed` | boolean | No | Derived: exit_code != 0 OR state FAILED | General failure flag |
| `node_fail` | boolean | Yes | All: NodeFail flag | Node hardware failure |
| `system_issue` | boolean | Yes | Join: outage logs (Conte only) | Correlated with downtime |
| `failure_reason` | string | Yes | Parse: error messages | Parsed failure reason |

**Transformation** (exit code categorization):
```python
def categorize_exit_code(exit_code, state, oom_killed, timed_out):
    if exit_code == 0 and state == 'COMPLETED':
        return 'success'
    elif oom_killed:
        return 'oom'
    elif timed_out:
        return 'timeout'
    elif state in {'CANCELLED', 'CANCELED'}:
        return 'cancelled'
    elif state in {'NODE_FAIL', 'FAILED'}:
        return 'node_failure' if state == 'NODE_FAIL' else 'failure'
    else:
        return 'failure'
```

---

### Category 10: User/Accounting (3 columns)

| Column | Type | Nullable | Source | Notes |
|--------|------|----------|--------|-------|
| `username_hash` | string | No | All: User (anonymized) | Anonymized username |
| `account` | string | No | All: Account (anonymized) | Allocation/project |
| `qos` | string | Yes | All: QOS | Quality of service |

**Note**: Anonymization already done in source data. Preserve as-is.

---

## Cluster-Specific Transformation Rules

### Stampede

**Source Structure**:
- Accounting: `AccountingStatistics/*.csv`
- Metrics: `TACC_Stats/NODE{1..6976}/[files]`
- Organization: Node-partitioned

**Key Transformations**:
```python
STAMPEDE_TRANSFORMS = {
    'timelimit': lambda x: int(x) * 60,  # minutes → seconds
    'memory_unit': 'bytes',
    'memory_includes_cache': True,
    'timestamp_tz': 'US/Central',
    
    # Partition → hardware mapping
    'partition_hardware': {
        'normal': {'node_memory_gb': 32, 'node_cores': 16},
        'largemem': {'node_memory_gb': 256, 'node_cores': 32},
        'gpu': {'node_memory_gb': 32, 'node_cores': 16, 'gpus': 1}
    }
}
```

**Special Logic**:
- Must reconstruct job-level metrics from node-partitioned files
- Job may span multiple NODE* directories
- Use job start/end time to filter relevant node samples

### Conte

**Source Structure**:
- Accounting: `AccountingStatistics/*.csv`
- Metrics: `TACC_Stats/YYYY-MM/[files]`
- Outages: `kickstand_2015.csv`, `Conte_outages.txt`

**Key Transformations**:
```python
CONTE_TRANSFORMS = {
    'timelimit': lambda x: int(x),  # already in seconds
    'memory_unit': 'kilobytes',
    'memory_includes_cache': False,  # RSS only
    'timestamp_tz': 'US/Eastern',
    
    'partition_hardware': {
        'shared': {'node_memory_gb': 128, 'node_cores': 16},
        'debug': {'node_memory_gb': 128, 'node_cores': 16},
        'knl': {'node_memory_gb': 96, 'node_cores': 64}
    }
}
```

**Special Logic**:
- Join with outage logs to populate `system_issue` column
- Metrics organized by month (easier than Stampede's node partitioning)

### Anvil

**Source Structure**:
- Accounting: `JobAccounting/job_accounting_MMMYYYY_anon.csv`
- Metrics: `JobResourceUsage/job_ts_metrics_MMMYYYY_anon.csv`
- Join key: JobID

**Key Transformations**:
```python
ANVIL_TRANSFORMS = {
    'timelimit': lambda x: int(x),  # already in seconds
    'memory_unit': 'gigabytes',  # already GB!
    'memory_includes_cache': True,
    'timestamp_tz': 'US/Eastern',
    'timestamp_precision': 'microseconds',
    
    'partition_hardware': {
        'gpu': {'node_memory_gb': 256, 'node_cores': 128, 'gpus': 4, 'gpu_mem': 40},
        'wide': {'node_memory_gb': 256, 'node_cores': 128, 'gpus': 0},
        'debug': {'node_memory_gb': 256, 'node_cores': 128, 'gpus': 4, 'gpu_mem': 40},
        'highmem': {'node_memory_gb': 1024, 'node_cores': 128, 'gpus': 0}
    }
}
```

**Special Logic**:
- Cleanest format: two files per month with simple join
- GPU metrics available via DCGM
- Already anonymized with purpose-built pipeline

---

## Validation Framework

### Per-Job Validation

```python
def validate_job_row(row):
    """Validation checks for a single job"""
    errors = []
    warnings = []
    
    # Required fields present
    assert row['jid'] is not None
    assert row['cluster'] in {'stampede', 'conte', 'anvil'}
    assert row['submit_time'] < row['start_time'] < row['end_time']
    
    # Hardware context populated
    assert row['node_memory_gb'] > 0
    assert row['node_cores'] > 0
    
    # Time consistency
    assert row['runtime_sec'] == (row['end_time'] - row['start_time']).total_seconds()
    assert row['queue_time_sec'] == (row['start_time'] - row['submit_time']).total_seconds()
    
    # Memory fractions in valid range
    if row['peak_memory_fraction'] is not None:
        if row['peak_memory_fraction'] > 2.0:
            warnings.append(f"High memory fraction: {row['peak_memory_fraction']}")
        assert 0 <= row['peak_memory_fraction'] <= 10  # Hard limit
    
    # CPU efficiency in valid range
    if row['cpu_efficiency'] is not None:
        if row['cpu_efficiency'] < 5:
            warnings.append(f"Very low CPU efficiency: {row['cpu_efficiency']}%")
        assert 0 <= row['cpu_efficiency'] <= 105  # Allow 5% slop
    
    return errors, warnings
```

### Cross-Cluster Validation

```python
def validate_cross_cluster(df):
    """Validate consistency across clusters"""
    
    # Memory offsets should match EXP-012 findings
    for source, target in [('conte', 'anvil'), ('anvil', 'stampede')]:
        source_data = df[df['cluster'] == source]['peak_memory_gb']
        target_data = df[df['cluster'] == target]['peak_memory_gb']
        
        ratio = target_data.mean() / source_data.mean()
        
        expected_ratios = {
            ('conte', 'anvil'): 9.1,
            ('anvil', 'stampede'): 5.7
        }
        
        expected = expected_ratios.get((source, target), None)
        if expected and abs(ratio - expected) / expected > 0.2:
            print(f"WARNING: {source}→{target} ratio {ratio:.1f} differs from expected {expected}")
    
    # Timelimit should be in seconds for all
    for cluster in df['cluster'].unique():
        cluster_data = df[df['cluster'] == cluster]
        if cluster_data['timelimit_sec'].max() < 3600:
            print(f"WARNING: {cluster} timelimits suspiciously small (max {cluster_data['timelimit_sec'].max()}s)")
    
    # Memory metadata should match clusters.json
    for cluster in df['cluster'].unique():
        cluster_data = df[df['cluster'] == cluster]
        mem_config = clusters[cluster]['memory_collection']
        
        assert (cluster_data['memory_includes_cache'] == mem_config['includes_cache']).all()
        assert (cluster_data['memory_collection_method'] == mem_config['method']).all()
```

---

## Example Row (Fully Populated)

```python
{
    # Job Identity
    'jid': '12345678',
    'jid_global': 'stampede_12345678',
    'cluster': 'stampede',
    'array_job_id': None,
    'array_task_id': None,
    'job_name': 'lammps_sim',
    
    # Hardware Context
    'node_memory_gb': 32.0,
    'node_cores': 16,
    'node_type': 'standard',
    'node_architecture': 'x86_64',
    'node_cpu_model': 'Intel Xeon E5-2680 (Sandy Bridge)',
    'gpu_count_per_node': 0,
    'gpu_memory_gb_per_device': None,
    'gpu_model': None,
    'hardware_generation': 'gen1_sandy_bridge',
    'interconnect': 'Mellanox FDR InfiniBand',
    
    # Time Fields
    'submit_time': pd.Timestamp('2015-03-15 14:30:00', tz='UTC'),
    'eligible_time': pd.Timestamp('2015-03-15 14:30:05', tz='UTC'),
    'start_time': pd.Timestamp('2015-03-15 15:45:00', tz='UTC'),
    'end_time': pd.Timestamp('2015-03-15 18:20:30', tz='UTC'),
    'timelimit_sec': 14400,  # 4 hours
    'runtime_sec': 9330,  # 2h 35m 30s
    'queue_time_sec': 4500,  # 1h 15m
    'timelimit_original': '240',
    'timelimit_unit_original': 'minutes',
    'submit_hour': 14,
    'submit_dow': 6,  # Sunday
    'runtime_fraction': 0.648,
    'timed_out': False,
    
    # Resource Allocation
    'nhosts': 4,
    'ncores': 64,
    'memory_requested_gb': 120.0,
    'account': 'proj_a1b2c3',
    'qos': 'normal',
    'reservation': None,
    
    # Memory Metrics
    'peak_memory_gb': 28.5,
    'peak_memory_fraction': 0.223,  # 28.5 / (32*4)
    'mean_memory_gb': 24.1,
    'memory_efficiency': 0.238,  # 28.5 / 120
    'memory_original_value': 30601641984,
    'memory_original_unit': 'bytes',
    'memory_includes_cache': True,
    'memory_collection_method': 'tacc_stats_custom',
    'memory_aggregation': 'max_per_node_then_max_across_nodes',
    'memory_sampling_interval_sec': 600,
    'oom_killed': False,
    
    # CPU Metrics
    'cpu_time_sec': 580800.0,  # 161.33 CPU-hours
    'cpu_efficiency': 97.2,  # Very efficient
    'value_cpuuser': 97.2,
    'cpu_aggregation': 'mean',
    'idle_cores_fraction': 0.028,
    'cpu_throttled': False,
    
    # I/O Metrics
    'io_read_gb': 145.2,
    'io_write_gb': 52.8,
    'value_nfs': 128456.0,
    'value_block': 945821.0,
    
    # GPU Metrics (N/A for this job)
    'gpu_utilization_mean': None,
    'gpu_memory_used_gb': None,
    'gpu_memory_fraction': None,
    'gpu_efficiency': None,
    'value_gpu': None,
    
    # Job Status
    'exit_code': 0,
    'state': 'COMPLETED',
    'exit_code_category': 'success',
    'failed': False,
    'node_fail': False,
    'system_issue': False,
    'failure_reason': None,
    
    # User/Accounting
    'username_hash': 'user_8a7f3b2e',
    'account': 'proj_a1b2c3',
    'qos': 'normal'
}
```

---

## Next Steps (Phase 3: Transformation Pipeline)

### Blockers for Implementation:
1. ✅ Schema designed (this document)
2. ✅ clusters.json created
3. ✅ Comparability matrix documented
4. ⏳ **NEEDED**: Inspect actual source files to confirm schemas
5. ⏳ **NEEDED**: Validate partition names match clusters.json
6. ⏳ **NEEDED**: Confirm TACC_Stats internal structure (Conte monthly, Stampede node dirs)

### Ready to Build:
- Per-cluster extraction scripts
- Normalization transforms
- Hardware context join logic
- Validation framework

### Questions for Domain Expert Review:
1. Are partition names in clusters.json correct?
2. Are hardware specs (memory, cores) accurate?
3. Confirm memory collection methodology descriptions
4. Any known issues with specific date ranges?
5. Validate GPU specifications (Anvil A100 config)
6. Confirm anonymization is consistent across clusters

---

**Status**: Phase 2 complete. Ready for expert review before proceeding to Phase 3.
