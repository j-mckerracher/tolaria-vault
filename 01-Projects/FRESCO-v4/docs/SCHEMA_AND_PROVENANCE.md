# FRESCO v4 Schema & Provenance

**Last Updated**: 2026-03-13

## Purpose
Define the schema fields and provenance considerations relevant to FRESCO v4 few-shot cross-cluster transfer experiments. The full canonical schema is defined in `FRESCO-v3/docs/SCHEMA_AND_PROVENANCE.md`; this document highlights the subset most critical to v4.

## Key fields for v4

### Identifiers
| Column | Type | Description |
|--------|------|-------------|
| `jid` | string | Job identifier (normalized to string) |
| `cluster` | categorical | One of: `anvil`, `conte`, `stampede` |

### Features (safe set for cross-cluster modeling)
| Column | Type | Description |
|--------|------|-------------|
| `ncores` | int64 | Number of cores allocated |
| `nhosts` | int64 | Number of hosts allocated |
| `timelimit_sec` | float64 | Wall-clock time limit in seconds |
| `runtime_sec` | float64 | Actual runtime in seconds (derived at analysis time) |
| `runtime_fraction` | float64 | `runtime_sec / timelimit_sec` |

> **NOTE**: `queue_time_sec` was included in the v3 safe feature set but is **dropped** for v4 per the v3 instability findings (EXP-062 through EXP-069 demonstrated that removing `queue_time_sec` stabilized cross-universe transfer). See `docs/feature_matrix.md` for details.

### Label
| Column | Type | Description |
|--------|------|-------------|
| `peak_memory_fraction` | float64 | Derived as `value_memused_max / (node_memory_gb * nhosts)` |

This is the primary prediction target. It is computed at analysis time from the raw `value_memused_max` column and hardware metadata recovered from `config/clusters.json`.

### Hardware metadata (recovered at analysis time)
| Column | Type | Source |
|--------|------|--------|
| `partition` | string | Mapped from raw `queue` field |
| `node_type` | string | From `config/clusters.json` |
| `node_cores` | int64 | From `config/clusters.json` |
| `node_memory_gb` | float64 | From `config/clusters.json` |
| `gpu_count_per_node` | int64 | From `config/clusters.json` |
| `gpu_model` | string | From `config/clusters.json` |

Hardware metadata is used to define the `hardware_cpu_standard` regime filter and to compute `peak_memory_fraction`. Conte and Stampede use cluster-wide defaults because their queue identifiers are anonymized.

## Provenance caveat: memory measurement semantics

| Cluster | `memory_includes_cache` | Implication |
|---------|------------------------|-------------|
| Anvil | `true` | `value_memused_max` includes OS page cache |
| Conte | `false` | `value_memused_max` excludes OS page cache |
| Stampede | `false` | `value_memused_max` excludes OS page cache |

This difference in memory measurement semantics means that identical workloads will report **higher** `peak_memory_fraction` on Anvil than on Conte/Stampede, all else being equal. This is the **measurement gap** that few-shot calibration in v4 aims to overcome.

The v3 zero-shot experiments demonstrated that this gap cannot be reliably bridged by feature engineering or unsupervised adaptation alone. Even a small number of labeled target observations (few-shot) provides direct signal about the target cluster's measurement regime, enabling calibration of the source model's predictions.

## Dtype stability rules (inherited from v3)
- No parquet writes with object columns when numeric is intended.
- Enforce explicit casts before any parquet write.
- Missing columns must exist with nulls (schema union by name).

## Versioning
- All v4 experiments reference `dataset_version: "v3.0"` because they use the v3 dataset.
- Run metadata must include git commit hashes and the experiment config file.
