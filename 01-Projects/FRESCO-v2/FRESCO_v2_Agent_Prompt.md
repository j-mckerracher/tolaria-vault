# FRESCO v2.0 Dataset Reconstruction: Agent Briefing

**Purpose**: Complete briefing for an LLM agent tasked with creating an implementation plan to rebuild the FRESCO dataset from raw institutional data.

**Your Task**: Create a comprehensive plan (do NOT implement) for combining three heterogeneous HPC clusters' raw data into a unified, research-grade dataset that fixes critical issues discovered in the v1.0 release.

---

## Executive Summary

You are being asked to plan the reconstruction of FRESCO (Failures, Reliability, and Efficiency in Supercomputing Clusters: Operational Data), a multi-institutional HPC job dataset spanning 20.9 million jobs across 75 months and three clusters.

**Why rebuild?** Extensive downstream research (EXP-011/012/013) revealed critical issues in v1.0:
- Cross-site memory prediction catastrophically fails (R² = -24)
- 6-9× systematic offsets between clusters due to undocumented methodology differences
- Missing metadata prevents normalization (no `node_memory_gb`, no `cluster` column)
- Inconsistent units (timelimit: minutes vs seconds) cause modeling failures

**Your goal**: Design a data engineering pipeline that transforms three distinct source formats into a unified schema with complete provenance, enabling cross-site analysis while preserving institutional heterogeneity.

---

## Background: The FRESCO Dataset

### What It Is
A public dataset combining job traces and performance metrics from three supercomputing clusters:
- **Purdue Anvil** (2022-2023): 13 months, GPU-centric, modern monitoring
- **Purdue Conte** (2015-2017): 34 months, mid-era, TACC_Stats monitoring
- **TACC Stampede** (2013-2018): 63 months, legacy, node-level collection

### What It Contains
For each job:
- **Accounting data**: Submit/start/end times, resource allocations, exit codes, queue info
- **Performance metrics**: CPU usage, memory, GPU utilization, I/O activity (sampled time-series)
- **Job attributes**: Allocated cores/nodes, timelimits, partitions, user accounts (anonymized)

### Current State (v1.0)
- **Location**: `/depot/sbagchi/data/josh/FRESCO/chunks/` (hourly Parquet shards)
- **Format**: `chunks/YYYY/MM/DD/HH[_TOKEN].parquet`
- **Schema**: 22 columns (timestamps, job attrs, 6 metric values)
- **Issues**: See "Critical v1.0 Issues" section below

### Access
- **Website**: https://www.frescodata.xyz
- **Raw data**: `/depot/sbagchi/www/fresco/repository/` (on Gilbreth/Purdue systems)
- **Official docs**: `FRESCO_Repository_Description.pdf` (387KB)

---

## Critical v1.0 Issues (From Research)

### Issue 1: Memory Prediction Catastrophically Fails
**Discovery**: EXP-011 found all cross-site memory transfer learning models have **negative R²**
- Worst case: Stampede → Anvil transfer R² = -24.3 (predictions worse than predicting mean)
- Even within-cluster performance is weak (Stampede R²=0.37, Conte R²=0.10, Anvil R²=-0.03)
- Coverage is excellent (99.9% of jobs have memory data), so not a missingness issue

**Root cause** (EXP-012):
- **6-9× systematic offsets** between clusters:
  - Anvil measures 9.1× more memory than Conte
  - Stampede measures 5.7× more than Anvil
  - Log-scale offsets: Conte→Anvil +2.21, Anvil→Stampede -1.74
- **Why?** Different measurement methodologies:
  - Variation in page cache/buffer inclusion (can be 2-5× difference)
  - Different collection tools (SLURM jobacct vs cgroups vs custom)
  - Workload mix differences (Anvil has AI/ML jobs with different memory patterns)

**Fix attempted** (EXP-013):
- Simple affine calibration in log space rescues all transfers (ΔR² up to +24.4)
- But post-calibration R² remains low (0.01-0.04), revealing weak underlying signal
- **Lesson**: Can eliminate systematic bias, but need standardized metrics for true comparability

### Issue 2: Missing Normalization Metadata
**Problem**: Cannot compute `peak_memory_fraction = peak_memory / node_memory` because `node_memory_gb` column doesn't exist
- This is THE critical metric for cross-site memory comparison
- Without it, cannot distinguish workload differences from measurement artifacts
- All memory values are absolute GB, which is meaningless without node capacity context

