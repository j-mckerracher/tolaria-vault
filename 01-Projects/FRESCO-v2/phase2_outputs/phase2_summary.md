# FRESCO v2.0 Phase 2 Completion Summary

**Date**: 2026-02-01  
**Phase**: Schema Design (Phase 2 of 5)  
**Status**: ✅ Complete - Ready for Domain Expert Review

---

## What Was Accomplished

Phase 2 focused on designing the unified schema with explicit metadata, normalization strategies, and cross-cluster comparability documentation. This phase addresses all critical issues discovered in EXP-011/012/013 research.

### Deliverables Created:

1. **`clusters.json`** (16KB)
   - Complete per-cluster metadata for Stampede, Conte, and Anvil
   - Memory collection methodology documentation
   - Hardware specifications by partition and generation
   - SLURM configuration details
   - Known collection gaps and outage periods
   - Cross-cluster validation references

2. **`comparability_matrix.md`** (14KB)
   - Comprehensive metric-by-metric comparability assessment
   - Decision tree for cross-cluster analysis
   - Validation evidence from EXP-011/012/013
   - DO/DON'T guidance for researchers
   - Quick reference table for common use cases

3. **`schema_design_complete.md`** (25KB)
   - Full 65-column schema specification with types and nullability
   - Cluster-specific transformation rules
   - Validation framework (per-job and cross-cluster checks)
   - Example fully-populated row
   - Detailed transformation functions with code
   - Blockers and next steps for Phase 3

---

## Key Design Decisions

### 1. **Dual Column Strategy** (Preserve + Normalize)

Every metric with variation gets:
- **Normalized column**: For cross-cluster analysis (e.g., `peak_memory_gb`, `timelimit_sec`)
- **Original column**: For provenance (e.g., `memory_original_value`, `timelimit_original`)
- **Metadata columns**: For interpretation (e.g., `memory_includes_cache`, `timelimit_unit_original`)

**Rationale**: Enables both cross-cluster research AND cluster-specific debugging without data loss.

### 2. **Hardware Context as First-Class Data**

Added 10 new columns documenting node characteristics:
- `node_memory_gb` - **Critical for computing memory fractions**
- `node_cores` - For CPU efficiency normalization
- `gpu_model`, `gpu_memory_gb_per_device` - For GPU workload analysis
- `hardware_generation` - Links to clusters.json for detailed specs

**Rationale**: Without node context, cannot normalize metrics. This was the #1 blocker in v1.0.

### 3. **Explicit Cluster Identifier**

- v1.0: Cluster inferred from filename suffix (`_S`, `_C`, or none)
- v2.0: Explicit `cluster` column with values {"stampede", "conte", "anvil"}

**Rationale**: Violates data independence to require filename parsing. Also error-prone.

### 4. **Memory Methodology Documentation**

Added 4 metadata columns per job:
- `memory_includes_cache` (boolean)
- `memory_collection_method` (string)
- `memory_aggregation` (string)
- `memory_sampling_interval_sec` (int)

**Rationale**: EXP-012 found 6-9× offsets due to methodology differences. Must document what each metric means.

### 5. **Time Normalization**

- All timestamps: `timestamp[us, tz=UTC]`
- All durations: seconds (int64)
- Special handling: Stampede timelimit in minutes → convert to seconds

**Rationale**: Fixes the timelimit unit inconsistency that broke v1.0 analyses.

---

## How This Fixes v1.0 Issues

| v1.0 Issue | v2.0 Solution | Column(s) Added/Changed |
|------------|---------------|-------------------------|
| **Memory prediction fails** (R²=-24) | Document methodology; provide fractions | `memory_includes_cache`, `memory_collection_method`, `peak_memory_fraction` |
| **6-9× systematic offsets** | Explicit metadata + comparability matrix | `memory_includes_cache`, `comparability_matrix.md` |
| **Missing node memory** | Add hardware context | `node_memory_gb`, `node_cores`, 8 other hardware columns |
| **Timelimit units inconsistent** | Normalize to seconds + document original | `timelimit_sec`, `timelimit_unit_original` |
| **No cluster column** | Explicit identifier | `cluster` |
| **Inferred from filename** | Self-contained data | `cluster`, `node_*` columns |

---

## Comparability Matrix Highlights

### ✅ **Excellent for Cross-Cluster**:
- Time fields: `runtime_sec`, `submit_time`, etc.
- Status: `exit_code`, `failed`, `oom_killed`, `timed_out`
- CPU: `cpu_efficiency` (percentage)
- Allocations: `nhosts`, `ncores` (with normalization)

### ⚠️ **Requires Normalization**:
- Memory: Use `peak_memory_fraction`, not raw `peak_memory_gb`
- Resource requests: Normalize to `node_memory_gb`
- GPU: Normalize to device capacity

