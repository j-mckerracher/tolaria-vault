# FRESCO v2.0 Dataset Rebuild Project

**Created**: 2026-02-01  
**Purpose**: Complete documentation package for rebuilding the FRESCO dataset from raw institutional sources  
**Context**: Based on findings from memory prediction research (EXP-011/012/013) in FRESCO-Research project

---

## 🎯 **Project Goal**

Rebuild the FRESCO (Failures, Reliability, and Efficiency in Supercomputing Clusters: Operational Data) dataset from original sources to fix critical issues discovered in v1.0:

### Critical v1.0 Issues
1. **Catastrophic cross-site memory prediction failures** (R² = -24)
2. **6-9× systematic offsets** between clusters due to undocumented methodology
3. **Missing normalization metadata** (no `node_memory_gb`, no `cluster` column)
4. **Inconsistent units** (timelimit: minutes vs seconds)
5. **Undocumented memory collection methodology**
6. **No hardware context** (node specs, GPU info)

### v2.0 Goals
- **65-column schema** (vs 22 in v1.0) with explicit provenance
- **Hardware context** category (10 new columns)
- **Normalized metrics** for cross-site comparability (`peak_memory_fraction`, etc.)
- **Metadata documentation** (`clusters.json` companion file)
- **Scientific rigor** enabling reproducible cross-institutional research

---

## 📋 **Quick Start (For Next Agent)**

### If You're Planning the Rebuild:

1. **Start here**: Read `FRESCO_v2_Agent_Prompt.md` (26KB)
   - Complete briefing with task definition
   - 6 critical issues explained
   - Target schema overview
   - Success criteria

2. **Then read**: `FRESCO_v2_Quick_Start.md` (12KB)
   - Step-by-step onboarding
   - First actions checklist
   - Questions template

3. **Reference**: Other docs as needed
   - Schema: `FRESCO_v2_Complete_Schema.md`
   - Questions: `FRESCO_Dataset_Agent_Design_Guide.md`
   - Source data: `FRESCO_Source_Data_Map.md`

4. **Official docs**: `FRESCO_Repository_Description.pdf` (395KB)

### Your Task
Create a comprehensive **implementation plan** (not code) covering:
- Phase breakdown (exploration → pilot → production)
- Technical approach per cluster
- Hardware metadata strategy
- Validation plan
- Risk assessment

---

## 📦 **Package Contents**

### Core Documents

#### 1. FRESCO_v2_Rebuild_Package_Index.md (14KB)
**Purpose**: High-level package overview  
**Contains**: Contents summary, problem statement, source overview, task definition, handoff checklist

#### 2. FRESCO_v2_Agent_Prompt.md (26KB) ⭐
**Purpose**: Main briefing for planning agent  
**Contains**: Complete context, 6 issues, source structure, 65-column schema, task definition, questions

#### 3. FRESCO_v2_Quick_Start.md (12KB)
**Purpose**: Step-by-step getting started guide  
**Contains**: Reading order, first actions, phase template, validation checklist, questions template

### Reference Documentation

#### 4. FRESCO_v2_Complete_Schema.md (18KB)
**Purpose**: Authoritative v2.0 schema specification  
**Contains**: 65 columns (9 categories), types, rationale, validation rules, example rows, migration guide

#### 5. FRESCO_Dataset_Agent_Design_Guide.md (18KB)
**Purpose**: Critical design questions and factors  
**Contains**: 25 blocking questions, design factors, lessons learned, 5-phase process, red flags

#### 6. FRESCO_Source_Data_Map.md (14KB)
**Purpose**: Navigate original repository structure  
**Contains**: 3-cluster profiles, exploration workflow, validation checks, common pitfalls, next steps

#### 7. FRESCO_v2_Recommendations.md (8KB)
**Purpose**: Initial recommendations (early draft)  
**Contains**: Critical additions, minimum viable fix, validation approach

### Official Documentation

#### 8. FRESCO_Repository_Description.pdf (395KB)
**Purpose**: Authoritative source schema from dataset creators  
**Contains**: Official specifications for Anvil, Conte, Stampede data formats  
**Action**: Read this first before sampling data

---

## 🗺️ **Source Data Location**

**Repository**: `/depot/sbagchi/www/fresco/repository/` (on Gilbreth cluster)

