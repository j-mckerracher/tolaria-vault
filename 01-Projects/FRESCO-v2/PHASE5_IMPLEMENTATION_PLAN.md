# Phase 5: Conte & Stampede Extractor Implementation Plan

**Date**: 2026-02-02  
**Goal**: Implement extractors for Conte and Stampede to complete multi-cluster v2.0 dataset

---

## Source Data Analysis

### Conte (2015-2017, 34 months)
**Structure**:
- `AccountingStatistics/YYYY-MM.csv` - Monthly SLURM accounting data
- `TACC_Stats/YYYY-MM/mem.csv` - Memory metrics (time-series)
- `TACC_Stats/YYYY-MM/cpu.csv` - CPU metrics
- `Conte_outages.txt` - Human-readable outage log

**Key characteristics**:
- PBS/Torque-style accounting (different fields than SLURM)
- TACC_Stats metrics organized by month (not node)
- Memory values in **bytes** (MemTotal=34359734272 = 32GB)
- Need to parse outage log for `system_issue` flag
- Join: `accounting.jobID` = `mem.csv.jobID`

**Schema mapping**:
- `jobID` → `jid`
- `timestamp` → `submit_time`
- `start` → `start_time`
- `end` → `end_time`
- `Resource_List.walltime` → `timelimit` (in **seconds**, not minutes!)
- `exec_host` → Parse for nhosts
- `resources_used.mem` → Used memory (different from MemUsed!)

### Stampede (2013-2018, 63 months)
**Structure**:
- `AccountingStatistics/stampede_accounting.csv` - Single 1.1GB CSV for ALL months
- `TACC_Stats/NODE*/mem.csv` - Memory metrics partitioned by node (6,172 nodes)
- Each node directory has metrics for all jobs that ran on that node

