# FRESCO Source Data Map

**Purpose**: Quick reference for working with original FRESCO repository data  
**Last Updated**: 2026-02-01  
**Location**: `/depot/sbagchi/www/fresco/repository/`

---

## Repository Structure

```
/depot/sbagchi/www/fresco/repository/
├── Anvil/                          # Purdue Anvil (2022-2023)
│   ├── JobAccounting/              # Monthly SLURM accounting CSVs
│   │   ├── README.pdf
│   │   ├── job_accounting_jun2022_anon.csv
│   │   ├── job_accounting_jul2022_anon.csv
│   │   └── ... (through jun2023)
│   └── JobResourceUsage/           # Monthly time-series metrics
│       ├── README.pdf
│       ├── job_ts_metrics_jun2022_anon.csv
│       └── ... (through jun2023)
│
├── Conte/                          # Purdue Conte (2015-2017)
│   ├── AccountingStatistics/       # SLURM accounting data
│   ├── TACC_Stats/                # Performance metrics by month
│   │   ├── 2015-03/
│   │   ├── 2015-04/
│   │   └── ... (through 2017-12)
│   ├── Conte_outages.txt          # Downtime log
│   ├── kickstand_2015.csv         # System events
│   └── liblist/                   # Library usage (purpose TBD)
│
├── Stampede/                       # TACC Stampede (2013-2018)
│   ├── AccountingStatistics/       # SLURM accounting data
│   └── TACC_Stats/                # Performance metrics by node
│       ├── NODE1/
│       ├── NODE2/
│       └── ... (through NODE6976)
│
├── version_1.0/                    # First combined release
├── FRESCO_Repository_Description.pdf  # Official schema docs (387KB)
└── index.html                      # Web directory listing
```

---

## Cluster Profiles

### Anvil (2022-2023)

**Format**: Modern two-file CSV structure  
**Time Range**: June 2022 – June 2023 (13 months)  
**Organization**: Monthly files per data type  

**Key Files**:
- `JobAccounting/*.csv`: Job-level attributes (submit/start/end times, resources, exit codes)
- `JobResourceUsage/*.csv`: Time-series metrics (CPU, memory, I/O sampled periodically)

**Characteristics**:
- **Modern SLURM**: Likely v21.08+ with improved accounting
- **GPU-centric**: Anvil is GPU cluster (A30, A100 partitions)
- **Clean format**: Purpose-built anonymization pipeline
- **Join key**: Job ID links accounting to resource usage

**Expected Schema** (verify with README.pdf):
- Accounting: `JobID`, `Submit`, `Start`, `End`, `Timelimit`, `NNodes`, `NCPUs`, `Account`, `Partition`, `QOS`, `ExitCode`, `State`
- ResourceUsage: `JobID`, `Timestamp`, `CPU_User%`, `Memory_Used_GB`, `GPU_Util%`, `IO_Read_MB`, `IO_Write_MB`

---

### Conte (2015-2017)

**Format**: Hybrid SLURM + TACC_Stats  
**Time Range**: March 2015 – December 2017 (34 months)  
**Organization**: Monthly TACC_Stats directories + accounting files  

**Key Directories**:
- `AccountingStatistics/`: SLURM sacct export (job-level)
- `TACC_Stats/YYYY-MM/`: Performance metrics organized by month
- `kickstand_2015.csv`: System downtime/event log (2.3MB)

**Characteristics**:
- **Mid-era cluster**: SLURM v14-16 era
- **TACC monitoring**: Uses TACC_Stats collection framework
- **Outage data**: Explicit downtime tracking (unique to Conte)
- **Monthly partitioning**: Metrics organized by calendar month

**Special Files**:
- `Conte_outages.txt`: Human-readable downtime descriptions
- `liblist/`: Directory containing library usage data (purpose unclear)

**Critical for Research**:
- Overlaps with Stampede (2015-2017) → enables cross-site comparison
- Outage data allows filtering jobs affected by system issues
- Middle ground between legacy (Stampede) and modern (Anvil) eras

---

### Stampede (2013-2018)

**Format**: Legacy TACC_Stats + SLURM accounting  
**Time Range**: February 2013 – April 2018 (63 months, longest coverage)  
**Organization**: Node-level TACC_Stats directories + accounting  

**Key Directories**:
- `AccountingStatistics/`: SLURM sacct export (job-level)
- `TACC_Stats/NODE*/`: Performance metrics partitioned by node (6976 nodes)

**Characteristics**:
- **Legacy era**: SLURM v2.6-v17 span
- **Massive scale**: 6976 nodes = 111,616 cores + 128 Xeon Phi accelerators
- **Node-centric data**: Metrics partitioned by hardware, not time
- **Longest timeline**: 5+ years captures workload evolution

**Data Organization Challenge**:
- Node directories (NODE1 through NODE6976) likely contain time-ordered metric files
- Reconstructing job-level metrics requires:
  1. Identify which nodes ran each job (from accounting data)
  2. Find metric files in corresponding NODE* directories
  3. Extract time ranges matching job start/end
  4. Aggregate across all nodes for multi-node jobs