### Structure
```
repository/
├── Anvil/                          # 2022-2023, modern CSV pairs
│   ├── JobAccounting/              # Job-level attributes
│   └── JobResourceUsage/           # Time-series metrics
├── Conte/                          # 2015-2017, hybrid format
│   ├── AccountingStatistics/       # SLURM accounting
│   ├── TACC_Stats/                # Monthly subdirs
│   └── kickstand_2015.csv         # Outage logs (unique!)
└── Stampede/                       # 2013-2018, legacy format
    ├── AccountingStatistics/       # SLURM accounting
    └── TACC_Stats/                # 6,976 node directories
```

### Current Combined Dataset (v1.0)
**Location**: `/depot/sbagchi/data/josh/FRESCO/chunks/`  
**Format**: Hourly Parquet shards (`YYYY/MM/DD/HH[_TOKEN].parquet`)  
**Issues**: See "Critical v1.0 Issues" above

---

## 🔬 **Research Context**

This rebuild is informed by three experiments:

### EXP-011: Memory Transfer Baseline
- **Finding**: All cross-site transfers have R² < 0 (catastrophic)
- **Worst case**: Stampede → Anvil R² = -24.3
- **Coverage**: 99.9% (not a data availability issue)

### EXP-012: Memory Label Validation
- **Finding**: 6-9× systematic offsets between clusters
- **Root cause**: Different measurement methodologies
  - Anvil: 9.1× more than Conte
  - Stampede: 5.7× more than Anvil
- **Ruled out**: Units errors, aggregation differences

### EXP-013: Memory Recalibration
- **Finding**: Affine calibration rescues all transfers (ΔR² up to +24.4)
- **But**: Post-calibration R² remains low (0.01-0.04)
- **Lesson**: Can eliminate bias but need standardized metrics for true comparability

**Full reports**: `../FRESCO-Research/Experiments/EXP-011_*/`, etc.  
**Findings log**: `../FRESCO-Research/Documentation/Findings_Log.md` (FIND-025 to FIND-031)

---

## 🎯 **Key Improvements in v2.0**

### New Columns (Critical)
1. **`cluster`**: Explicit identifier {"stampede", "conte", "anvil"}
2. **`node_memory_gb`**: Enables normalization (THE game-changer)
3. **`peak_memory_fraction`**: Cross-site comparable metric
4. **`memory_includes_cache`**: Documents methodology explicitly
5. **`memory_collection_method`**: "slurm_jobacct", "cgroups", "custom"
6. **`timelimit_sec`**: Normalized to seconds (from inconsistent minutes/seconds)

### New Category: Hardware Context (10 columns)
- `node_memory_gb`, `node_cores`, `node_type`
- `partition`, `hardware_generation`
- `gpu_type`, `gpu_memory_gb`, `gpus_per_node`, `gpus_allocated`
- `network_topology`

### Companion File: clusters.json
Separate metadata documenting:
- Memory collection methodology per cluster
- Node specifications per partition
- SLURM version timeline
- Hardware changes/upgrades
- Known issues

**Why critical**: Documents what cannot be inferred from data alone

---

## 📊 **Statistics**

### Documentation Package
- **Total docs**: 8 files (107KB markdown + 395KB PDF)
- **Main prompt**: 26KB (comprehensive briefing)
- **Schema**: 65 columns (vs 22 in v1.0)
- **Questions**: 25 blocking questions organized by category
- **Phases**: 6 recommended (discovery → hardware → pilot → production → release → validation)

### Dataset Scale
- **Jobs**: 20.9 million
- **Months**: 75 (gaps: 2018-05 through 2022-05)
- **Clusters**: 3 (Stampede, Conte, Anvil)
- **Years span**: 2013-2023 (10 years)

### Research Results (That Motivated This)
- **Cross-site R²**: -24.3 to -0.7 (all negative)
- **Systematic offsets**: 6-9× between clusters
- **Calibration improvement**: +24.4 ΔR² (Stampede → Anvil)
- **Post-calibration**: R² 0.01-0.04 (weak underlying signal)

---

## ✅ **Recommended Workflow**

### Phase 1: Planning (You Are Here)
1. Read `FRESCO_v2_Agent_Prompt.md` (main briefing)
2. Review `FRESCO_v2_Complete_Schema.md` (target schema)
3. Study 25 blocking questions (Design Guide)
4. Sample source data on Gilbreth
5. Identify questions requiring dataset creator input
6. Draft comprehensive implementation plan
7. Present to user for approval

### Phase 2: Discovery
- Read official PDF documentation
- Sample files from all 3 clusters
- Document actual schemas found
- Answer 25 blocking questions
- Verify assumptions

### Phase 3: Hardware Metadata
- Build `clusters.json` with node specs
- Source from user guides, sysadmin, vendor docs
- Validate against job allocations

