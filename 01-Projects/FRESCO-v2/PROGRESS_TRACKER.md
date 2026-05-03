# FRESCO v2.0 Rebuild: Progress Tracker

**Last Updated**: 2026-02-01  
**Current Phase**: Phase 4 Complete → Phase 5 (Conte/Stampede extractors) Starting

---

## Phase Completion Status

### ✅ Phase 1: Planning & Requirements (COMPLETE)
- [x] Read official documentation
- [x] Analyze v1.0 issues (EXP-011/012/013)
- [x] Define requirements
- [x] Create implementation plan

### ✅ Phase 2: Schema Design (COMPLETE)
**Deliverables**: `phase2_outputs/`
- [x] `clusters.json` (16 KB) - Hardware metadata, memory methodology
- [x] `comparability_matrix.md` (14 KB) - Metric-by-metric cross-cluster guide
- [x] `schema_design_complete.md` (25 KB) - Full 65-column specification
- [x] `phase2_summary.md` (14 KB) - Completion summary

**Key achievements**:
- Documented memory methodology for all 3 clusters
- Identified 6 critical v1.0 fixes
- Designed normalized + provenance column strategy

### ✅ Phase 3: Transformation Pipeline (COMPLETE)
**Deliverables**: `phase3_pipeline/`
- [x] Base extractor with hardware join logic
- [x] Anvil extractor (fully implemented)
- [x] Memory normalization module
- [x] Time normalization module (critical timelimit fix)
- [x] Schema validation framework
- [x] Runnable pilot script
- [x] SLURM submission script
- [x] Comprehensive documentation

**Key achievements**:
- Two-stage pipeline: Extract → Transform → Validate → Output
- Timelimit minutes→seconds conversion for Stampede
- Memory fractions computation (peak / node_memory)
- Dual column strategy (normalized + original)

### ✅ Phase 4: Validation (COMPLETE)
**Deliverables**:
- [x] `PHASE4_VALIDATION_COMPLETE.md` (14 KB) - Full validation report
- [x] `PHASE4_SUMMARY.md` (5.5 KB) - Executive summary
- [x] `phase4_validation_sample.csv` (59 KB) - 100 sample jobs
- [x] SLURM job execution (Job ID 10246311, success)

**Validation results**:
- ✅ 158,455 jobs extracted (August 2022 Anvil)
- ✅ All 6 critical fixes verified
- ✅ Schema compliance: 57 columns implemented
- ✅ Processing rate: 264 jobs/sec
- ✅ Output: 10 MB parquet (63 bytes/job)

**Critical fixes verified**:
1. ✅ Cluster identifier column
2. ✅ Timelimit units normalized
3. ✅ Hardware context joined (node_memory_gb)
4. ✅ Memory fractions computed
5. ✅ Memory methodology metadata
6. ✅ Failure classification enhanced

### ⏳ Phase 5: Multi-Cluster Implementation (IN PROGRESS)
**Goal**: Implement Conte and Stampede extractors
- [ ] Conte extractor (TACC_Stats monthly + outage join)
- [ ] Stampede extractor (node-partitioned reconstruction)
- [ ] Validation pilot (one month each)
- [ ] Cross-cluster offset measurement

**Estimated time**: 1 week

### ⏳ Phase 6: Production Run (NOT STARTED)
**Goal**: Process all 75 months across 3 clusters
- [ ] SLURM array job parallelization
- [ ] Progress monitoring dashboard
- [ ] Error handling and retry logic
- [ ] Final data quality report

**Estimated time**: 1 week

### ⏳ Phase 7: Scientific Validation (NOT STARTED)
**Goal**: Verify improvements over v1.0
- [ ] Re-run EXP-011 memory prediction
- [ ] Measure ΔR² improvement (expected: -24 → positive)
- [ ] Cross-cluster offset verification
- [ ] v1.0 vs v2.0 comparison report

**Estimated time**: 3-5 days

### ⏳ Phase 8: Release (NOT STARTED)
**Goal**: Public dataset release
- [ ] Documentation updates (README, methodology)
- [ ] Website update (frescodata.xyz)
- [ ] Release notes
- [ ] Citation guide

**Estimated time**: 2-3 days

---

## File Inventory

