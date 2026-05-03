# Phase 5: Multi-Cluster Implementation - Progress Update

**Date**: 2026-02-02 01:19 UTC  
**Status**: Conte extractor implemented and testing  
**Progress**: 50% complete (Conte done, Stampede next)

---

## What's Been Accomplished

### ✅ Phase 5a: Conte Extractor (IN PROGRESS)
- [x] Explored Conte source data structure
- [x] Analyzed schemas (Accounting + TACC_Stats)
- [x] Implemented `ConteExtractor` class (250 lines)
- [x] Created `run_pilot_conte.py` pilot script
- [x] Created SLURM submission script
- [x] Submitted pilot job (Job ID: 10246652)
- [ ] Validate Conte output (waiting for job)
- [ ] Compare to Anvil (cross-cluster validation)

### ⏳ Phase 5b: Stampede Extractor (NEXT)
- [ ] Design node-partitioned data aggregation
- [ ] Implement `StampedeExtractor` class
- [ ] Optimize for 6,172-node reconstruction
- [ ] Create Stampede pilot script
- [ ] Test on 2015-03
- [ ] Validate output

---

## Technical Implementation Details

### Conte Extractor Architecture

**Data flow**:
```
Accounting (2015-03.csv) → Parse PBS/Torque format
    ↓
TACC_Stats/2015-03/mem.csv → Aggregate time-series
    ↓
Join on jobID → Merge accounting + metrics
    ↓
Hardware context join (clusters.json) → Add node specs
    ↓
Transformations (memory, time) → Normalize units
    ↓
ChunkedWriter → Hourly parquet files (NO suffix)
```

**Key features**:
1. **PBS/Torque parsing**: Different from SLURM (Anvil)
   - `jobevent='E'` filter for completed jobs only
   - `exec_host` format: `"node1/0+node1/1+node2/0"`
   - `walltime` format: `"HH:MM:SS"` or `"DD-HH:MM:SS"`

2. **Memory handling**:
   - Source unit: **bytes** (MemTotal=34359734272 = 32GB)
   - Aggregation: `MAX(MemUsed)` across timestamps
   - Metadata: `includes_cache=False` (RSS only)

3. **Time parsing**:
   - Format: `"MM/DD/YYYY HH:MM:SS"` (different from Anvil!)
   - Timelimit already in seconds (no conversion needed)
   - Timezone: US/Eastern (normalize to UTC in transforms)

4. **Hardware specs**:
   - Multiple partitions: shared (128GB), debug (128GB), knl (96GB)
   - Haswell CPUs (16 cores/node) + KNL (64 cores/node)
   - No GPUs on Conte

### Comparison: Anvil vs Conte

| Aspect | Anvil | Conte |
|--------|-------|-------|
| **Format** | SLURM CSV | PBS/Torque CSV |
| **Memory unit** | GB (already normalized) | Bytes (need conversion) |
| **Timelimit unit** | Seconds | Seconds |
| **Memory cache** | Included (cgroups) | Excluded (RSS only) |
| **Organization** | Two files (acct + metrics) | Monthly TACC_Stats |
| **Node memory** | 256GB/1024GB | 128GB/96GB |
| **Time format** | ISO-like | MM/DD/YYYY HH:MM:SS |
| **Join key** | "Job Id" | "jobID" |

**Expected memory offset**: Anvil measures ~9× more than Conte due to cache inclusion (from EXP-012)

---

## Critical Fixes Applied

### 1. Unit Conversion (Memory)
Conte memory in **bytes**, need → GB:
```python
# In memory.py normalize_memory_units()
if cluster == "conte":
    df["peak_memory_gb"] = df["memory_original_value"] / (1024**3)  # bytes → GB
```

### 2. Timestamp Parsing
Different format requires custom parsing:
```python
# MM/DD/YYYY HH:MM:SS → datetime
pd.to_datetime(acc_df['timestamp'], format='%m/%d/%Y %H:%M:%S')
```

### 3. exec_host Parsing
PBS format: `"node1/0+node1/1+node2/0+node2/1"`
- Split by `+`
- Extract node names before `/`
- Deduplicate: `{node1, node2}`

### 4. Walltime Parsing
Supports multiple formats:
- `"02:30:45"` → 9045 seconds
- `"1-04:00:00"` → 100800 seconds (1 day + 4 hours)
- `"45:30"` → 2730 seconds (45 min 30 sec)

---

## Validation Plan (When Pilot Completes)

### Schema Compliance
- [ ] 13 required columns present
- [ ] `cluster='conte'` in all rows
- [ ] `jid_global='conte_jobID...'` format
- [ ] `node_memory_gb` populated (128 or 96)
- [ ] `peak_memory_fraction` computed

### Data Quality
- [ ] Job count matches accounting file
- [ ] Memory coverage >70%
- [ ] Timelimit values reasonable (no negatives)
- [ ] Timestamps in correct range (2015-03)
- [ ] No duplicate jid_global values

