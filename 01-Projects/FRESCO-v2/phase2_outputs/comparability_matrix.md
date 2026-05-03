# FRESCO v2.0 Cross-Cluster Comparability Matrix

**Purpose**: Document which metrics can be directly compared across clusters and which require normalization or calibration.

**Version**: 2.0  
**Last Updated**: 2026-02-01  
**Based on**: EXP-011, EXP-012, EXP-013 research findings

---

## Summary

This matrix categorizes every major metric by cross-cluster comparability. Use this guide to:
- **Design analyses**: Know which metrics support cross-site studies
- **Avoid pitfalls**: Don't compare incompatible metrics directly
- **Choose normalization**: Apply correct transforms for comparability

**Color Legend**:
- ✅ **Directly comparable** - Values can be compared without transformation
- ⚠️ **Comparable with normalization** - Requires standardization but feasible
- ❌ **Not comparable** - Fundamental measurement differences prevent comparison
- 🔬 **Research-grade comparable** - Requires calibration model (EXP-013 approach)

---

## Job Identity & Provenance

| Metric | Comparable? | Notes |
|--------|-------------|-------|
| `jid` (job ID) | ✅ | Unique within cluster; use `jid_global` for cross-cluster |
| `cluster` | ✅ | Explicit identifier; foundation for all comparisons |
| `submit_time`, `start_time`, `end_time` | ✅ | Normalized to UTC microseconds in v2.0 |
| `runtime_sec` | ✅ | Walltime is standardized across SLURM; directly comparable |
| `queue_time_sec` | ✅ | Derived from timestamps; comparable |
| `job_name` | ✅ | User-provided string; meaningful within-cluster only |

**Verdict**: Time-related fields are the gold standard for cross-cluster comparison. They form the basis for workload characterization.

---

## Resource Allocations

| Metric | Comparable? | Notes |
|--------|-------------|-------|
| `nhosts` (node count) | ✅ | Integer count; directly comparable |
| `ncores` (core count) | ⚠️ | Comparable if normalized by `node_cores`<br>Anvil: 128-core nodes<br>Stampede: 16-core nodes<br>Conte: 16/64-core nodes (heterogeneous) |
| `timelimit_sec` | ✅ | **v2.0 fixes this**: Normalized to seconds (v1.0 had Stampede in minutes) |
| `memory_requested_gb` | ⚠️ | Comparable with normalization to `node_memory_gb`<br>Different node capacities: Stampede 32GB, Conte 128GB, Anvil 256GB-1TB |
| `partition` | ❌ | Cluster-specific names; not comparable<br>Use `node_type` for cross-cluster hardware categories |
| `account` | ❌ | Anonymized per-cluster; no cross-cluster meaning |

**Verdict**: Allocation counts (nodes, cores) are comparable. Resource requests need normalization to node capacity.

---

## Memory Metrics **[CRITICAL - Major v1.0 Issue]**

| Metric | Comparable? | Validation | Notes |
|--------|-------------|------------|-------|
| `peak_memory_gb` (raw) | ❌ | R² = -24 cross-site | **6-9× systematic offsets** (FIND-028)<br>Stampede: /proc/meminfo (includes cache)<br>Conte: cgroup RSS (excludes cache)<br>Anvil: cgroup usage (includes cache)<br>**NEVER compare raw values across clusters** |
| `peak_memory_fraction` | ⚠️ | Improved but weak signal | `peak_memory / node_memory`<br>Removes hardware capacity effect<br>Still contains measurement methodology differences<br>Use for exploratory analysis with caution |
| `peak_memory_gb` (calibrated) | 🔬 | R² = 0.01-0.04 after calibration | EXP-013: Affine log-space calibration rescues transfers<br>Formula: `log(mem_target) = α + β·log(mem_source)`<br>Requires target cluster data for calibration<br>Post-calibration R² low (0.01-0.04) reveals weak underlying signal |
| `memory_efficiency` | ❌ | N/A | `peak_memory / memory_requested`<br>Only valid within-cluster (if memory requests available)<br>Different user request patterns + measurement differences |
| `oom_killed` (boolean) | ✅ | N/A | Exit code-based detection; methodology-independent |