### Local Documentation (Windows)
Location: `C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\FRESCO-v2\`

**Phase 2 outputs** (`phase2_outputs/`):
- `clusters.json` - Hardware specifications
- `comparability_matrix.md` - Cross-cluster metric guide
- `schema_design_complete.md` - 65-column schema
- `phase2_summary.md` - Phase 2 completion

**Phase 3 pipeline** (`phase3_pipeline/`):
- `src/extractors/base.py` - Base extractor class
- `src/extractors/anvil.py` - Anvil implementation
- `src/transforms/memory.py` - Memory normalization
- `src/transforms/time.py` - Time normalization
- `src/validation/schema.py` - Validation framework
- `scripts/run_pilot.py` - Pilot execution
- `scripts/slurm_pilot.sh` - SLURM submission
- `scripts/validate_pilot.py` - Comprehensive validation
- Documentation: `QUICKSTART.md`, `PHASE3_COMPLETE.md`

**Phase 4 validation**:
- `PHASE4_VALIDATION_COMPLETE.md` - Full report
- `PHASE4_SUMMARY.md` - Executive summary
- `phase4_validation_sample.csv` - Sample output

**Design guides**:
- `FRESCO_Dataset_Agent_Design_Guide.md` - 25 blocking questions
- `FRESCO_Source_Data_Map.md` - Repository structure
- `FRESCO_v2_Complete_Schema.md` - Schema specification

### On Gilbreth (Production)
Location: `/depot/sbagchi/data/josh/FRESCO-Research/Experiments/phase4_validation/`

**Pipeline**:
- `phase3_pipeline/` - Complete pipeline (17 files)
- Conda environment: `fresco_v2` (Python 3.10.19)

**Pilot output**:
- `pilot_output/anvil_202208.parquet` - 10 MB, 158,455 jobs
- `pilot_output/validation_report_anvil_202208.json` - Validation summary
- `pilot_output/sample_anvil_202208.csv` - 100 sample jobs

**Logs**:
- `logs/pilot_10246311.{out,err}` - SLURM job logs
- `phase3_pipeline/pilot_run.log` - Execution trace

---

## Key Metrics

### v1.0 Issues (From EXP-011/012/013)
- ❌ Cross-cluster memory R² = -24.3 (catastrophic)
- ❌ 6-9× systematic offsets between clusters
- ❌ No `node_memory_gb` column
- ❌ No `cluster` identifier
- ❌ Timelimit in minutes (Stampede) vs seconds (others)
- ❌ Undocumented memory methodology

### v2.0 Improvements (Verified in Phase 4)
- ✅ Explicit `cluster` column (100% coverage)
- ✅ `node_memory_gb` joined from hardware specs (100% coverage)
- ✅ `peak_memory_fraction` computed (70.6% coverage)
- ✅ `memory_includes_cache`, `memory_collection_method` metadata
- ✅ Timelimit normalized to seconds (conversion ready for Stampede)
- ✅ Rich failure classification (state, oom_killed, timeout)

### Pipeline Performance
- **Processing rate**: 264 jobs/second
- **Compression**: 63 bytes/job (Parquet)
- **Memory coverage**: 70.6% (consistent with v1.0)
- **Failure rate**: 36% (Anvil August 2022)
- **OOM detection**: 0.1% (209 jobs)

### Projected Full Dataset
- **Total jobs**: ~20.9 million
- **Total size**: ~1.1 GB (vs v1.0's 20+ GB)
- **Processing time**: ~2 hours (Anvil + Conte + Stampede, parallelized)

---

## Next Action Items

### Immediate (Today/Tomorrow)
1. ⏳ Compare v2.0 to v1.0 August 2022 Anvil (verify parity)
2. ⏳ Investigate CPU efficiency = 100% (compare to v1.0 value_cpuuser)
3. ⏳ Start Conte extractor implementation

### This Week
4. ⏳ Implement Conte TACC_Stats monthly parsing
5. ⏳ Join Conte outage log (system_issue flag)
6. ⏳ Validate Conte on 2015-03 (overlap with Stampede)

### Next Week
7. ⏳ Implement Stampede node-partitioned reconstruction
8. ⏳ Validate Stampede on 2015-03
9. ⏳ Measure cross-cluster offsets (raw vs fractions)

### Week 3
10. ⏳ Re-run EXP-011 with v2.0 data
11. ⏳ Production run (75 months, SLURM array jobs)
12. ⏳ Final quality report and v2.0 release

---

## Blocking Issues

**Current**: None ✅

**Resolved**:
- ✅ DOS line endings in SLURM script (fixed with dos2unix)
- ✅ Conda environment setup (working)
- ✅ GPU resource allocation (--gres=gpu:1 required)
- ✅ Schema validation (minor type warnings, non-critical)

**Watching**:
- ⚠️ CPU efficiency = 100% (needs investigation)
- ⚠️ Memory fractions >1.0 (1.92 max, may be legitimate)
- ⚠️ Missing QoS data (100% null, may be expected)

---

## Resources

### Documentation
- Official: `/depot/sbagchi/www/fresco/repository/FRESCO_Repository_Description.pdf`
- Schema: `FRESCO_v2_Complete_Schema.md`
- Design: `FRESCO_Dataset_Agent_Design_Guide.md`
- Source map: `FRESCO_Source_Data_Map.md`

### Data Locations
- Source: `/depot/sbagchi/www/fresco/repository/{Anvil,Conte,Stampede}/`
- v1.0: `/depot/sbagchi/data/josh/FRESCO/chunks/`
- v2.0 workspace: `/depot/sbagchi/data/josh/FRESCO-Research/Experiments/phase4_validation/`

### Computing
- Cluster: Gilbreth (Purdue RCAC)
- Resources: `--gres=gpu:1` required for all jobs
- Submission: `sbbest <slurm_script>` (not `sbatch`)
- Conda env: `fresco_v2` (Python 3.10.19)

---

## Timeline Estimate

- **Phases 1-4**: ✅ Complete (3 days)
- **Phase 5** (Conte/Stampede): 1 week
- **Phase 6** (Production): 1 week
- **Phase 7** (Validation): 3-5 days
- **Phase 8** (Release): 2-3 days

**Total to v2.0 release**: 2-3 weeks from today

---

**Last validated**: 2026-02-01 18:18 UTC  
**Pilot job**: 10246311 (success)  
**Current focus**: Conte extractor implementation
