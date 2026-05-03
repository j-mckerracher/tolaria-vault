# FRESCO v2.0 Rebuild Package: Index

**Created**: 2026-02-01  
**Purpose**: Complete handoff package for rebuilding FRESCO dataset from raw sources  
**Context**: Follows memory prediction research (EXP-011/012/013) that revealed critical v1.0 issues

---

## 📦 **Package Contents**

### 1. Agent Briefing (START HERE)
**File**: `FRESCO_v2_Agent_Prompt.md` (26KB)  
**Purpose**: Complete briefing for the next LLM agent  
**Contains**:
- Executive summary (what FRESCO is, why rebuild)
- 6 critical v1.0 issues discovered through research
- Source data structure (3 clusters × different formats)
- Target v2.0 schema (65 columns, 9 categories)
- Task definition and success criteria
- First actions and questions to ask user

**Read this first** if you're the planning agent.

---

### 2. Quick Start Guide
**File**: `FRESCO_v2_Quick_Start.md` (12KB)  
**Purpose**: Step-by-step instructions for agent onboarding  
**Contains**:
- How to use this package (reading order)
- First actions (copy docs, sample data)
- Phase breakdown template
- Validation checklist
- Questions template for user
- Success metrics

**Use this** to orient yourself and get started quickly.

---

### 3. Complete Schema Specification
**File**: `FRESCO_v2_Complete_Schema.md` (17KB)  
**Purpose**: Authoritative v2.0 schema definition  
**Contains**:
- 65 columns organized into 9 categories
- Original data location documentation
- Type specifications and nullability
- Rationale for each column
- Validation constraints
- Example rows
- Migration guide from v1.0
- Game-changer columns highlighted

**Reference this** when mapping source → target schema.

---

### 4. Dataset Design Guide
**File**: `FRESCO_Dataset_Agent_Design_Guide.md` (15KB)  
**Purpose**: Critical questions and design factors  
**Contains**:
- **Part 0**: Source data structure (Anvil/Conte/Stampede organization)
- **Part 1**: 25 blocking questions (memory, time, hardware, job identity, failures, provenance)
- **Part 2**: Critical design factors (normalization vs preservation tradeoff, etc.)
- **Part 3**: Information needed (source samples, institutional knowledge, validation data)
- **Part 4**: Lessons from downstream research (what broke, what worked)
- **Part 5**: Recommended 5-phase design process
- **Part 6**: Red flags to watch for
- **Part 7**: Minimum viable metadata checklist

**Use this** to identify blocking questions and design decisions.

---

### 5. Source Data Map
**File**: `FRESCO_Source_Data_Map.md` (14KB)  
**Purpose**: Navigate original repository structure  
**Contains**:
- Repository structure (3 clusters)
- Cluster profiles with expected schemas
- Recommended 6-phase exploration workflow
- Data quality validation checks (with code)
- Common pitfalls from v1.0 and fixes
- Questions for dataset creator
- Next steps roadmap

**Use this** to understand source data organization before sampling.

---

### 6. Supporting Research Context

#### Findings Log
**File**: `Findings_Log.md`  
**Relevant**: FIND-025 through FIND-031 (memory-related discoveries)  
- FIND-025: Excellent memory coverage (99.9%)
- FIND-026: Catastrophic cross-site failures (R² = -24)
- FIND-027: Non-standardization as root cause
- FIND-028: Systematic 6-9× offsets between clusters
- FIND-029: Aggregation consistency (max-per-node across all)
- FIND-030: Calibration rescues transfers (ΔR² up to +24.4)
- FIND-031: Weak underlying signal revealed (post-calib R² 0.01-0.04)

#### Experiment Reports
**Location**: `Experiments/EXP-011_*/`, `EXP-012_*/`, `EXP-013_*/`  
**Purpose**: Detailed methodology and results that motivated v2.0

- **EXP-011**: Memory transfer baseline + missingness
  - Established catastrophic failure (all cross-site R² < 0)
  - Verified coverage excellent (not a data availability issue)
  
- **EXP-012**: Memory label validation
  - Diagnosed 6-9× systematic offsets
  - Ruled out units and aggregation as causes
  - Identified measurement methodology differences
  
- **EXP-013**: Memory recalibration
  - Proved calibration rescues all transfers
  - Revealed weak underlying signal (R² 0.01-0.04)
  - Demonstrated need for standardized metrics

---

## 🎯 **The Problem (Summary)**

### What We Discovered
Through three experiments, we found that FRESCO v1.0 has **catastrophic cross-site memory prediction failures**:
- All cross-site transfers have **negative R²** (worst: -24.3)
- Root cause: **6-9× systematic offsets** between clusters
- Why: Undocumented differences in memory measurement methodology

### What This Means
Current FRESCO v1.0 is **scientifically unsuitable** for:
- Cross-site memory prediction
- Memory efficiency comparisons across institutions
- Transfer learning from historical data to new clusters
- Any analysis assuming memory metrics are comparable

