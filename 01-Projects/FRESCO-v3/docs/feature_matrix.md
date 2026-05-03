# Phase 1 — Feature Availability Matrix (EXP-016)

## Goal
Compute a vetted list of features that are **safe for cross-cluster modeling** (strict criterion) and document schema/dtype drift that must be normalized before any cross-cluster claims.

## Authoritative update (EXP-039, 2026-03-12)
The original EXP-016 run below was based on a local snapshot. We have now rerun Phase 1 on the authoritative `chunks-v3` parquet as `EXP-039_feature_matrix_authoritative_v3`.

Key authoritative outcomes from the sampled, job-level rerun:
- raw rows sampled:
  - anvil: `171,959`
  - conte: `85,711`
  - stampede: `225,830`
- job rows profiled:
  - anvil: `4,622`
  - conte: `5,015`
  - stampede: `8,741`
- union columns: `52`
- intersection columns: `52`
- safe columns at strict 0% missingness cutoff: `32`

Default safe-feature set for authoritative Phase 2/3 runs:

```text
ncores, nhosts, timelimit_sec, runtime_sec, queue_time_sec, runtime_fraction
```

These are now the preferred overlap features for cross-cluster claims on `chunks-v3`.

## Evidence artifacts
Run folder:
- `experiments\EXP-016_feature_matrix\`

Reproduce:
```powershell
python scripts\feature_matrix.py --config experiments\EXP-016_feature_matrix\config\exp016_feature_matrix.json
```

Key outputs:
- Results: `experiments\EXP-016_feature_matrix\results\feature_matrix.json`
- Input file manifest (SHA256): `experiments\EXP-016_feature_matrix\manifests\input_files.json`
- Run metadata: `experiments\EXP-016_feature_matrix\manifests\run_metadata.json`
- Logs: `experiments\EXP-016_feature_matrix\logs\feature_matrix.log`
- Environment: `experiments\EXP-016_feature_matrix\validation\python_version.txt`, `...\pip_freeze.txt`

## Inputs scanned (local snapshot)
This Phase 1 run was executed on a **local sample** of parquet outputs (not the full `/depot/.../chunks-v3/` dataset):
- Source: `FRESCO-Research\Experiments\EXP-001_baseline_statistical_analysis\results\tmp\job_partials\...`
- Clusters are inferred from `source_token` convention:
  - `NONE` → Anvil
  - `C` → Conte
  - `S` → Stampede

Sampling:
- 20 parquet files sampled per cluster (seeded; see config).

## Acceptance criterion used (strict)
A feature is labeled **safe** iff:
1. It is present in all clusters (column intersection), and
2. Mean missingness per cluster is **0%** on the sampled files.

This is intentionally conservative; it prioritizes defensible transfer setups over feature richness.

## Summary (from `feature_matrix.json`)
- Union columns: **39**
- Intersection columns: **39**
- Safe columns (0% missingness across clusters): **31**
- Not safe under the strict rule: **8**

### Not-safe columns (strict 0% missingness)
These had non-zero missingness in at least one cluster (see `missingness_mean_by_cluster` in the JSON):
- `account` (Conte is 100% null in sampled files)
- `nhosts` (Conte has small missingness)
- `value_block_max`
- `value_cpuuser_max`
- `value_gpu_max` (100% missing for all clusters in this snapshot)
- `value_memused_max`
- `value_memused_minus_diskcache_max`
- `value_nfs_max`

## Dtype drift diagnostics (must normalize)
Even among intersecting columns, dtype drift exists and must be normalized before any unified v3 schema write:
- `ncores`: `int64` (anvil) vs `double` (conte) vs `int32` (stampede)
- `nhosts`: `int64` (anvil) vs `double` (conte) vs `int32` (stampede)
- Timestamps: `timestamp[ns, tz=UTC]` vs `timestamp[us, tz=UTC]` (stampede)
- `exitcode`: dictionary-encoded string in stampede vs string elsewhere
- `timelimit`: `double` (anvil/conte) vs `int64` (stampede)

**Implication**: Phase 2/3 must use explicit casting rules (as required by `docs/SCHEMA_AND_PROVENANCE.md`) before any union-by-name parquet write.

## Limitations
- This Phase 1 run used a local parquet snapshot (EXP-001 job_partials), not the authoritative v3 dataset under `/depot/...`.
- Results are based on **sampled files**; they are strong indicators, but not a substitute for full-dataset validation on the HPC filesystem.

## Next steps (per plan)
- Run the same script against the true v3 (or v2.0) chunk roots on HPC to confirm the safe feature set.
- Use the safe columns as the default feature set for overlap diagnostics + regime matching.
