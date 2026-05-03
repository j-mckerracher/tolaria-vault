# FRESCO v2.0 Reconstruction: Quick Start Guide

**For**: The next LLM agent tasked with planning the rebuild  
**Date**: 2026-02-01  
**Context**: Follow-up to memory prediction research (EXP-011/012/013)

---

## 🚀 **How to Use This Package**

### Step 1: Read the Main Prompt
Open: `FRESCO_v2_Agent_Prompt.md` (26KB)

This is your **complete briefing**:
- Executive summary (what and why)
- Background on FRESCO dataset
- Critical v1.0 issues discovered through research
- Source data structure (3 clusters)
- Target v2.0 schema (65 columns)
- Your task definition
- Success criteria

**Estimated reading time**: 30-40 minutes

---

### Step 2: Review Supporting Documentation

#### Essential Reading (in order):
1. **`FRESCO_v2_Complete_Schema.md`** (17KB)
   - Full column specification
   - Example rows
   - Validation rules
   - *Focus*: Understand the target schema completely

2. **`FRESCO_Dataset_Agent_Design_Guide.md`** (15KB)
   - 25 blocking questions to ask
   - Critical design factors
   - Lessons from research
   - *Focus*: Part 1 (questions) and Part 4 (lessons learned)

3. **`FRESCO_Source_Data_Map.md`** (14KB)
   - Repository structure
   - Cluster profiles
   - Exploration workflow
   - *Focus*: Sections on each cluster (Anvil/Conte/Stampede)

#### Context Reading (optional but helpful):
4. **`Findings_Log.md`**
   - FIND-025 through FIND-031: Memory-related discoveries
   - Explains the "why" behind many v2.0 design choices

5. **Experiment READMEs**:
   - `Experiments/EXP-011_Memory_transfer_baseline_missingness/README.md`
   - `Experiments/EXP-012_memory_label_validation/README.md`
   - `Experiments/EXP-013_memory_recalibration/README.md`
   - *Purpose*: See the research that motivated this rebuild

---

### Step 3: First Actions (Once You Start)

#### Action 1: Copy Official Documentation
```bash
scp jmckerra@gilbreth.rcac.purdue.edu:/depot/sbagchi/www/fresco/repository/FRESCO_Repository_Description.pdf Documentation/
```

**Why**: This 387KB PDF is the authoritative source schema. Everything else is informed speculation until you read this.

#### Action 2: Sample Source Data
```bash
# Connect to Gilbreth
ssh jmckerra@gilbreth.rcac.purdue.edu

# Explore repository
cd /depot/sbagchi/www/fresco/repository
ls -lh Anvil/JobAccounting/ | head -10
ls -lh Anvil/JobResourceUsage/ | head -10
ls Conte/TACC_Stats/
ls Stampede/TACC_Stats/ | head -20

# Sample Anvil data (modern format)
head -2 Anvil/JobAccounting/job_accounting_jun2022_anon.csv
head -2 Anvil/JobResourceUsage/job_ts_metrics_jun2022_anon.csv

# Exit
exit
```

**Why**: Must verify actual source structure matches documentation assumptions.

#### Action 3: Identify Blocking Questions
Review the 25 questions in `FRESCO_Dataset_Agent_Design_Guide.md` Part 1.

For each question:
- ✅ Can answer from documentation
- ❓ Requires sampling source data
- 🔴 Requires user (dataset creator) input

Create a list of 🔴 questions to ask the user before proceeding.

---

### Step 4: Create Your Plan

Your plan should include (at minimum):

#### Phase 0: Discovery (Days 1-3)
- [ ] Read official documentation PDF
- [ ] Sample all three cluster source formats
- [ ] Answer 25 blocking questions (or identify who can)
- [ ] Document actual schemas found
- [ ] Verify assumptions about file organization

#### Phase 1: Hardware Metadata (Days 4-5)
- [ ] Build `clusters.json` with node specs per partition
- [ ] Source information: User guides, sysadmin, vendor specs
- [ ] Validate: Cross-check with sample job allocations

#### Phase 2: Pilot - Schema Mapping (Days 6-8)
- [ ] Map source columns → v2.0 columns for each cluster
- [ ] Document all transformations (units, aggregations, etc.)
- [ ] Identify irreversible decisions (max vs mean, null handling)