**Key Insight (EXP-012 FIND-028)**:
```
Measured offsets (geometric mean ratios):
  Anvil / Conte   = 9.1×  (Anvil measures 9x more)
  Stampede / Anvil = 5.7×  (Stampede measures 6x more)
  Stampede / Conte = 51.9× (Stampede measures 52x more)

Root cause: Cache inclusion differences
  Stampede: MemUsed from /proc/meminfo (RSS + cache + buffers)
  Conte:    RSS from cgroup memory.stat (RSS only)
  Anvil:    cgroup memory.usage_in_bytes (RSS + cache)
```

**Recommended Practice**:
1. **Never** use `peak_memory_gb` directly for cross-cluster comparison
2. Use `peak_memory_fraction` for exploratory analysis (note: still imperfect)
3. For predictive modeling: Apply EXP-013 calibration with target data
4. Document memory methodology explicitly in all cross-cluster papers
5. Consider workload differences (Anvil ML/AI vs Stampede/Conte HPC)

---

## CPU Metrics

| Metric | Comparable? | Notes |
|--------|-------------|-------|
| `cpu_time_sec` | ⚠️ | Raw CPU-seconds comparable if normalized<br>`cpu_time / (runtime * ncores)` for efficiency |
| `cpu_efficiency` | ✅ | Percentage [0-100%]; directly comparable<br>Computed consistently: `(cpu_user + cpu_system) / (walltime × cores)` |
| `value_cpuuser` (raw %) | ⚠️ | Aggregation method may differ<br>Use `cpu_efficiency` instead for cross-cluster |
| `idle_cores_fraction` | ✅ | `1 - cpu_efficiency`; directly comparable |

**Verdict**: CPU efficiency is robust for cross-cluster comparison. It's a normalized percentage independent of hardware.

---

## I/O Metrics

| Metric | Comparable? | Notes |
|--------|-------------|-------|
| `io_read_gb` | ⚠️ | Units comparable but filesystem differences matter<br>Stampede: Ranch parallel filesystem<br>Conte/Anvil: GPFS/Lustre differences<br>Workload mix (Anvil ML data loading vs traditional HPC) |
| `io_write_gb` | ⚠️ | Same as read; use with caution |
| `value_nfs` (ops) | ❌ | Filesystem-specific; not comparable |
| `value_block` (ops) | ❌ | Device-specific; not comparable |

**Verdict**: I/O bytes are weakly comparable (same units) but confounded by filesystem and workload differences.

---

## GPU Metrics

| Metric | Comparable? | Notes |
|--------|-------------|-------|
| `gpu_utilization_mean` | ⚠️ | Percentage but GPU generation matters<br>Stampede: K20 (Kepler)<br>Anvil: A100 (Ampere)<br>Different computational capabilities affect "100% busy" meaning |
| `gpu_memory_used_gb` | ⚠️ | Comparable if normalized to `gpu_memory_gb_per_device`<br>K20: 5GB vs A100: 40GB |
| `gpu_memory_fraction` | ⚠️ | Better but GPU memory architecture differs<br>HBM2 (A100) vs GDDR5 (K20) |
| `gpu_efficiency` | ⚠️ | Use with caution; GPU workload characteristics vary |

**Verdict**: Limited GPU data (mostly Anvil). Cross-generation GPU comparison is hardware-dependent.

---

## Job Status & Failures

| Metric | Comparable? | Notes |
|--------|-------------|-------|
| `exit_code` | ✅ | SLURM standard codes; directly comparable |
| `state` | ✅ | SLURM standard states; comparable |
| `failed` (boolean) | ✅ | Derived from exit_code/state; comparable |
| `timed_out` (boolean) | ✅ | `runtime >= timelimit`; directly comparable |
| `oom_killed` (boolean) | ✅ | Exit code-based; methodology-independent |
| `node_fail` (boolean) | ⚠️ | Detection method may vary by cluster<br>Conte has explicit outage logs; others inferred |