**Historical Significance**:
- Flagship TACC system from Knights Landing era
- Data spans transition from traditional HPC to accelerator computing
- Overlaps with Conte (2015-2017) enables validation

---

## Combined Dataset (v1.0)

**Output Location**: `/depot/sbagchi/data/josh/FRESCO/chunks/`

**Format**: Hourly Parquet shards  
**Partitioning**: `chunks/YYYY/MM/DD/HH[_TOKEN].parquet`  
**Coverage**: 2013-02 through 2023-06 (75 months, gaps: 2018-05 through 2022-05)

**Schema**: 22 columns (timestamps, job attributes, resource metrics)

**Known Issues** (from EXP-011/012/013):
1. **Missing `cluster` column**: Token suffix (`_S`, `_C`, none) used implicitly
2. **No `node_memory_gb`**: Cannot compute normalized memory usage
3. **Timelimit units vary**: Stampede=minutes, Conte/Anvil=seconds
4. **Memory methodology undocumented**: Causes 6-9× cross-site offsets
5. **No hardware metadata**: Cannot stratify by node type or generation

---

## Critical Files to Review First

### 1. Official Documentation
```bash
/depot/sbagchi/www/fresco/repository/FRESCO_Repository_Description.pdf
```
**Action**: Copy locally and extract authoritative schema definitions for each source.

### 2. Anvil README Files
```bash
/depot/sbagchi/www/fresco/repository/Anvil/JobAccounting/README.pdf
/depot/sbagchi/www/fresco/repository/Anvil/JobResourceUsage/README.pdf
```
**Action**: Understand modern format that should guide v2.0 schema design.

### 3. Sample Data Files
```bash
# Anvil - check one accounting + one resource usage file
/depot/sbagchi/www/fresco/repository/Anvil/JobAccounting/job_accounting_jun2022_anon.csv
/depot/sbagchi/www/fresco/repository/Anvil/JobResourceUsage/job_ts_metrics_jun2022_anon.csv

# Conte - check one month of TACC_Stats
/depot/sbagchi/www/fresco/repository/Conte/TACC_Stats/2015-03/

# Stampede - check one node's data
/depot/sbagchi/www/fresco/repository/Stampede/TACC_Stats/NODE1/
```
**Action**: Inspect actual file structure, column names, data types, sampling rates.

### 4. Outage/Event Data
```bash
/depot/sbagchi/www/fresco/repository/Conte/kickstand_2015.csv
/depot/sbagchi/www/fresco/repository/Conte/Conte_outages.txt
```
**Action**: Understand how to filter jobs affected by system issues.

---

## Recommended Exploration Workflow

### Phase 1: Documentation Review (Day 1)
1. Read `FRESCO_Repository_Description.pdf` cover-to-cover
2. Review Anvil README files (newest format)
3. Document official schema for each cluster

### Phase 2: Sample Inspection (Day 2-3)
1. **Anvil**:
   - Load one accounting CSV: `pd.read_csv('job_accounting_jun2022_anon.csv', nrows=100)`
   - Load one resource CSV: `pd.read_csv('job_ts_metrics_jun2022_anon.csv', nrows=1000)`
   - Verify join key (JobID), check for missing values, measure sampling rate
   
2. **Conte**:
   - Explore one TACC_Stats month: `ls -R Conte/TACC_Stats/2015-03/`
   - Load one accounting file: `ls Conte/AccountingStatistics/ && head -100 <file>`
   - Understand time-series file organization
   
3. **Stampede**:
   - Explore one node directory: `ls -lh Stampede/TACC_Stats/NODE1/`
   - Count total files: `find Stampede/TACC_Stats/ -type f | wc -l`
   - Estimate join complexity: nodes × jobs × time ranges

### Phase 3: Schema Alignment (Day 4-5)
1. Create mapping table: source columns → v2.0 schema
2. Identify **exact** transformations needed:
   - Unit conversions (KB→GB, minutes→seconds)
   - Timestamp parsing (different formats across eras)
   - Memory metric normalization
3. Document **irreversible** decisions:
   - What gets averaged vs maxed vs summed?
   - How to handle missing time-series samples?
   - When to mark values as `NULL` vs `0`?

### Phase 4: Hardware Metadata (Day 6)
1. Build `clusters.json` with authoritative hardware specs:
   - Node memory per partition (e.g., Anvil: a30=190GB, a100-40gb=510GB)
   - Core counts per node type
   - GPU specs per partition
   - SLURM version timeline
2. Source: Cluster user guides, sysadmin consultation, vendor specs

### Phase 5: Pilot Implementation (Day 7-10)
1. Implement combination pipeline for **one month** of data (e.g., 2015-03)
2. Process all three clusters for that month
3. Validate:
   - Row counts match source
   - Join rates (accounting → metrics) are acceptable
   - Normalized metrics (e.g., `peak_memory_fraction`) are in [0, 1]
   - Cross-cluster distributions overlap reasonably