**Fix needed**: Join with hardware metadata at ingestion time

### Issue 3: Inconsistent Units
**Problem**: Timelimit stored in different units by cluster
- Stampede: **minutes** (legacy SLURM export format)
- Conte/Anvil: **seconds** (post-processed or newer SLURM)
- Causes 60× errors in models that use timelimit as a feature

**Fix needed**: Normalize to seconds at ingestion: `CASE WHEN cluster='stampede' THEN timelimit*60 ELSE timelimit END`

### Issue 4: Missing Cluster Identifier
**Problem**: v1.0 uses filename suffix (`_S`, `_C`, or none) to implicitly identify cluster
- No explicit `cluster` column in the data itself
- Requires parsing filenames to determine provenance
- Error-prone and violates data independence principles

**Fix needed**: Add `cluster` column with values {"stampede", "conte", "anvil"}

### Issue 5: Undocumented Memory Methodology
**Problem**: No metadata documenting:
- What tool collected memory metrics (SLURM jobacct? cgroups? custom?)
- What exactly is measured (RSS? RSS+cache? cgroup memory.usage_in_bytes?)
- How aggregation works (max per job? mean? final sample?)
- Sampling rate and any gaps

**Impact**: Makes the data scientifically unusable for cross-site studies without calibration
**Fix needed**: Add metadata columns:
- `memory_includes_cache` (boolean)
- `memory_collection_method` (string: "slurm_jobacct", "cgroups", "custom")
- `memory_aggregation` (string: "max_per_node", "mean", etc.)
- `memory_sampling_interval_sec` (int)

### Issue 6: No Hardware Context
**Problem**: Missing columns that describe the hardware each job ran on:
- Node memory capacity (see Issue 2)
- Node core counts (needed for CPU efficiency)
- GPU specifications (type, memory, count per node)
- Hardware generation/node type
- Partition characteristics

**Impact**: Cannot stratify analyses by hardware type, cannot compute utilization fractions
**Fix needed**: Join with cluster/partition hardware specs and add columns like `node_type`, `node_cores`, `node_memory_gb`, `gpu_type`, `gpu_memory_gb`

---

## Source Data Structure

### Repository Location
`/depot/sbagchi/www/fresco/repository/`

### Anvil (2022-2023) - Modern Format
```
Anvil/
├── JobAccounting/
│   ├── README.pdf
│   ├── job_accounting_jun2022_anon.csv
│   ├── job_accounting_jul2022_anon.csv
│   └── ... (monthly through jun2023)
└── JobResourceUsage/
    ├── README.pdf
    ├── job_ts_metrics_jun2022_anon.csv
    └── ... (monthly time-series)
```

**Format**: Two-file CSV structure
- **Accounting**: Job-level attributes (1 row per job)
- **ResourceUsage**: Time-series metrics (many rows per job, periodic sampling)
- **Join key**: JobID
- **Era**: Modern SLURM v21+ with GPU monitoring
- **Characteristics**: Clean, purpose-built anonymization, GPU-centric workloads

### Conte (2015-2017) - Hybrid Format
```
Conte/
├── AccountingStatistics/       # SLURM sacct exports
├── TACC_Stats/
│   ├── 2015-03/
│   ├── 2015-04/
│   └── ... (monthly subdirs through 2017-12)
├── Conte_outages.txt          # Human-readable downtime log
├── kickstand_2015.csv         # System events (2.3MB)
└── liblist/                   # Library usage data
```

**Format**: Hybrid SLURM + TACC_Stats
- **Accounting**: SLURM sacct-style data
- **TACC_Stats**: Performance metrics organized by month (structure TBD)
- **Unique feature**: Outage/downtime logs (enables filtering system-impacted jobs)
- **Era**: Mid-era SLURM v14-16, transitional monitoring
- **Overlap**: 2015-2017 overlaps with Stampede (enables cross-validation)

### Stampede (2013-2018) - Legacy Format
```
Stampede/
├── AccountingStatistics/       # SLURM sacct exports
└── TACC_Stats/
    ├── NODE1/
    ├── NODE2/
    └── ... (6,976 node directories through NODE6976)
```