### What v2.0 Fixes
1. **Explicit metadata**: Documents collection methodology per cluster
2. **Normalized metrics**: `peak_memory_fraction` is cross-site comparable
3. **Hardware context**: `node_memory_gb` enables proper normalization
4. **Provenance**: `cluster` column, original values preserved
5. **Consistent units**: All temporal values in seconds
6. **Companion metadata**: `clusters.json` documents what data can't

---

## 🗺️ **Source Data Overview**

### Location
`/depot/sbagchi/www/fresco/repository/`

### Three Clusters, Three Formats

#### Anvil (2022-2023): Modern
- **Files**: Monthly CSV pairs (JobAccounting + JobResourceUsage)
- **Era**: SLURM v21+, GPU-centric, clean format
- **Challenge**: Join accounting to time-series

#### Conte (2015-2017): Hybrid
- **Files**: SLURM accounting + TACC_Stats monthly subdirs + outage logs
- **Era**: Mid-generation, transitional monitoring
- **Unique**: Downtime tracking (kickstand.csv)
- **Challenge**: Hybrid format combination

#### Stampede (2013-2018): Legacy
- **Files**: SLURM accounting + TACC_Stats in 6,976 node directories
- **Era**: Legacy (SLURM v2.6-v17), longest coverage (63 months)
- **Challenge**: Reconstruct job metrics from node-partitioned data

### Current Combined (v1.0)
- **Location**: `/depot/sbagchi/data/josh/FRESCO/chunks/`
- **Format**: Hourly Parquet shards (`YYYY/MM/DD/HH[_TOKEN].parquet`)
- **Schema**: 22 columns (timestamps, job attrs, 6 metrics)
- **Issues**: See "The Problem" above

---

## 📋 **Your Task (If You're the Planning Agent)**

### Goal
Create a comprehensive **implementation plan** (not code) for rebuilding FRESCO v2.0 from raw sources.

### Deliverables
1. **Phase breakdown** (exploration → pilot → production → release)
2. **Blocking questions** (which require user input?)
3. **Technical approach** (per-cluster ingestion + transformation logic)
4. **Data flow architecture** (pipeline structure, parallelization)
5. **Hardware metadata strategy** (building clusters.json)
6. **Validation plan** (unit/integration/scientific tests)
7. **Pilot scope** (one-month test with success criteria)
8. **Rollout strategy** (order, monitoring, failure handling)
9. **Documentation requirements** (provenance, reproducibility)
10. **Risk assessment** (what could go wrong, mitigations)

