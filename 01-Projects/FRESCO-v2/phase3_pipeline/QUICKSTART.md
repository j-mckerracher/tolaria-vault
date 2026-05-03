# FRESCO v2.0 Phase 3 - Quick Start Guide

**Ready to run the pilot?** Follow these steps.

---

## Prerequisites

- Access to Gilbreth cluster
- Python 3.10+
- Source data at `/depot/sbagchi/www/fresco/repository/`

---

## Setup (5 minutes)

```bash
# 1. SSH to Gilbreth
ssh jmckerra@gilbreth.rcac.purdue.edu

# 2. Create workspace
cd /depot/sbagchi/data/josh/FRESCO-Research/Experiments/
mkdir phase3_pilot && cd phase3_pilot

# 3. Copy pipeline (from Windows to Gilbreth)
# Run this in PowerShell on Windows:
scp -r "C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\FRESCO-v2\phase3_pipeline" jmckerra@gilbreth.rcac.purdue.edu:/depot/sbagchi/data/josh/FRESCO-Research/Experiments/phase3_pilot/

# 4. Setup conda environment (back on Gilbreth)
cd phase3_pipeline
module load anaconda
conda create -n fresco_v2 python=3.10 -y
conda activate fresco_v2
pip install -r requirements.txt
```

---

## Run Pilot (10 minutes)

```bash
# Run extraction for August 2022 (Anvil)
python scripts/run_pilot.py \
  --month 2022-08 \
  --cluster anvil \
  --source /depot/sbagchi/www/fresco/repository/ \
  --output ../pilot_output/

# Watch progress
tail -f pilot_run.log
```

---

## Check Results

```bash
# View summary
tail -100 pilot_run.log

# List output files
ls -lh ../pilot_output/
# Expected:
#   anvil_202208.parquet          (~200-400MB)
#   validation_report_*.json       (~2KB)
#   sample_*.csv                   (~50KB)

# Inspect validation report
cat ../pilot_output/validation_report_anvil_202208.json

# Load in Python to check
python -c "
import pandas as pd
df = pd.read_parquet('../pilot_output/anvil_202208.parquet')
print(f'Loaded {len(df)} jobs')
print(f'Columns: {len(df.columns)}')
print(f'Date range: {df[\"submit_time\"].min()} to {df[\"submit_time\"].max()}')
print(f'Memory coverage: {df[\"peak_memory_gb\"].notna().sum()/len(df)*100:.1f}%')
print(df.describe())
"
```

---

## Expected Output

### Success Looks Like:

```
================================================================================
FRESCO v2.0 PILOT RUN
================================================================================
Month: 2022-08
Cluster: anvil
Source: /depot/sbagchi/www/fresco/repository/
Output: ../pilot_output/
================================================================================

================================================================================
STAGE 1: EXTRACTION
================================================================================
Initialized anvil extractor
Extracting Anvil 2022-08
Read 1234567 jobs from accounting
Read 45678901 metric samples
✓ Extracted 1234567 jobs

================================================================================
STAGE 2: TRANSFORMATION
================================================================================
Normalizing timestamps to UTC...
✓ Normalized timestamps to UTC for anvil
Normalizing timelimit to seconds...
anvil timelimit already in seconds
✓ Computed derived time fields for 1234567 jobs
Normalizing memory units...
Anvil memory already in GB, no conversion needed
✓ Computed memory fractions for 1234567 jobs
  Mean peak_memory_fraction: 0.345
  Median peak_memory_fraction: 0.289
✓ Detected 1234 OOM-killed jobs (0.1%)
✓ Transformation complete

================================================================================
STAGE 3: VALIDATION
================================================================================
Validating 1234567 rows
✓ Validation PASSED
⚠ 2 warnings

VALIDATION REPORT:
  Total jobs: 1234567
  Clusters: {'anvil': 1234567}
  Date range: 2022-08-01 to 2022-08-31
  Memory coverage: 99.8%
  Validation: PASSED ✓

================================================================================
STAGE 4: OUTPUT
================================================================================
✓ Wrote 1234567 jobs to ../pilot_output/anvil_202208.parquet
  File size: 342.50 MB
✓ Wrote validation report to ../pilot_output/validation_report_anvil_202208.json
✓ Wrote sample (100 rows) to ../pilot_output/sample_anvil_202208.csv

================================================================================
SUMMARY STATISTICS
================================================================================
Jobs extracted: 1234567
Date range: 2022-08-01 to 2022-08-31
Partitions: {'gpu': 1100000, 'wide': 100000, 'debug': 34567}
Failed jobs: 45678 (3.7%)
Timed out: 12345 (1.0%)
OOM killed: 1234 (0.1%)

Memory usage:
  Mean peak_memory_fraction: 0.345
  Median peak_memory_fraction: 0.289
  95th percentile: 0.782

CPU efficiency:
  Mean: 67.3%
  Median: 78.9%

================================================================================
PILOT RUN COMPLETE ✓
================================================================================
```