**Format**: Legacy TACC_Stats + SLURM accounting
- **Accounting**: SLURM sacct-style data
- **TACC_Stats**: Metrics partitioned by node (6,976 nodes = 111,616 cores)
- **Challenge**: Must reconstruct job-level metrics from node-partitioned files
- **Era**: Legacy SLURM v2.6-v17, 5+ years capturing HPC evolution
- **Scale**: Longest coverage (63 months), flagship TACC system

### Official Documentation
- **Main doc**: `/depot/sbagchi/www/fresco/repository/FRESCO_Repository_Description.pdf` (387KB)
- **Anvil READMEs**: In JobAccounting/ and JobResourceUsage/ subdirs
- **CRITICAL**: Read these first to understand authoritative source schemas

---

## Target Schema: v2.0 Specification

### Design Principles
1. **Explicit provenance**: Every row declares its cluster, node type, hardware generation
2. **Normalization-ready**: Include both raw values AND normalized fractions
3. **Metadata-rich**: Document collection methodology explicitly
4. **Backwards-compatible**: Preserve original values for validation
5. **Cross-site comparable**: Derived columns use standardized denominators

### Column Categories (65 total)

#### 1. Job Identity (6 columns)
- `jid` (string): Original job ID from source cluster
- `jid_global` (string): Globally unique `{cluster}_{jid}`
- `cluster` (string): {"stampede", "conte", "anvil"}
- `array_job_id` (string, nullable): Parent array job ID
- `array_task_id` (int64, nullable): Task index
- `job_name` (string, nullable): User-provided name

#### 2. Hardware Context (10 columns) **[NEW CATEGORY]**
- `node_memory_gb` (float64): Memory capacity per node **[CRITICAL]**
- `node_cores` (int32): CPU cores per node
- `node_type` (string): Hardware model/generation
- `partition` (string): SLURM partition
- `hardware_generation` (string): Era ("sandy_bridge", "knights_landing", "milan", etc.)
- `gpu_type` (string, nullable): GPU model if applicable
- `gpu_memory_gb` (float64, nullable): GPU memory per device
- `gpus_per_node` (int32): GPUs available per node
- `gpus_allocated` (int32): GPUs requested by job
- `network_topology` (string): Interconnect type

#### 3. Time Fields (12 columns)
- `submit_time` (timestamp[ns, tz=UTC]): Job submission
- `start_time` (timestamp[ns, tz=UTC]): Execution start
- `end_time` (timestamp[ns, tz=UTC]): Completion/termination
- `timelimit_sec` (int64): Wall time limit in **seconds** (normalized)
- `runtime_sec` (int64): Actual runtime (end - start)
- `queue_time_sec` (int64): Time waiting (start - submit)
- `timelimit_original` (string): Raw value from source
- `timelimit_unit_original` (string): Unit from source ("minutes", "seconds")
- `submit_hour` (int8): Hour of day [0-23] (derived)
- `submit_dow` (int8): Day of week [0-6] (derived)
- `runtime_fraction` (float64): runtime / timelimit (derived)
- `timed_out` (boolean): Did job hit timelimit? (derived)

#### 4. Resource Allocation (6 columns)
- `nhosts` (int32): Number of nodes allocated
- `ncores` (int32): Number of CPU cores allocated
- `memory_requested_gb` (float64, nullable): Requested memory
- `account` (string): Allocation account (anonymized)
- `qos` (string): Quality of service
- `reservation` (string, nullable): Named reservation if used

#### 5. Memory Metrics (11 columns) **[HEAVILY REVISED]**
- `peak_memory_gb` (float64): Maximum memory used (normalized units)
- `peak_memory_fraction` (float64): peak_memory / (node_memory * nhosts) **[KEY METRIC]**
- `mean_memory_gb` (float64, nullable): Average if time-series available
- `memory_efficiency` (float64): peak_memory / memory_requested (if requested known)
- `memory_original_value` (float64): Raw value from source (provenance)
- `memory_original_unit` (string): Unit from source
- `memory_includes_cache` (boolean): Page cache/buffers included? **[CRITICAL]**
- `memory_collection_method` (string): "slurm_jobacct", "cgroups", "custom"
- `memory_aggregation` (string): "max_per_node", "mean", "final_sample"
- `memory_sampling_interval_sec` (int32): Time between samples
- `oom_killed` (boolean): Out-of-memory termination? (from exit code)