**Key characteristics**:
- Simpler accounting schema (12 columns vs Conte's 32)
- Memory values in **KB** (MemTotal=16777216 = 16GB in KB)
- `walltime` in **minutes** (need ×60 conversion!)
- Node-partitioned data requires **reconstruction**:
  - For job J that ran on nodes [N1, N2, N3]
  - Read `NODE1/mem.csv`, `NODE2/mem.csv`, `NODE3/mem.csv`
  - Filter each for `jobID=J`
  - Aggregate per-node metrics → job-level metric
- **Challenge**: 6,172 nodes × per-job reads = slow

**Schema mapping**:
- `jobID` → `jid`
- `submit` → `submit_time`
- `start` → `start_time`
- `end` → `end_time`
- `walltime` → `timelimit` (CRITICAL: convert minutes×60 → seconds)
- `nnodes` → `nhosts`
- `ncpus` → `ncores`

---

## Implementation Strategy

### Phase 5a: Conte Extractor (Simpler)
**Why first**: Monthly organization similar to Anvil, easier join logic

**Steps**:
1. Implement `ConteExtractor(BaseExtractor)`
2. Read accounting CSV for month
3. Read `TACC_Stats/YYYY-MM/mem.csv` for memory metrics
4. Join on `jobID`
5. Aggregate time-series → job-level (MAX for memory)
6. Parse `exec_host` for node list
7. Join hardware context from `clusters.json`
8. Apply memory normalization (bytes → GB)
9. Parse outages log, flag jobs during outages

**Estimated complexity**: Medium (2-3 days)

### Phase 5b: Stampede Extractor (Complex)
**Why second**: Node-partitioned structure requires special handling

**Steps**:
1. Implement `StampedeExtractor(BaseExtractor)`
2. Read entire `stampede_accounting.csv` (1.1GB)
3. Filter to specific month
4. **For each job**:
   - Parse `nnodes` to get node list
   - For each node: Read `TACC_Stats/NODE{i}/mem.csv`
   - Filter for `jobID`
   - Aggregate per-node metrics
5. Join hardware context
6. Apply memory normalization (KB → GB)
7. **CRITICAL**: Apply timelimit conversion (minutes × 60)

**Challenge**: Performance
- Naive approach: 6,172 nodes × O(jobs) reads = hours
- Optimization: Cache node files in memory, read once per month
- Alternative: Preprocess node files → job-indexed structure

**Estimated complexity**: High (3-4 days)

---

## Critical Design Decisions

### 1. Memory Aggregation (Multi-Node Jobs)
**Question**: For job with 4 nodes, how to aggregate memory?

**Options**:
- **MAX across nodes**: `peak_memory_gb = max(node1_mem, node2_mem, ...)`
- **SUM across nodes**: `peak_memory_gb = sum(node1_mem, node2_mem, ...)`
- **MEAN across nodes**: `peak_memory_gb = mean(node1_mem, node2_mem, ...)`

**Decision**: **MAX per node, then SUM across nodes**
- Rationale: Matches Anvil behavior (total memory used by job)
- For v1.0 compatibility
- `peak_memory_fraction = sum(node_maxes) / (node_memory_gb × nhosts)`

### 2. Stampede Performance Optimization
**Challenge**: Reading 6,172 node files per month is slow

**Proposed solution**: Monthly node file caching
```python
class StampedeExtractor:
    def extract_month(self, year, month):
        # Read all node mem.csv files for this month (once)
        node_cache = {}
        for node_dir in TACC_Stats/NODE*/:
            df = read_csv(node_dir / "mem.csv")
            # Filter to jobs in this month
            df = df[(df.timestamp >= month_start) & (df.timestamp < month_end)]
            node_cache[node_name] = df
        
        # Now process jobs
        for job in accounting_df:
            node_list = get_nodes(job)
            job_metrics = []
            for node in node_list:
                node_df = node_cache[node]
                job_df = node_df[node_df.jobID == job.jobID]
                job_metrics.append(job_df.MemUsed.max())
            
            job.peak_memory = sum(job_metrics) / 1024  # KB → MB
```

**Expected speedup**: 100× (one read per node instead of per-job)

### 3. Timelimit Unit Conversion (CRITICAL)
**Stampede only**: `walltime` column is in **minutes**

**Must apply conversion**:
```python
if cluster == "stampede":
    df["timelimit_sec"] = df["walltime"] * 60
    df["timelimit_original"] = df["walltime"]
    df["timelimit_unit_original"] = "minutes"
else:
    df["timelimit_sec"] = df["walltime"]
    df["timelimit_unit_original"] = "seconds"
```

This is THE critical fix from EXP-012 findings.

### 4. Outage Correlation (Conte Only)
**Conte has `Conte_outages.txt`**:
```
Unscheduled Outage to Conte Scratch - January 20, 2015 3:45pm - January 21, 2015 3:45pm
```

**Implementation**:
- Parse outage log → list of (start_time, end_time) intervals
- For each job: Check if `job.start_time` or `job.end_time` overlaps any outage
- Set `system_issue = True` if overlap detected

**Value**: Enables filtering jobs impacted by system issues in analysis

---

## Validation Strategy

### Pilot Month: 2015-03 (Conte + Stampede Overlap)
**Why**: Both clusters have data for this month, enables cross-validation

**Tests**:
1. **Conte pilot**: Extract 2015-03, validate schema
2. **Stampede pilot**: Extract 2015-03, validate schema
3. **Cross-cluster comparison**:
   - Compare job counts (Conte vs Stampede, should be different)
   - Measure raw memory offsets (should see 6-9× difference)
   - Compute memory fractions, verify offsets disappear
   - Check timelimit values (Stampede ×60 applied correctly?)

**Success criteria**:
- ✅ Both extractors complete without errors
- ✅ All v2.0 columns populated
- ✅ Memory fractions in [0, 2] range
- ✅ Raw memory offset ~6-9× (consistent with EXP-012)
- ✅ Timelimit in seconds for both (Stampede converted)

---

## clusters.json Updates Needed

### Conte Metadata
```json
"conte": {
  "memory_collection": {
    "method": "tacc_stats_monthly",
    "includes_cache": false,  // Verify!
    "unit": "bytes",
    "aggregation": "max_per_node",
    "sampling_interval_sec": 600,
    "notes": "TACC_Stats organized by month, RSS only (no cache)"
  },
  "partitions": {
    "standard": {
      "node_memory_gb": 32,
      "node_cores": 16,
      "node_type": "Haswell (E5-2680v3)"
    }
  }
}
```

### Stampede Metadata (Update)
```json
"stampede": {
  "memory_collection": {
    "method": "tacc_stats_node_partitioned",
    "includes_cache": true,  // Verify!
    "unit": "kilobytes",
    "aggregation": "max_per_node_sum_across_nodes",
    "sampling_interval_sec": 600,
    "notes": "TACC_Stats organized by node (6172 nodes), includes page cache"
  },
  "accounting": {
    "timelimit_unit": "minutes",  // CRITICAL
    "notes": "walltime column is in minutes, must convert ×60 to seconds"
  }
}
```

---

## File Deliverables

### Code
- `src/extractors/conte.py` - Conte extractor implementation
- `src/extractors/stampede.py` - Stampede extractor implementation
- `src/utils/outage_parser.py` - Parse Conte_outages.txt
- `scripts/run_pilot_conte.py` - Conte pilot script
- `scripts/run_pilot_stampede.py` - Stampede pilot script

### Documentation
- `PHASE5_CONTE_COMPLETE.md` - Conte extractor completion report
- `PHASE5_STAMPEDE_COMPLETE.md` - Stampede extractor completion report
- `PHASE5_CROSS_CLUSTER_VALIDATION.md` - 2015-03 comparison results

### Validation
- `phase5_conte_201503_sample.csv` - 100 sample Conte jobs
- `phase5_stampede_201503_sample.csv` - 100 sample Stampede jobs
- `phase5_cross_cluster_comparison.json` - Metrics comparison

---

## Risk Assessment

### High Risk
- **Stampede performance**: Node-partitioned reads may be too slow
  - **Mitigation**: Implement caching, test on small month first
- **Memory unit confusion**: Bytes (Conte) vs KB (Stampede) vs GB (Anvil)
  - **Mitigation**: Extensive unit tests, validate against v1.0

### Medium Risk
- **Missing metadata**: clusters.json may have wrong specs
  - **Mitigation**: Validate against actual data ranges
- **Outage parsing**: Dates may be ambiguous (12/2 vs 2/12)
  - **Mitigation**: Manual verification of parsed dates

### Low Risk
- **Schema mismatches**: Column names may differ
  - **Mitigation**: Already inspected schemas, know mappings

---

## Timeline

**Week 1**: Conte implementation + validation
- Days 1-2: Implement ConteExtractor
- Day 3: Test on 2015-03, fix bugs
- Day 4: Validate output, cross-check v1.0

**Week 2**: Stampede implementation + validation
- Days 1-2: Implement StampedeExtractor (naive version)
- Day 3: Optimize node caching, performance test
- Day 4: Test on 2015-03, fix bugs
- Day 5: Cross-cluster validation (Conte vs Stampede)

**Week 3**: Production readiness
- Days 1-2: Full month production runs (one per cluster)
- Day 3: SLURM array job setup for parallelization
- Days 4-5: Documentation, code review, release prep

**Total**: 2-3 weeks to full v2.0 production

---

## Next Immediate Actions

1. ✅ Exploration complete (Conte + Stampede schemas understood)
2. ⏳ Update `clusters.json` with Conte metadata
3. ⏳ Implement `ConteExtractor` class
4. ⏳ Create `run_pilot_conte.py` script
5. ⏳ Test Conte on 2015-03, validate output

**Starting now**: Conte extractor implementation

---

**Document prepared by**: FRESCO v2.0 Pipeline Agent  
**Phase**: 5 (Multi-Cluster Implementation)  
**Status**: Planning complete, implementation starting