#### Phase 3: Pilot - Implementation (Days 9-14)
- [ ] Implement ingestion for one month (recommend: 2015-03)
- [ ] Process Conte + Stampede (overlap period)
- [ ] Run validation suite
- [ ] Generate data quality report

#### Phase 4: Pilot - Validation (Days 15-17)
- [ ] Check: Row counts, join rates, distributions
- [ ] Validate: Normalized metrics in [0,1], timestamps ordered
- [ ] Compare: v2.0 vs v1.0 on same month
- [ ] Decision: Go/no-go for full production

#### Phase 5: Production (Weeks 4-6)
- [ ] Parallelize across all 75 months
- [ ] Monitor: Progress, error rates, resource usage
- [ ] Handle: Edge cases, failures, retries
- [ ] Validate: Per-month summary statistics

#### Phase 6: Release (Week 7)
- [ ] Final validation across full dataset
- [ ] Build data quality report
- [ ] Update user documentation
- [ ] Package reproducibility materials

**Expand each phase with sub-tasks, dependencies, and risks.**

---

### Step 5: Validate Your Plan

Before presenting to user, check:

- ✅ **Addresses all 6 critical v1.0 issues** (memory offsets, missing cluster ID, inconsistent units, no node_memory_gb, undocumented methodology, no hardware context)
- ✅ **Includes validation at every phase** (unit tests, integration tests, scientific validation)
- ✅ **Pilot-first approach** (test on small subset before full production)
- ✅ **Cluster-specific logic** (Anvil ≠ Conte ≠ Stampede)
- ✅ **Metadata creation plan** (clusters.json is as important as data)
- ✅ **Risk assessment** (what could go wrong, mitigations)
- ✅ **Blocking questions identified** (what requires user input)
- ✅ **Resource estimates** (compute time, storage, memory)
- ✅ **Reproducibility plan** (version control, provenance tracking)

---

## 🎯 **Key Priorities**