#### 6. CPU Metrics (6 columns)
- `cpu_time_sec` (float64): Total CPU seconds consumed
- `cpu_efficiency` (float64): cpu_time / (runtime * ncores) [0-100%]
- `value_cpuuser` (float64): Raw CPU user % from source (provenance)
- `cpu_aggregation` (string): How CPU computed ("mean", "max", etc.)
- `idle_cores_fraction` (float64): 1 - cpu_efficiency
- `cpu_throttled` (boolean): Evidence of throttling (from metrics)

#### 7. I/O Metrics (4 columns)
- `io_read_gb` (float64): Total data read
- `io_write_gb` (float64): Total data written
- `value_nfs` (float64): NFS ops from source (provenance)
- `value_block` (float64): Block I/O from source (provenance)

#### 8. GPU Metrics (5 columns)
- `gpu_utilization_mean` (float64): Average GPU utilization % [0-100]
- `gpu_memory_used_gb` (float64): GPU memory used
- `gpu_memory_fraction` (float64): GPU memory / gpu_memory_gb
- `gpu_efficiency` (float64): gpu_utilization / 100
- `value_gpu` (float64): Raw GPU metric from source (provenance)

#### 9. Job Status (7 columns)
- `exit_code` (int32): Numeric exit code
- `state` (string): Final state ("COMPLETED", "FAILED", "TIMEOUT", "CANCELLED")
- `exit_code_category` (string): Grouped ("success", "failure", "oom", "timeout")
- `failed` (boolean): Non-zero exit or failed state
- `node_fail` (boolean): Node failure caused termination
- `system_issue` (boolean): Correlated with outage log (Conte only)
- `failure_reason` (string, nullable): Parsed from error logs if available

#### 10. User/Accounting (3 columns)
- `username_hash` (string): Anonymized username
- `account` (string): Anonymized allocation/project
- `qos` (string): Quality of service level

**Total**: 65 columns (expandable)

### Companion File: clusters.json
Separate metadata file documenting cluster-level characteristics:

```json
{
  "stampede": {
    "institution": "TACC",
    "location": "University of Texas at Austin",
    "temporal_coverage": "2013-02 to 2018-04",
    "total_jobs": 8200000,
    "slurm_versions": ["2.6", "14.03", "17.02"],
    "monitoring_system": "TACC_Stats",
    "memory_collection": {
      "method": "tacc_stats_custom",
      "includes_cache": true,
      "aggregation": "max_per_node",
      "sampling_interval_sec": 600,
      "notes": "Legacy TACC_Stats framework, node-level collection"
    },
    "partitions": {
      "normal": {
        "node_memory_gb": 32,
        "node_cores": 16,
        "node_type": "Sandy Bridge (E5-2680)",
        "network": "Mellanox FDR InfiniBand"
      },
      "largemem": {
        "node_memory_gb": 256,
        "node_cores": 32,
        "node_type": "Westmere (X7560)"
      }
    },
    "hardware_changes": [
      {"date": "2013-02", "event": "Initial deployment", "nodes": 6976}
    ],
    "known_issues": [
      "Timelimit in minutes, not seconds",
      "Node-partitioned data requires reconstruction"
    ]
  },
  "conte": { /* similar structure */ },
  "anvil": { /* similar structure */ }
}
```

**Critical**: This file is as important as the data itself—it documents what cannot be inferred from the data alone.

---

## Detailed Documentation (Read These First)

Three comprehensive guides have been prepared:

### 1. FRESCO v2.0 Complete Schema Specification
**File**: `Documentation/FRESCO_v2_Complete_Schema.md` (17KB)
- Full 65-column specification with types, nullability, rationale
- Example row showing populated values
- Validation constraints (e.g., `peak_memory_fraction` ∈ [0, 1])
- Migration guide from v1.0 to v2.0
- Game-changer columns highlighted

### 2. FRESCO Dataset Agent Design Guide
**File**: `Documentation/FRESCO_Dataset_Agent_Design_Guide.md` (15KB)
- **Part 0**: Source data structure (Anvil/Conte/Stampede organization)
- **Part 1**: 25 blocking questions organized by category (memory, time, hardware, etc.)
- **Part 2**: Critical design factors (normalization vs preservation tradeoff, etc.)
- **Part 3**: Information needed (source samples, institutional knowledge, validation data)
- **Part 4**: Lessons from downstream research (what broke, what worked)
- **Part 5**: Recommended 5-phase design process
- **Part 6**: Red flags to watch for
- **Part 7**: Minimum viable metadata checklist