### Phase 4: Pilot
- Implement for one month (recommend: 2015-03)
- Process Conte + Stampede (overlap period)
- Run validation suite
- Go/no-go decision

### Phase 5: Production
- Parallelize across 75 months
- Monitor progress and errors
- Handle edge cases

### Phase 6: Release
- Final validation
- Data quality report
- Documentation updates
- Reproducibility package

---

## ⚠️ **Critical Warnings**

### Do NOT:
- ❌ Assume format consistency (each cluster is unique)
- ❌ Skip validation phases (fail fast)
- ❌ Make up answers to blocking questions
- ❌ Discard original values (preserve provenance)
- ❌ Rush to production (pilot first)

### Do:
- ✅ Read all docs before planning (2-3 hours)
- ✅ Sample actual source files
- ✅ Ask dataset creator for institutional knowledge
- ✅ Plan validation at every phase (30-40% effort)
- ✅ Preserve cluster-specific logic
- ✅ Document irreversible decisions

---

## 🔗 **Related Projects**

### FRESCO-Research (Parent Project)
**Location**: `../FRESCO-Research/`  
**Purpose**: Active research on FRESCO dataset  
**Contains**:
- 28 experiments (Master_Index.md)
- 31 findings (Findings_Log.md)
- Active research paths (Research_Plan.md)
- EXP-011/012/013 that motivated this rebuild

### Relationship
- **FRESCO-Research**: Uses v1.0, discovers issues, conducts experiments
- **FRESCO-v2**: Rebuilds dataset to fix discovered issues
- **Flow**: Research findings → v2.0 requirements → rebuild → better research

---

## 📞 **Contact / Next Steps**

### Questions for Dataset Creator
The planning agent will identify which of the 25 blocking questions require your input, such as:
- Memory methodology (cache inclusion per cluster?)
- TACC_Stats structure (what's inside dirs?)
- v1.0 pipeline (can you share code?)
- Hardware specs (node memory per partition?)

### Ready to Start?
When you have a planning agent ready:

**Prompt**: "Read `FRESCO_v2_Agent_Prompt.md` in this directory and create a comprehensive plan to rebuild the FRESCO dataset. Follow all instructions in the document."

---

## 📚 **Reading Order for Agents**

### Essential (Must Read)
1. `README.md` (this file) - 5 minutes
2. `FRESCO_v2_Agent_Prompt.md` - 30 minutes
3. `FRESCO_v2_Complete_Schema.md` - 20 minutes
4. `FRESCO_Dataset_Agent_Design_Guide.md` (Part 1 & 4) - 20 minutes

**Total**: ~75 minutes essential reading

### Detailed (Reference as Needed)
5. `FRESCO_Source_Data_Map.md` - When exploring source data
6. `FRESCO_v2_Quick_Start.md` - Step-by-step checklist
7. `FRESCO_v2_Rebuild_Package_Index.md` - High-level overview
8. `FRESCO_Repository_Description.pdf` - Official source schemas

---

## 🎓 **Key Lessons Learned**

From EXP-011/012/013:

1. **Metadata is not optional**: Undocumented methodology caused 6-9× offsets
2. **Normalization requires context**: Need `node_memory_gb` for `peak_memory_fraction`
3. **Heterogeneity is reality**: Don't force unification where it doesn't exist
4. **Calibration has limits**: Can remove bias but can't create transferable signal
5. **Validation finds issues early**: 1% sample caught root cause
6. **Provenance matters**: Future researchers need to trace to source

---

## ✨ **Success Criteria**

The v2.0 rebuild succeeds when:

1. **All 6 critical issues addressed**
   - Cross-site memory comparisons are scientifically valid
   - Metadata enables proper normalization
   - Units are consistent
   - Provenance is explicit

2. **Validation passes**
   - Row counts match sources
   - Join rates > 95%
   - Normalized metrics ∈ [0, 1]
   - Cross-cluster distributions reasonable

3. **Documentation complete**
   - clusters.json exists and is comprehensive
   - All transformations documented
   - Reproducibility package ready

4. **Research-grade quality**
   - Suitable for peer-reviewed publication
   - Enables cross-site analysis
   - Supports transfer learning

---

**Project Status**: Planning Phase  
**Next Milestone**: Implementation plan created and approved  
**Estimated Duration**: 4-8 weeks (full rebuild)  
**Last Updated**: 2026-02-01

---

**Go rebuild FRESCO the right way!** 🚀