### Must-Haves (Non-Negotiable)
1. **Explicit `cluster` column** (no more implicit suffixes)
2. **`node_memory_gb` joined** (enables normalization)
3. **`timelimit_sec` normalized** (consistent units)
4. **Memory methodology documented** (`memory_includes_cache`, `memory_collection_method`)
5. **Hardware context columns** (`node_type`, `partition`, GPU specs)
6. **`clusters.json` metadata file** (documents what data can't)

### Should-Haves (High Value)
7. **Normalized metrics** (`peak_memory_fraction`, `cpu_efficiency`, `runtime_fraction`)
8. **Derived failure flags** (`oom_killed`, `timed_out`, `node_fail`)
9. **Conte outage correlation** (`system_issue` flag from kickstand data)
10. **Original value preservation** (`*_original` columns for provenance)

### Nice-to-Haves (If Time Allows)
11. **GPU metrics** (if available in TACC_Stats)
12. **Time-series aggregation variants** (mean, p95 in addition to max)
13. **Node-level failure analysis** (Stampede NODE* data deep-dive)
14. **Library usage correlation** (Conte liblist/ directory)

---

## ⚠️ **Common Pitfalls to Avoid**

### 1. Assuming Format Consistency
**Wrong**: "All clusters use the same TACC_Stats structure"  
**Right**: "Conte has monthly subdirs, Stampede has node subdirs—need cluster-specific ingestion"

### 2. Underestimating Validation Effort
**Wrong**: "We'll validate at the end"  
**Right**: "Validate after each phase—fail fast if schema mismatches"

### 3. Ignoring Era Effects
**Wrong**: "SLURM works the same across 10 years"  
**Right**: "SLURM v2.6 (2013) to v21+ (2023)—expect breaking changes"

### 4. Forgetting Metadata
**Wrong**: "Just convert the data"  
**Right**: "clusters.json is as critical as the data—plan its creation explicitly"

### 5. Premature Optimization
**Wrong**: "Design distributed pipeline from day 1"  
**Right**: "Single-month pilot first, optimize for production later"

### 6. Making Up Answers
**Wrong**: "I'll assume memory includes cache"  
**Right**: "Flag this as blocking question for dataset creator"

### 7. Discarding Provenance
**Wrong**: "Replace timelimit with normalized version"  
**Right**: "Add timelimit_sec, keep timelimit_original + unit"

---

## 📋 **Questions Template for User**

Copy this when you're ready to engage the dataset creator:

```markdown
## Blocking Questions for FRESCO v2.0 Planning

Hi! I'm planning the FRESCO v2.0 rebuild based on the research findings (EXP-011/012/013). 
I need your help with questions that only the dataset creator can answer:

### 1. Memory Methodology (CRITICAL)
For each cluster (Stampede, Conte, Anvil):
- What tool collected memory metrics? (SLURM jobacct? cgroups? custom?)
- Does "memory used" include page cache and buffers?
- What's the sampling interval?
- What aggregation was used for v1.0? (max per job? mean? final sample?)

### 2. TACC_Stats Structure
- Conte: What files are inside the monthly subdirs (e.g., 2015-03/)?
- Stampede: What files are inside node dirs (e.g., NODE1/)?
- What metrics are available beyond CPU/mem/IO?
- File formats? (CSV, binary, custom?)

### 3. Hardware Specifications
Can you provide or point me to:
- Node memory capacity per partition/cluster
- Core counts per node type
- GPU specs per partition (type, memory, count per node)
- Hardware generation labels ("Sandy Bridge", "Knights Landing", etc.)
- Any mid-cluster hardware upgrades (dates + what changed)

### 4. v1.0 Pipeline
- Can you share the code/scripts used to combine sources into Parquet chunks?
- What transformations were applied?
- Any workarounds for data issues?
- How was timelimit unit inconsistency handled?

### 5. Anonymization
- How were Job IDs transformed? (hash, offset, preserved?)
- Username anonymization method? (salt+hash?)
- Any sampling or filtering applied?

### 6. Priorities
- What analyses are most important for v2.0 to support?
- Timeline preference: Aggressive (weeks) or cautious (months)?
- Compute resource constraints?

I'll incorporate your answers into the implementation plan. Thank you!
```

---

## 📊 **Success Metrics**

Your plan is ready to execute when:

1. **User has reviewed and approved** blocking questions answers
2. **Pilot scope is defined** (specific month, success criteria)
3. **Resource requirements estimated** (compute hours, storage GB)
4. **Risk mitigation planned** (backups, checkpoints, failure handling)
5. **Validation suite designed** (unit/integration/scientific tests)
6. **Documentation plan exists** (what docs to create, when)

---

## 🔗 **Quick Reference Links**

All documentation is in:
```
C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\FRESCO-Research\Documentation\
```

**Core Planning Docs**:
- `FRESCO_v2_Agent_Prompt.md` ← Main briefing (this package)
- `FRESCO_v2_Complete_Schema.md` ← Target schema (65 columns)
- `FRESCO_Dataset_Agent_Design_Guide.md` ← 25 questions + lessons
- `FRESCO_Source_Data_Map.md` ← Repository structure

**Research Context**:
- `Master_Index.md` ← 28 experiments overview
- `Findings_Log.md` ← 31 findings (see FIND-025 to FIND-031)
- `Research_Plan.md` ← Active research paths

**Source Data**:
- Location: `/depot/sbagchi/www/fresco/repository/`
- Official docs: `FRESCO_Repository_Description.pdf` (copy locally first)
- Current v1.0: `/depot/sbagchi/data/josh/FRESCO/chunks/`

---

## 💡 **Final Tips**

1. **Read before you plan**: Invest 2-3 hours reading all documentation before drafting your plan
2. **Sample before assuming**: Look at actual source files, don't rely on documentation alone
3. **Ask before guessing**: User is dataset creator—they know what you don't
4. **Pilot before production**: One-month test can save weeks of wasted effort
5. **Document irreversible decisions**: Future researchers will thank you
6. **Validate obsessively**: Data quality is more important than speed

---

**Ready to start?** 

Read `FRESCO_v2_Agent_Prompt.md` (the main briefing), then review the three supporting guides. Sample source data on Gilbreth. Identify blocking questions. Draft your plan. Good luck! 🚀

---

**Prepared by**: Research assistant (EXP-011/012/013)  
**Date**: 2026-02-01  
**Handoff to**: Planning agent for FRESCO v2.0 rebuild