### 3. FRESCO Source Data Map
**File**: `Documentation/FRESCO_Source_Data_Map.md` (14KB)
- Repository structure with file listings
- Cluster profiles (Anvil/Conte/Stampede) with expected schemas
- Recommended 6-phase exploration workflow
- Data quality validation checks with code examples
- Common pitfalls from v1.0 and how to avoid them
- Questions for dataset creator
- Next steps roadmap

---

## Your Task: Create an Implementation Plan

### What You Should Produce

A comprehensive implementation plan saved to the session workspace that includes:

#### 1. Phase Breakdown
- List all phases from data exploration through production release
- Estimate complexity (not time/dates) for each phase
- Identify dependencies and blockers
- Mark parallel-safe phases

#### 2. Blocking Questions
- Review the 25 questions in the Design Guide
- Prioritize: which MUST be answered before starting?
- Suggest how to find answers (documentation, sampling, institutional contact)
- Identify questions that can be deferred

#### 3. Technical Approach
For each cluster (Anvil, Conte, Stampede):
- **Ingestion strategy**: How to read source format?
- **Schema mapping**: Source columns → v2.0 columns (include transformations)
- **Join logic**: How to combine accounting + time-series?
- **Aggregation rules**: How to compute job-level metrics from samples?
- **Edge cases**: Missing data, array jobs, job failures, etc.

#### 4. Data Flow Architecture
- Overall pipeline structure (modular? monolithic?)
- Processing granularity (per-file? per-month? per-cluster?)
- Parallelization strategy (Dask? Ray? SLURM arrays?)
- Storage intermediate results? Or stream-through?
- Checkpointing for restartability

#### 5. Hardware Metadata Strategy
- How to build `clusters.json`?
- Where to source node specs? (User guides? Sysadmin consult? Vendor docs?)
- How to handle mid-cluster upgrades? (Hardware changes over 10 years)
- Validation: Ensure partition specs match actual job allocations

#### 6. Validation Plan
- **Unit tests**: Per-cluster ingestion correctness
- **Integration tests**: Cross-cluster consistency
- **Scientific validation**: Compare v2.0 to v1.0 on key metrics
- **Smoke tests**: One-month pilot before full production
- **Data quality report**: Coverage, join rates, distribution sanity

#### 7. Pilot Scope
- Which month to pilot? (Recommend: 2015-03, includes Conte+Stampede overlap)
- Success criteria for pilot
- Validation metrics to check
- Go/no-go decision criteria

#### 8. Rollout Strategy
- Order of cluster processing (Anvil → Conte → Stampede? Or parallel?)
- Monitoring during production (progress tracking, error rates)
- Handling failures (retries, manual intervention, skip-and-log)
- Final validation before release

#### 9. Documentation Requirements
- What documentation must be created?
- Provenance tracking (commit hashes, timestamps, versions)
- User-facing documentation updates
- Reproducibility package

#### 10. Risk Assessment
- What could go wrong?
- Data loss risks and mitigations
- Computational resource needs (time, storage, memory)
- Unknowns that could derail the project

### What You Should NOT Do

- **Do NOT implement code** (plan only)
- **Do NOT make up answers** to the 25 blocking questions
- **Do NOT assume source data structure** without verification
- **Do NOT underestimate complexity** (this is a multi-week engineering effort)

### Guidance on Approach

1. **Start with questions**: Which of the 25 blocking questions can you answer from docs? Which require user input?

2. **Pilot-first mindset**: Plan to test everything on a small subset (one month) before full production

3. **Embrace heterogeneity**: Each cluster needs cluster-specific logic (don't force unification where it doesn't belong)

4. **Metadata is data**: Plan `clusters.json` creation with same rigor as main dataset

5. **Validation budget**: Allocate 30-40% of effort to validation/QC (not an afterthought)

6. **Fail-fast checks**: Build early validation that catches schema mismatches immediately

7. **Reproducibility**: Every transformation must be documented and versionable

---

## Available Resources

### On Gilbreth Cluster
- **Source data**: `/depot/sbagchi/www/fresco/repository/`
- **Output location**: `/depot/sbagchi/data/josh/FRESCO-Research/Experiments/` (for pilot)
- **Storage**: Data depot has ample space (terabytes available)
- **Compute**: GPU-only cluster, use `--gres=gpu:1` for all jobs
- **Submission**: Use `sbbest` wrapper for automatic partition selection

