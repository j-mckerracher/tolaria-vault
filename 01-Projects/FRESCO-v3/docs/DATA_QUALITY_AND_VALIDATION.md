# FRESCO v3 Data Quality & Validation

**Last Updated**: 2026-03-11

## Implementation status (PROD-20260203-v3)
The production build itself still writes only `validation/schema_report.json`, but `scripts/finalize_production_v3.py` has now backfilled the missing validation and reproducibility artifacts for `PROD-20260203-v3`.

Artifacts now present for the finalized production run:
- `validation/dtype_report.json`
- `validation/missingness_report.json`
- `validation/sanity_checks.json`
- `validation/python_version.txt`
- `validation/pip_freeze.txt`
- `validation/conda_env.yml`
- `validation/host_info.txt`

Current quantified sanity findings for `PROD-20260203-v3`:
- `42` rows with negative `queue_time_sec` / `submit_after_start`
- `402,365` rows with `runtime_fraction > 1.05`

So the run now has machine-readable validation outputs, but the remaining sanity exceptions still need to be documented and judged in context rather than treated as a full clean pass.

## 1. Validation levels

### Level 0 (Schema)
- Column set matches canonical schema
- Dtypes match expected types

### Level 1 (Sanity)
- Non-negative constraints: `nhosts>0`, `ncores>0`, `timelimit_sec>0`
- `runtime_sec >= 0`, `queue_time_sec >= 0`
- `peak_memory_fraction` in (0, 2] after cleaning (document thresholds)

### Level 2 (Cross-field consistency)
- `runtime_sec <= timelimit_sec * (1+epsilon)` (allow for scheduler rounding)
- `runtime_fraction` in [0,1+epsilon]

### Level 3 (Distribution monitoring)
- Missingness per column per cluster
- Drift checks across months (basic alarms)

## 2. Known data caveats
- Conte: time ordering inconsistencies in legacy accounting data (expected warning)
- Cross-cluster: partition/node_type may be disjoint; comparisons require regime matching

## 3. Required validation artifacts
Each run must produce machine-readable outputs:
- schema diff report
- dtype report
- missingness report (per cluster, per month)
- summary statistics table

## 4. Acceptance criteria for production
- Level 0 and Level 1 must pass
- Level 2 failures must be quantified and documented
- Level 3 used for monitoring, not hard-fail (unless extreme)