### Cross-Cluster Comparison (Conte vs Anvil)
```python
# Load both from chunks-v2.0
conte_df = read_parquet("2015/03/15/00.parquet", filters=[("cluster", "=", "conte")])
anvil_df = read_parquet("2022/08/15/00.parquet", filters=[("cluster", "=", "anvil")])

# Compare memory distributions
print(f"Conte peak_memory_gb: mean={conte_df.peak_memory_gb.mean():.2f}")
print(f"Anvil peak_memory_gb: mean={anvil_df.peak_memory_gb.mean():.2f}")
print(f"Raw offset: {anvil_df.peak_memory_gb.mean() / conte_df.peak_memory_gb.mean():.1f}×")

# Compare fractions (should be similar!)
print(f"Conte peak_memory_fraction: mean={conte_df.peak_memory_fraction.mean():.3f}")
print(f"Anvil peak_memory_fraction: mean={anvil_df.peak_memory_fraction.mean():.3f}")
```

**Expected**:
- Raw memory: Anvil ~9× higher (cache vs RSS)
- Fractions: Similar (0.10-0.15 range)

---

## Stampede Design Preview

### Challenge: Node-Partitioned Data
- 6,172 node directories
- Each has `mem.csv` with all jobs on that node
- Must reconstruct job-level metrics from per-node files

### Optimization Strategy
**Problem**: Naive approach is O(jobs × nodes) file reads

**Solution**: Monthly caching
```python
def extract_month(year, month):
    # 1. Read all node mem.csv files ONCE
    node_cache = {}
    for node_id in range(1, 6173):
        df = read_csv(f"TACC_Stats/NODE{node_id}/mem.csv")
        df = df[(df.timestamp >= month_start) & (df.timestamp < month_end)]
        node_cache[node_id] = df
    
    # 2. For each job, lookup in cache
    for job in accounting:
        node_list = job.exec_host  # e.g., [1, 15, 203]
        job_mem = []
        for node_id in node_list:
            node_df = node_cache[node_id][node_cache[node_id].jobID == job.jobID]
            job_mem.append(node_df.MemUsed.max())
        job.peak_memory_kb = sum(job_mem)  # Sum across nodes, KB
```

**Expected speedup**: 100-1000× (vs reading per job)

### Critical Stampede Fix: Timelimit Units
```python
# Stampede walltime is in MINUTES (not seconds!)
df["timelimit_sec"] = df["walltime"] * 60  # THE CRITICAL FIX
df["timelimit_unit_original"] = "minutes"
```

This is the root cause of the timelimit inconsistency discovered in EXP-012.

---

## Next Steps

### Immediate (Today)
1. ⏳ Wait for Conte pilot to complete (10 min)
2. ⏳ Validate Conte output
3. ⏳ Check for errors, fix if needed
4. ⏳ Sample Conte chunks, verify schema

### Short-Term (This Week)
5. ⏳ Implement Stampede extractor
6. ⏳ Test node-partitioned aggregation
7. ⏳ Run Stampede pilot (2015-03)
8. ⏳ Three-way comparison (Anvil + Conte + Stampede)

### Medium-Term (Next Week)
9. ⏳ Production scripts for all 75 months
10. ⏳ SLURM array job parallelization
11. ⏳ Re-run EXP-011 memory prediction
12. ⏳ Measure improvement (R² from -24 → positive)

---

## Files Delivered

### Code (Phase 5a)
- `src/extractors/conte.py` (12.6 KB, 250 lines)
- `scripts/run_pilot_conte.py` (6 KB)
- `scripts/slurm_pilot_conte.sh` (777 bytes)

### Documentation
- `PHASE5_IMPLEMENTATION_PLAN.md` (10.7 KB)
- This file: `PHASE5_PROGRESS_UPDATE.md`

### In Progress
- Conte pilot output (awaiting job completion)
- Conte validation report
- Stampede extractor (design phase)

---

## Risk Mitigation

### Identified Risks
1. **Memory unit confusion**: Bytes vs KB vs GB
   - **Status**: Addressed with explicit unit tracking
2. **Timestamp parsing**: Multiple formats
   - **Status**: Implemented flexible parser
3. **Stampede performance**: 6,172 node files
   - **Status**: Caching strategy designed

### Validation Checkpoints
- ✅ Anvil pilot successful (158K jobs, 780 chunks)
- ⏳ Conte pilot running (ETA: 5 min)
- ⏳ Stampede pilot (next 2-3 days)
- ⏳ Cross-cluster comparison (after all pilots)

---

## Timeline

**Original estimate**: 1 week for Phase 5  
**Actual progress**:
- Day 1 (today): Conte extractor complete, pilot running
- Day 2-3: Stampede extractor + pilot
- Day 4-5: Validation + cross-cluster analysis

**On track**: Yes ✓

---

**Document prepared by**: FRESCO v2.0 Pipeline Agent  
**Phase**: 5a (Conte) in progress  
**Next milestone**: Conte validation complete  
**Overall completion**: ~65% (Phases 1-4 done, 5a testing, 5b-8 remaining)