### Local Documentation
All documentation is in: `C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\FRESCO-Research\Documentation\`
- Schema specification: `FRESCO_v2_Complete_Schema.md`
- Design guide: `FRESCO_Dataset_Agent_Design_Guide.md`
- Source map: `FRESCO_Source_Data_Map.md`
- Research findings: `Findings_Log.md` (31 findings logged)
- Master index: `Master_Index.md` (28 experiments tracked)

### Research Context
Three experiments inform this work:
- **EXP-011**: Established baseline (catastrophic failure, R²=-24)
- **EXP-012**: Diagnosed root cause (6-9× offsets, methodology differences)
- **EXP-013**: Tested fix (calibration rescues transfers but reveals weak signal)

Full experiment reports in: `Experiments/EXP-011_Memory_transfer_baseline_missingness/`, etc.

---

## Success Criteria

Your plan is successful if:

1. **Comprehensive**: Covers all phases from exploration to production
2. **Realistic**: Acknowledges unknowns and includes contingency
3. **Actionable**: Another engineer could follow the plan
4. **Risk-aware**: Identifies failure modes and mitigations
5. **Science-driven**: Prioritizes data quality and provenance over speed
6. **Modular**: Phases can be executed independently where possible
7. **Validated**: Includes multiple checkpoints to catch errors early

---

## Starting Point: First Actions

When you begin planning:

1. **Review official documentation** (copy PDF locally):
   ```bash
   scp jmckerra@gilbreth.rcac.purdue.edu:/depot/sbagchi/www/fresco/repository/FRESCO_Repository_Description.pdf ./
   ```

2. **Read the three comprehensive guides** (Schema, Design Guide, Source Map)

3. **Inspect sample files** from each cluster:
   ```bash
   # Anvil
   head -2 /depot/sbagchi/www/fresco/repository/Anvil/JobAccounting/job_accounting_jun2022_anon.csv
   head -2 /depot/sbagchi/www/fresco/repository/Anvil/JobResourceUsage/job_ts_metrics_jun2022_anon.csv
   
   # Conte
   ls /depot/sbagchi/www/fresco/repository/Conte/TACC_Stats/2015-03/
   
   # Stampede  
   ls /depot/sbagchi/www/fresco/repository/Stampede/TACC_Stats/NODE1/
   ```

4. **Identify blocking questions** that require user input (dataset creator)

5. **Draft pilot plan** for one month (2015-03 recommended)

6. **Seek user feedback** on approach before full planning

---

## Key Mindset

You are planning a **data archaeology and reconstruction project** with scientific consequences. Every decision impacts what research will be possible with FRESCO v2.0.

**Guiding principles**:
- When in doubt, preserve more (metadata, original values, provenance)
- Explicit is better than implicit (cluster IDs, units, methodology)
- Normalize but don't discard (keep both `timelimit_sec` and `timelimit_original`)
- Document irreversible decisions (aggregation methods, null handling)
- Validate early, validate often (unit tests, smoke tests, pilot, cross-checks)

**Remember**: This dataset will be cited in research papers. The decisions you plan will shape scientific conclusions. Take the time to get it right.

---

## Questions to Ask User (Dataset Creator)

Before finalizing your plan, prepare questions for the user on:

1. **TACC_Stats structure**: What's inside monthly (Conte) and node (Stampede) directories?
2. **Memory methodology**: SLURM configs, cache inclusion, known bugs per cluster?
3. **v1.0 pipeline**: Can the original combination code be shared?
4. **Hardware specs**: Node memory/cores/GPU per partition? Mid-cluster upgrades?
5. **Anonymization**: What transformations were applied to job IDs, usernames?
6. **Priorities**: What analyses are most important? (Guides which features to prioritize)
7. **Timeline**: Aggressive (weeks) or cautious (months)?
8. **Resources**: Preferred compute environment? Storage limits? Existing tools?

---

## Final Instruction

Create a detailed, phase-by-phase implementation plan that balances ambition (a scientifically rigorous v2.0) with pragmatism (achievable with available resources). Save the plan to the session workspace and summarize the key phases, risks, and first steps.

**Do NOT begin implementation—planning only.**

Good luck! You're helping rebuild a foundational dataset for HPC systems research.

---

**Document prepared by**: Research assistant (EXP-011/012/013 executor)  
**Date**: 2026-02-01  
**Session**: FRESCO memory prediction rescue + v2.0 planning  
**Status**: Ready for handoff to planning agent