### ❌ **Not Comparable**:
- Raw `peak_memory_gb` (6-9× offsets)
- Partition names (cluster-specific)
- Accounts (anonymized per-cluster)

### 🔬 **Research-Grade Calibration**:
- Memory prediction: Apply EXP-013 affine log-space calibration
- Requires target cluster data
- Post-calibration R² = 0.01-0.04 (weak signal but systematic bias removed)

---

## clusters.json Structure

The companion metadata file documents per-cluster:

### Core Metadata:
- Institution, location, temporal coverage
- SLURM versions and configuration
- Memory collection methodology (**the critical fix**)
- Time field formats and timezones

### Hardware Specifications:
- Per-partition specs (memory, cores, GPUs)
- Hardware generation tracking (for mid-deployment changes)
- Interconnect and architecture details

### Data Source Organization:
- File structure and organization strategy
- Join keys and relationships
- Known collection gaps

### Validation References:
- Links to EXP-011/012/013 findings
- Expected systematic offsets
- Coverage statistics

**Key Insight**: This file is as important as the data itself. It documents what cannot be inferred from the data alone.

---

## Schema Statistics

- **Total columns**: 65
- **Categories**: 10
  1. Job Identity (6)
  2. Hardware Context (10) **[NEW]**
  3. Time Fields (12)
  4. Resource Allocation (6)
  5. Memory Metrics (11) **[HEAVILY REVISED]**
  6. CPU Metrics (6)
  7. I/O Metrics (4)
  8. GPU Metrics (5)
  9. Job Status (7)
  10. User/Accounting (3)

- **New columns in v2.0**: 21
- **Required (not nullable)**: 37
- **Optional (nullable)**: 28

---

## Cluster-Specific Highlights

### Stampede (2013-2018)
- **Challenge**: Timelimit in minutes (not seconds)
- **Challenge**: Node-partitioned TACC_Stats (6,976 directories)
- **Advantage**: Longest coverage (63 months)
- **Memory**: Includes page cache (MemUsed from /proc/meminfo)
- **Unit**: Bytes

### Conte (2015-2017)
- **Unique**: Explicit outage tracking (kickstand files)
- **Unique**: Temporal overlap with Stampede (cross-validation)
- **Organization**: Monthly TACC_Stats directories
- **Memory**: RSS only (cgroup memory.stat)
- **Unit**: Kilobytes
- **Heterogeneous**: CPU nodes (16-core) + KNL nodes (64-core)

### Anvil (2022-2023)
- **Cleanest**: Two-file monthly format (accounting + time-series)
- **Modern**: GPU monitoring via DCGM
- **Workload**: Heavy ML/AI (TensorFlow, PyTorch)
- **Memory**: Includes page cache (cgroup memory.usage_in_bytes)
- **Unit**: Gigabytes (already normalized!)
- **Precision**: Microsecond timestamps (others are seconds)

---

## Validation Framework

### Three-Tier Validation:

1. **Per-Job Validation**:
   - Required fields present
   - Values in valid ranges
   - Time sequence consistency
   - Hardware context populated
   - Fractions in [0, 2] range

2. **Cross-Cluster Validation**:
   - Memory offsets match EXP-012 findings (6-9×)
   - Timelimit in seconds for all clusters
   - Metadata matches clusters.json
   - Distribution shapes reasonable

3. **Scientific Validation** (Phase 4):
   - Re-run EXP-011 memory prediction (should improve)
   - Check `peak_memory_fraction` distributions are similar
   - Verify calibration (EXP-013) still works
   - Spot-check known jobs against source

---

## Questions for Domain Expert Review

Before proceeding to Phase 3 (implementation), need to validate:

### Hardware Specifications:
1. ✅ Are partition names correct for each cluster?
2. ✅ Are node memory sizes accurate?
3. ✅ Are core counts per node correct?
4. ✅ GPU specifications (Anvil A100 40GB, Stampede K20 5GB)?
5. ⚠️ Any mid-deployment hardware changes not captured?

### Memory Collection:
6. ✅ Memory methodology descriptions accurate?
7. ⚠️ Confirm Stampede includes page cache
8. ⚠️ Confirm Conte uses RSS only
9. ⚠️ Confirm Anvil uses cgroup memory.usage_in_bytes
10. ⚠️ Sampling intervals correct (Stampede 600s, Conte 300s, Anvil 300s)?

### Source Data:
11. ⚠️ Confirm partition names in actual source files
12. ⚠️ Validate TACC_Stats internal structure (need samples)
13. ⚠️ Any known date ranges with bad data?
14. ⚠️ Confirm anonymization is consistent

### Coverage:
15. ✅ Known outage periods documented correctly?
16. ⚠️ Any additional collection gaps?