### Constraints
- **Plan only** (do NOT implement code)
- **Question first** (don't make up answers to the 25 blocking questions)
- **Pilot-first** (test on small subset before production)
- **Validate obsessively** (30-40% of effort on validation)

### Success Criteria
- Addresses all 6 critical v1.0 issues
- Includes validation at every phase
- Cluster-specific logic (embrace heterogeneity)
- Metadata creation plan (clusters.json)
- Risk-aware (identifies failure modes)
- Actionable (another engineer could follow it)

---

## 🚀 **Getting Started (Next Agent)**

### Step 1: Read (2-3 hours)
1. `FRESCO_v2_Agent_Prompt.md` (main briefing)
2. `FRESCO_v2_Complete_Schema.md` (target schema)
3. `FRESCO_Dataset_Agent_Design_Guide.md` (Part 1: questions, Part 4: lessons)
4. `FRESCO_Source_Data_Map.md` (cluster profiles)

### Step 2: Sample (1 hour)
```bash
ssh jmckerra@gilbreth.rcac.purdue.edu

# Copy official docs
scp /depot/sbagchi/www/fresco/repository/FRESCO_Repository_Description.pdf ~/

# Sample each cluster
head -2 /depot/sbagchi/www/fresco/repository/Anvil/JobAccounting/job_accounting_jun2022_anon.csv
ls /depot/sbagchi/www/fresco/repository/Conte/TACC_Stats/2015-03/
ls /depot/sbagchi/www/fresco/repository/Stampede/TACC_Stats/NODE1/
```

### Step 3: Question (1 hour)
- Review 25 blocking questions in Design Guide
- Mark: ✅ answerable from docs, ❓ need sampling, 🔴 need user
- Prepare 🔴 questions for dataset creator

### Step 4: Plan (1-2 days)
- Draft phases (discovery → hardware → pilot → production → release)
- For each phase: tasks, dependencies, risks, validation
- Include pilot details (month choice, success criteria)
- Document all assumptions and unknowns

### Step 5: Review (1 hour)
- Check against success criteria
- Validate plan completeness
- Present to user for feedback

---

## 📊 **Key Numbers (Context)**

### Dataset Scale
- **Jobs**: 20.9 million total
- **Months**: 75 (gaps: 2018-05 through 2022-05)
- **Clusters**: 3 (Stampede, Conte, Anvil)
- **Columns**: 22 (v1.0) → 65 (v2.0)
- **Files**: ~5,000 Parquet shards (v1.0)

### Research Results (That Motivated This)
- **Cross-site R²**: All negative (range: -24.3 to -0.7)
- **Offsets**: 6-9× between clusters
- **Calibration improvement**: +24.4 ΔR² (S→Anvil)
- **Post-calibration ceiling**: R² ~0.01-0.04
- **Coverage**: 99.9% of jobs have memory data

### v2.0 Improvements
- **New columns**: +43 (65 total)
- **New category**: Hardware Context (10 columns)
- **Game-changers**: `node_memory_gb`, `peak_memory_fraction`, `memory_includes_cache`
- **Metadata file**: `clusters.json` (cluster-level documentation)

---

## ⚠️ **Critical Warnings**

### Do NOT:
- ❌ Assume format consistency across clusters (each is unique)
- ❌ Skip validation phases (fail fast if schema mismatches)
- ❌ Make up answers to blocking questions (ask user)
- ❌ Discard original values (preserve provenance)
- ❌ Rush to production (pilot first on one month)
- ❌ Ignore era effects (10 years = SLURM v2.6 to v21+)
- ❌ Forget metadata (clusters.json is as important as data)

### Do:
- ✅ Read all documentation before planning (invest 2-3 hours)
- ✅ Sample actual source files (don't trust docs alone)
- ✅ Ask user for institutional knowledge (they created v1.0)
- ✅ Plan validation at every phase (30-40% effort)
- ✅ Preserve heterogeneity (cluster-specific logic is OK)
- ✅ Document irreversible decisions (aggregation, null handling)
- ✅ Test pilot first (one month before 75-month production)

---

## 🔗 **File Locations**

### This Package (Documentation/)
```
FRESCO_v2_Rebuild_Package_Index.md     ← You are here
FRESCO_v2_Agent_Prompt.md              ← Main briefing (26KB)
FRESCO_v2_Quick_Start.md               ← Getting started (12KB)
FRESCO_v2_Complete_Schema.md           ← Target schema (17KB)
FRESCO_Dataset_Agent_Design_Guide.md   ← Questions + lessons (15KB)
FRESCO_Source_Data_Map.md              ← Source structure (14KB)
Findings_Log.md                        ← 31 research findings
Master_Index.md                        ← 28 experiments
Research_Plan.md                       ← Active paths
```

### Source Data (Gilbreth)
```
/depot/sbagchi/www/fresco/repository/
├── Anvil/               ← 2022-2023 data
├── Conte/               ← 2015-2017 data
├── Stampede/            ← 2013-2018 data
└── FRESCO_Repository_Description.pdf  ← Official docs
```

### Current Dataset (v1.0)
```
/depot/sbagchi/data/josh/FRESCO/chunks/
└── YYYY/MM/DD/HH[_TOKEN].parquet
```

---

## 💼 **Handoff Checklist**

For the person/agent taking over:

- [ ] Read main briefing (`FRESCO_v2_Agent_Prompt.md`)
- [ ] Review target schema (`FRESCO_v2_Complete_Schema.md`)
- [ ] Understand 25 blocking questions (Design Guide Part 1)
- [ ] Read lessons learned (Design Guide Part 4)
- [ ] Copy official PDF documentation locally
- [ ] Sample source data from all 3 clusters
- [ ] Identify questions requiring user input
- [ ] Draft initial phase breakdown
- [ ] Present plan outline to user for feedback
- [ ] Incorporate feedback and finalize plan

---

## 🎓 **Key Lessons (From Research)**

1. **Memory metrics need normalization**: Absolute GB is meaningless without node capacity
2. **Metadata is not optional**: Undocumented methodology causes 6-9× offsets
3. **Calibration works but reveals limits**: Can remove bias but can't create signal
4. **Heterogeneity is reality**: Don't force unification where it doesn't exist
5. **Provenance matters**: Future researchers need to trace data to source
6. **Validation finds issues early**: EXP-012 caught root cause on 1% sample
7. **Pilot saves time**: One-month test validates before 75-month production

---

## 📞 **Contact / Context**

**Dataset Creator**: User (has access to raw sources, institutional knowledge)  
**Research Lead**: EXP-011/012/013 executor (documented findings)  
**Planning Agent**: TBD (you, if reading this to create plan)  
**Implementation Agent**: TBD (will execute the plan)

**Questions?** Ask the dataset creator—they know:
- TACC_Stats internal structure
- Memory collection methodology per cluster
- v1.0 combination pipeline details
- Hardware specs and mid-cluster upgrades
- Anonymization transformations applied

---

## ✅ **Ready?**

If you're the next agent:
1. Open `FRESCO_v2_Agent_Prompt.md`
2. Follow the instructions
3. Create a comprehensive implementation plan
4. Present to user for approval

**Good luck rebuilding FRESCO v2.0!** 🚀

---

**Package created**: 2026-02-01  
**Session**: FRESCO memory prediction rescue + v2.0 planning  
**Research basis**: EXP-011 (baseline), EXP-012 (diagnosis), EXP-013 (calibration)  
**Status**: Ready for planning agent handoff
