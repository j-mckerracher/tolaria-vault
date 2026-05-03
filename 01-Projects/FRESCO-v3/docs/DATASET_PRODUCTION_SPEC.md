# FRESCO v3 Dataset Production Specification

**Last Updated**: 2026-02-03  
**Status**: Draft (baseline requirements)

## 1. Scope
FRESCO v3 is a reproducible pipeline that produces a **unified, provenance-rich dataset** that supports **defensible cross-cluster insights** via:

1. A stable, unified schema across clusters and eras.
2. Normalized metrics (e.g., memory fractions) to reduce gross scale mismatches.
3. Explicit provenance metadata documenting measurement semantics.
4. Workload taxonomy + overlap-aware matching to enable valid cross-cluster comparisons.

## 2. Inputs
- Raw source shards (FRESCO): `/depot/sbagchi/data/josh/FRESCO/chunks/` (hourly parquet)
- Hardware metadata: clusters.json (node_memory_gb, gpu_model, etc.)

## 3. Outputs
### 3.1 Primary dataset
- Output root: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/`
- Partitioning: `chunks-v3/<YYYY>/<MM>/<DD>/<HH>.parquet`
- Files contain **mixed clusters** in a single schema.

### 3.2 Required artifacts
- `manifests/`:
  - `input_manifest.jsonl` (every input shard processed)
  - `output_manifest.jsonl` (every output shard written)
  - `run_metadata.json` (run config, git hashes, environment)
- `validation/`:
  - `schema_report.json`
  - `missingness_report.json`
  - `dtype_report.json`
  - `sanity_checks.json`

## 4. Schema invariants
- Every output file must conform to the canonical schema described in `docs/SCHEMA_AND_PROVENANCE.md`.
- Dtype stability is mandatory (no mixed object/float in parquet writes).
- A `cluster` column is mandatory and must be one of {anvil, conte, stampede}.

## 5. Cross-cluster comparability requirements
Cross-cluster insights must be produced using one of:
- **Regime matching** (recommended): only compare cohorts where feature support overlaps.
- **Taxonomy alignment**: partition/node types mapped to a shared taxonomy.

All cross-cluster results must report:
- overlap coverage (% of target jobs covered)
- cohort definition
- measurement semantics flags (e.g., memory_includes_cache)

## 6. Reproducibility contract
Every run must be reproducible from:
- the git commit(s)
- the config file
- the run manifest
- the environment lock

See `runbooks/REPRODUCIBILITY_CHECKLIST.md`.

---

## 7. Future Dataset / New Cluster Extensibility (Design Requirement)
FRESCO v3 must support adding new datasets/clusters **without redesign**.

### 7.1 Integration model
New datasets are integrated by implementing a new **source adapter/extractor** that maps raw fields into the **canonical schema + provenance semantics**, while:
- enforcing explicit dtypes before parquet write
- using schema union-by-name (missing columns present as nulls)
- emitting measurement semantics provenance fields

### 7.2 What must be updated when a new dataset is added
- extractor module (new adapter)
- hardware/provenance metadata (e.g., clusters.json extension)
- taxonomy mapping (partition/node_type → `workload_regime`)
- schema version (only if new canonical columns are introduced; maintain backward compatibility)

### 7.3 When a redesign would be required
A redesign is only needed if a future dataset breaks core assumptions, e.g.:
- no stable job identifiers or timestamps
- fundamentally different granularity (not job-level)
- metrics that cannot be expressed via the schema/provenance framework