**Legend**:
- ✅ High confidence (from documentation)
- ⚠️ Needs verification (from actual source inspection or domain expert)

---

## Blockers for Phase 3 (Transformation Pipeline)

### Must Have Before Implementation:

1. **Source Schema Verification**:
   - Inspect sample files from each cluster
   - Confirm column names and types
   - Validate partition values

2. **TACC_Stats Structure**:
   - Understand Conte monthly directory contents
   - Understand Stampede node directory contents
   - Document join logic for multi-node jobs

3. **Domain Expert Sign-Off**:
   - Hardware specifications validated
   - Memory methodology confirmed
   - Known issues/gaps complete

### Nice to Have:

4. **Sample Data**:
   - 1000 jobs from each cluster/period
   - Known "interesting" jobs (failures, edge cases)
   - Ground truth for validation

5. **Institutional Contact**:
   - TACC: Stampede monitoring details
   - RCAC: Conte outage correlation
   - RCAC: Anvil anonymization process

---

## Phase 3 Preview: Transformation Pipeline

Once blockers are cleared, Phase 3 will build:

### Per-Cluster Extractors:
```
stampede_extractor.py   # Handle node-partitioned TACC_Stats
conte_extractor.py      # Handle monthly dirs + outage join
anvil_extractor.py      # Handle two-file join (simplest)
```

### Normalization Transforms:
```
normalize_memory.py     # Unit conversion + metadata population
normalize_time.py       # Timezone + unit conversion
normalize_hardware.py   # Join with clusters.json
```

### Validation Suite:
```
validate_schema.py      # Per-job checks
validate_consistency.py # Cross-cluster checks
validate_science.py     # Re-run EXP-011/012 validation
```

### Output:
```
fresco_v2/
├── parquet/
│   ├── YYYY/MM/DD/HH_cluster.parquet   # Hourly shards
│   └── ...
├── clusters.json                        # Metadata
├── comparability_matrix.md              # Documentation
└── validation_report.md                 # QC results
```

---

## Estimated Complexity

### Phase 3 (Transformation Pipeline):
- **Stampede**: High complexity (node-partitioned reconstruction)
- **Conte**: Medium complexity (monthly + outage join)
- **Anvil**: Low complexity (clean two-file format)

### Phase 4 (Validation):
- **Unit tests**: ~2-3 days
- **Integration tests**: ~1 day
- **Scientific validation** (re-run experiments): ~2-3 days

### Phase 5 (Production Run):
- **Pilot** (one month): ~1 day
- **Full production** (all data): ~1 week (parallelizable)
- **Final QC**: ~2-3 days

**Total Estimate**: 3-4 weeks from Phase 3 start to production release (assuming no major surprises)

---

## Success Criteria

Phase 2 is successful if:

1. ✅ Schema addresses all v1.0 issues (memory, timelimit, hardware context)
2. ✅ Comparability matrix documents what can/cannot be compared
3. ✅ clusters.json provides complete methodology documentation
4. ✅ Transformation rules defined for each cluster
5. ✅ Validation framework designed
6. ✅ Domain expert review questions prepared
7. ⏳ Blockers for Phase 3 identified (awaiting source inspection)

**Status**: 6 of 7 criteria met. Awaiting source data inspection and domain expert feedback.

---

## Files Delivered

All Phase 2 outputs are in: `C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\FRESCO-v2\phase2_outputs\`

1. **`clusters.json`** (16KB)
   - Queryable metadata for all three clusters
   - Hardware specs, methodology, SLURM config
   - Cross-cluster notes and validation references

2. **`comparability_matrix.md`** (14KB)
   - Metric-by-metric comparability assessment
   - Decision tree and quick reference
   - DO/DON'T guidance based on EXP-011/012/013

3. **`schema_design_complete.md`** (25KB)
   - Full 65-column specification
   - Transformation rules per cluster
   - Validation framework
   - Example row and next steps

4. **`phase2_summary.md`** (this document, 10KB)
   - Phase completion summary
   - Key decisions and rationale
   - Blockers and questions for expert review

**Total Documentation**: ~65KB, comprehensively designed dataset v2.0

---

## Next Action

**For User/Dataset Creator**:

1. **Review Phase 2 outputs** (especially clusters.json hardware specs)
2. **Answer domain expert questions** (see "Questions for Domain Expert Review" section)
3. **Inspect source files** to confirm schemas match expectations
4. **Provide samples** of TACC_Stats internal structure (Conte monthly, Stampede node dirs)
5. **Approve schema design** or request revisions

**Then Proceed to Phase 3**: Build transformation pipeline with validated schema and source understanding.

---

**Phase 2 Status**: ✅ **COMPLETE** - Awaiting domain expert review and source inspection before Phase 3 implementation.
