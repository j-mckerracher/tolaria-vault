# FRESCO v4 Data Quality & Validation

**Last Updated**: 2026-03-13

## Dataset source
FRESCO v4 uses the authoritative `chunks-v3` dataset. All data quality properties, validation levels, and acceptance criteria are inherited from FRESCO v3.

See `FRESCO-v3/docs/DATA_QUALITY_AND_VALIDATION.md` for the full specification.

## Validation levels (summary)

### Level 0 (Schema)
- Column set matches canonical schema
- Dtypes match expected types

### Level 1 (Sanity)
- Non-negative constraints: `nhosts > 0`, `ncores > 0`, `timelimit_sec > 0`
- `runtime_sec >= 0`, `queue_time_sec >= 0`
- `peak_memory_fraction` in (0, 2] after cleaning

### Level 2 (Cross-field consistency)
- `runtime_sec <= timelimit_sec * (1 + epsilon)`
- `runtime_fraction` in [0, 1 + epsilon]

### Level 3 (Distribution monitoring)
- Missingness per column per cluster
- Drift checks across months

## Acceptance criteria
- Level 0 and Level 1 must pass
- Level 2 failures must be quantified and documented
- Level 3 used for monitoring, not hard-fail (unless extreme)

## Known data caveats (inherited from v3)

### Production-level caveats
- **42 rows** with negative `queue_time_sec` / `submit_after_start` in `PROD-20260203-v3`
- **402,365 rows** with `runtime_fraction > 1.05` in `PROD-20260203-v3`
- Conte: time ordering inconsistencies in legacy accounting data (expected warning)

### Cross-cluster caveats
- Partition/node_type may be disjoint across clusters; comparisons require regime matching
- `memory_includes_cache` differs across clusters (Anvil=true, Conte/Stampede=false)
- Conte and Stampede hardware metadata relies on cluster-wide defaults (queue names anonymized)

### v4-specific validation notes
- Few-shot calibration sets (the N labeled target jobs) must be validated for:
  - Non-null `peak_memory_fraction`
  - Membership in the overlap cohort
  - No duplication with the evaluation set
- The calibration/evaluation split is deterministic given `few_shot.target_label_seed` and `few_shot.n_target_labels`

## Required validation artifacts per v4 experiment
Each v4 experiment run should produce:
- `results/metrics.json` (evaluation metrics on held-out target)
- `results/calibration_params.json` (learned calibration parameters, if applicable)
- `manifests/calibration_job_ids.json` (the N job IDs used for calibration)
- `validation/split_integrity_check.json` (confirms zero overlap between calibration and evaluation sets)