**Verdict**: Failure modes are well-standardized by SLURM. Highly comparable.

---

## Hardware Context **[NEW in v2.0]**

| Metric | Comparable? | Notes |
|--------|-------------|-------|
| `node_memory_gb` | ❌ | Descriptive, not comparable<br>Documents hardware capacity (32GB → 256GB → 1TB) |
| `node_cores` | ❌ | Descriptive (16 → 64 → 128 cores)<br>Use for normalization, not comparison |
| `node_type` | ⚠️ | Categorical; enables stratified analysis<br>"standard", "largemem", "gpu" comparable concepts |
| `hardware_generation` | ❌ | Cluster-specific IDs<br>Links to `clusters.json` for detailed specs |
| `gpu_model` | ❌ | Descriptive (K20 vs V100 vs A100)<br>Too heterogeneous for direct comparison |

**Verdict**: Hardware context fields enable **normalization**, not direct comparison. They're the denominators for efficiency calculations.

---

## Derived Efficiency Metrics **[Recommended for Cross-Cluster Studies]**

| Metric | Formula | Comparability | Notes |
|--------|---------|---------------|-------|
| `cpu_efficiency` | `cpu_time / (runtime * ncores)` | ✅ Excellent | Hardware-independent percentage |
| `runtime_fraction` | `runtime / timelimit` | ✅ Excellent | Scheduler behavior + user estimation |
| `peak_memory_fraction` | `peak_memory / node_memory` | ⚠️ Moderate | Removes capacity effect but measurement differences remain |
| `gpu_memory_fraction` | `gpu_mem_used / gpu_mem_capacity` | ⚠️ Moderate | GPU architecture differences |
| `cores_per_job` | `ncores` | ⚠️ Weak | Workload parallelism differs by field (ML vs traditional HPC) |
| `nodes_per_job` | `nhosts` | ⚠️ Weak | Scale patterns differ by cluster policy |

**Key Insight**: Efficiency metrics (ratios) are more comparable than absolute values. Always prefer normalized metrics for cross-cluster work.

---

## Comparability Decision Tree

```
START: Want to compare metric X across clusters?
│
├─ Is it a SLURM-standard field (exit_code, state, runtime)?
│  └─ YES → ✅ Directly comparable
│
├─ Is it a memory metric?
│  ├─ Raw GB? → ❌ NOT comparable (6-9× offsets)
│  ├─ Normalized fraction? → ⚠️ Use with caution (measurement differences persist)
│  └─ Need prediction? → 🔬 Apply EXP-013 calibration
│
├─ Is it hardware-specific (cores, memory, GPUs)?
│  ├─ Absolute count? → ⚠️ Normalize to capacity first
│  └─ Efficiency (ratio)? → ✅ Comparable if denominator is standardized
│
├─ Is it filesystem/network-related?
│  └─ ⚠️ Weakly comparable; document differences
│
└─ Is it cluster-specific (partition, account)?
   └─ ❌ NOT comparable
```

---

## Validation Evidence

### EXP-011: Baseline Cross-Cluster Memory Prediction
**Finding FIND-027**: Raw memory values yield catastrophic failure
- Stampede → Anvil: R² = -24.3
- All cross-site transfers: Negative R²
- **Conclusion**: Memory metrics not standardized

### EXP-012: Root Cause Analysis
**Finding FIND-028**: 6-9× systematic offsets between clusters
```
Log-scale offsets:
  Conte → Anvil:    +2.21 (9.1× multiplier)
  Anvil → Stampede: -1.74 (5.7× divider)
```
**Finding FIND-029**: Aggregation is consistent (max-per-node)
- All clusters use same aggregation logic
- Problem is measurement methodology, not aggregation

### EXP-013: Calibration Rescue
**Finding FIND-030**: Affine log-space calibration eliminates systematic bias
```python
log(mem_target) = α + β * log(mem_source)
```
- Rescues transfers: ΔR² up to +24.4
- Post-calibration R² still low (0.01-0.04)
- **Interpretation**: Can remove systematic bias but weak underlying signal