---

## Troubleshooting

### "Module 'pandas' not found"
```bash
conda activate fresco_v2
pip install -r requirements.txt
```

### "Accounting file not found"
```bash
# Check source path
ls /depot/sbagchi/www/fresco/repository/Anvil/JobAccounting/
# Ensure month format is correct (e.g., aug2022 not 2022-08)
```

### "Validation failed"
```bash
# Check error messages in pilot_run.log
cat pilot_run.log | grep ERROR
# Common issues:
#   - Missing columns: Check extractor column mapping
#   - Time ordering: Check timestamp parsing
#   - Range violations: Check transform logic
```

---

## What to Check in Output

### 1. Validation Report (`validation_report_*.json`)

```json
{
  "total_jobs": 1234567,
  "validation_passed": true,  // ← MUST be true
  "memory_coverage": 99.8,     // ← Should be >99%
  "error_count": 0,            // ← MUST be 0
  "warning_count": 2           // ← <10 is acceptable
}
```

### 2. Sample CSV (`sample_*.csv`)

Open in Excel/LibreOffice and spot-check:
- [ ] `cluster` = "anvil" for all rows
- [ ] `submit_time` has timezone (e.g., "2022-08-31 17:29:55+00:00")
- [ ] `timelimit_sec` in seconds (e.g., 345600 = 96 hours)
- [ ] `peak_memory_fraction` between 0 and 1 (mostly)
- [ ] `node_memory_gb` populated (e.g., 256 for Anvil GPU)
- [ ] `memory_includes_cache` = True

### 3. Parquet File Size

- **Anvil month**: 200-400MB compressed
- **If <50MB**: Missing metrics, check join logic
- **If >1GB**: Uncompressed, check parquet write settings

---

## Next Steps After Pilot

### If Pilot Succeeds ✓

1. **Review with domain expert** (Josh/advisor)
2. **Proceed to Phase 3b**: Implement Conte + Stampede extractors
3. **Phase 4**: Run full validation (all 3 clusters, one month each)
4. **Phase 5**: Production run (all 75 months)

### If Pilot Has Issues ✗

1. **Review errors** in `pilot_run.log`
2. **Check sample output** for anomalies
3. **Fix identified issues** in extractor or transforms
4. **Re-run pilot**

---

## Quick Commands Reference

```bash
# Activate environment
conda activate fresco_v2

# Run pilot (Anvil, Aug 2022)
python scripts/run_pilot.py --month 2022-08 --output ../pilot_output/

# Check output size
du -sh ../pilot_output/

# View validation report
cat ../pilot_output/validation_report_anvil_202208.json | python -m json.tool

# Load and describe in Python
python -c "import pandas as pd; pd.read_parquet('../pilot_output/anvil_202208.parquet').info()"

# Check logs
tail -100 pilot_run.log
grep ERROR pilot_run.log
grep WARNING pilot_run.log
```

---

## Contact

- **Implementation questions**: See `phase3_summary.md`
- **Schema questions**: See `../phase2_outputs/schema_design_complete.md`
- **Hardware specs**: See `config/clusters.json`

---

**Ready? Run the pilot and report back!** 🚀