### Phase 6: Full Production (Week 3+)
1. Parallelize across months (Dask, Ray, or SLURM array jobs)
2. Monitor for edge cases (year boundaries, leap days, DST transitions)
3. Generate summary statistics per month for validation
4. Build data quality report (coverage, join rates, anomaly counts)

---

## Data Quality Checks

After combining each cluster, validate:

### 1. Completeness
```python
# Expected vs actual row counts
expected_jobs = len(accounting_data)
actual_jobs = len(combined_data['jid'].unique())
join_rate = actual_jobs / expected_jobs
assert join_rate > 0.95, f"Low join rate: {join_rate:.1%}"
```

### 2. Temporal Consistency
```python
# All timestamps in expected range
assert (df['start_time'] >= df['submit_time']).all()
assert (df['end_time'] >= df['start_time']).all()
assert (df['runtime_sec'] == (df['end_time'] - df['start_time']).dt.total_seconds()).all()
```

### 3. Resource Sanity
```python
# Memory never exceeds node capacity
assert (df['peak_memory_gb'] <= df['node_memory_gb'] * df['nhosts']).all()

# CPU efficiency in [0, 100%]
assert (df['cpu_efficiency'] >= 0).all() and (df['cpu_efficiency'] <= 100).all()

# GPU allocations valid
assert (df['gpus_allocated'] >= 0).all()
assert (df[df['partition'].str.contains('gpu')]['gpus_allocated'] > 0).all()
```

### 4. Cross-Cluster Overlap (2015-2017)
```python
# Conte and Stampede should have similar job distributions in overlap period
conte_2016 = df[(df['cluster'] == 'conte') & (df['submit_time'].dt.year == 2016)]
stamp_2016 = df[(df['cluster'] == 'stampede') & (df['submit_time'].dt.year == 2016)]

# Compare distributions (should differ but not wildly)
compare_distributions(conte_2016['runtime_sec'], stamp_2016['runtime_sec'])
compare_distributions(conte_2016['peak_memory_fraction'], stamp_2016['peak_memory_fraction'])
```

---

## Common Pitfalls (Learned from v1.0)

### 1. **Implicit Cluster Identifiers**
- v1.0 used filename suffix (`_S`, `_C`) instead of explicit `cluster` column
- **Fix**: Add `cluster` column immediately after reading source data

### 2. **Timelimit Unit Inconsistency**
- Stampede stores minutes, others store seconds
- **Fix**: Normalize to seconds during ingestion:
  ```python
  if cluster == 'stampede':
      df['timelimit_sec'] = df['timelimit'] * 60
  else:
      df['timelimit_sec'] = df['timelimit']
  ```

### 3. **Memory Methodology Not Documented**
- Led to 6-9× offsets in downstream research
- **Fix**: Add `memory_includes_cache`, `memory_collection_method` columns with explicit values

### 4. **Missing Node Memory**
- Cannot compute normalized usage without knowing node capacity
- **Fix**: Join with hardware metadata:
  ```python
  df = df.merge(node_specs[['node_type', 'node_memory_gb']], on='node_type', how='left')
  df['peak_memory_fraction'] = df['peak_memory_gb'] / df['node_memory_gb']
  ```

### 5. **Aggregation Ambiguity**
- Is `memory_used` max/mean/final sample per job?
- **Fix**: Document clearly: "MAX sampled value across all nodes and time"

---

## Questions for Dataset Creator (User)

Before proceeding with v2.0 design:

1. **Memory methodology**: Can you provide documentation on:
   - Exact SLURM configuration: `JobAcctGatherFrequency`, `JobAcctGatherType`
   - Whether page cache/buffers were included (per cluster)
   - Any known bugs or anomalies in collection

2. **Hardware metadata**: Can you provide or point to:
   - Node type specifications (cores, memory, GPU) per cluster/partition
   - SLURM version timeline per cluster
   - Maintenance/upgrade dates that might affect data

3. **Anonymization details**: What was transformed?
   - Job IDs: Hashed, offset, or preserved?
   - Usernames: Salt/hash algorithm?
   - Any sampling/filtering applied?

4. **TACC_Stats format**: Can you describe:
   - File structure inside `TACC_Stats/` directories
   - Sampling rate (5 min? 10 min?)
   - Which metrics are available (beyond CPU/mem/IO)

5. **Version 1.0 pipeline**: Can you share:
   - Code used to combine sources into Parquet chunks
   - Any known issues or workarounds applied
   - Validation tests used

---

## Next Steps

1. **Copy this document** to dataset agent's context
2. **Copy PDF documentation** locally for reference
3. **Sample data files** to verify assumptions
4. **Design combination pipeline** using FRESCO_Dataset_Agent_Design_Guide.md
5. **Validate pilot** on one month before full production
6. **Document everything** for reproducibility

---

**Key Insight**: The original three-cluster structure reveals why cross-site prediction fails—each cluster has fundamentally different collection infrastructure. v2.0 must preserve this heterogeneity explicitly while providing standardized derived metrics for comparability.
