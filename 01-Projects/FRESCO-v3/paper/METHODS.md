# Methods (Draft): FRESCO v3 Pipeline and Comparability

**Last Updated**: 2026-02-03

## Overview
This section is written in a paper-ready style and must be kept synchronized with:
- code commit hashes
- configuration files
- run manifests

## Pipeline
1. **Extraction**: parse raw scheduler/telemetry shards into job-level records.
2. **Transformation**: normalize time and memory measures, attach hardware metadata.
3. **Schema enforcement**: union-by-name across clusters with explicit dtype casts.
4. **Validation**: schema + sanity + cross-field consistency checks.
5. **Output**: hourly parquet shards under a unified directory structure.

## Memory normalization
- We compute `peak_memory_fraction = peak_memory_gb / (node_memory_gb * nhosts)` when peak memory is available.
- In the current authoritative `chunks-v3` workflow, `peak_memory_gb` is derived at analysis time from job-level `value_memused_max`, which is already GB-scale in the production parquet.
- `node_memory_gb` and other hardware context fields are currently recovered at analysis time from `config/clusters.json`, with `partition` recovered from the raw `queue` field.
- When peak_memory_fraction is not present, we compute an equivalent proxy if `node_memory_from_metrics` and `node_memory_gb` are available.
- We record semantics in `memory_includes_cache`, `memory_collection_method`, and related provenance fields.

## Cross-cluster comparability
We do not treat clusters as i.i.d. Instead, cross-cluster insights are derived using:
- a workload taxonomy
- overlap-aware cohort selection
- reporting of overlap coverage and distributional diagnostics

## Reproducibility
Every production run produces:
- input/output manifests
- run metadata including config, commits, and environment locks
- validation reports

This enables full third-party reproduction.