---

## Recommendations for Cross-Cluster Research

### DO:
1. ✅ Use `cpu_efficiency`, `runtime_sec`, `exit_code`, `timed_out` directly
2. ✅ Normalize allocations to node capacity (`ncores / node_cores`)
3. ✅ Apply EXP-013 calibration for memory prediction tasks
4. ✅ Stratify analyses by `node_type` or `hardware_generation`
5. ✅ Document all normalization transforms explicitly
6. ✅ Validate assumptions with pilot analysis (e.g., check distribution shapes)

### DON'T:
1. ❌ Compare raw `peak_memory_gb` across clusters (6-9× offsets)
2. ❌ Assume partition names mean the same thing across clusters
3. ❌ Ignore workload differences (Anvil ML vs Stampede HPC)
4. ❌ Treat `peak_memory_fraction` as perfectly comparable (it's improved, not perfect)
5. ❌ Use cross-cluster memory models without calibration
6. ❌ Forget to cite EXP-011/012/013 when discussing memory comparability

### CAUTION:
1. ⚠️ `peak_memory_fraction`: Use for exploratory analysis, not predictive modeling
2. ⚠️ GPU metrics: Limited to Anvil; cross-generation comparison is hardware-dependent
3. ⚠️ I/O metrics: Filesystem and workload confounds
4. ⚠️ Array jobs: May have different representation across clusters

---

## v2.0 Schema Design Impact

### Problem in v1.0:
- No explicit `cluster` column (inferred from filename)
- Missing `node_memory_gb` (couldn't compute fractions)
- Inconsistent units (`timelimit` in minutes vs seconds)
- No memory methodology documentation

### Fixed in v2.0:
- ✅ Explicit `cluster` column
- ✅ Hardware context columns (`node_memory_gb`, `node_cores`, etc.)
- ✅ Normalized time units (`timelimit_sec` always seconds)
- ✅ Dual columns: normalized + original (e.g., `peak_memory_gb` + `peak_memory_original_value`)
- ✅ Metadata columns (`memory_includes_cache`, `memory_collection_method`)
- ✅ Companion `clusters.json` documenting methodology

### Still Requires User Awareness:
- Memory measurement differences cannot be fully eliminated (inherent to data)
- `clusters.json` MUST be consulted for cross-cluster studies
- Calibration still needed for predictive modeling
- Workload mix differences (Anvil ML vs traditional HPC) persist

---

## Quick Reference Table

| Use Case | Recommended Metrics | Comparability | Notes |
|----------|-------------------|---------------|-------|
| Workload characterization | `runtime_sec`, `nhosts`, `ncores`, `submit_time` | ✅ Excellent | Core SLURM fields |
| Failure analysis | `exit_code`, `failed`, `oom_killed`, `timed_out` | ✅ Excellent | Standardized across SLURM |
| CPU efficiency | `cpu_efficiency`, `cpu_time_sec` (normalized) | ✅ Excellent | Hardware-independent |
| Memory usage (descriptive) | `peak_memory_fraction` | ⚠️ Moderate | Use for distributions, not prediction |
| Memory prediction | Calibrated `peak_memory_gb` | 🔬 Research-grade | Apply EXP-013 method |
| Resource requests | `memory_requested_gb / node_memory_gb` | ⚠️ Moderate | Normalize to capacity |
| GPU utilization | `gpu_utilization_mean` (within Anvil) | ⚠️ Weak | Cross-generation comparison limited |
| I/O patterns | `io_read_gb`, `io_write_gb` | ⚠️ Weak | Filesystem confounds |

---

## Version History

- **v2.0** (2026-02-01): Initial comparability matrix based on EXP-011/012/013
- Future: Update as validation studies complete

---

**Citation**: When using cross-cluster comparisons in research, cite:
- This comparability matrix (FRESCO v2.0 documentation)
- EXP-011 (baseline failure)
- EXP-012 (root cause analysis)
- EXP-013 (calibration method)

**Contact**: See `Documentation/Master_Index.md` for experiment details and findings.
