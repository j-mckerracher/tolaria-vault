# Phase 1 - Feature Availability Matrix (v4 Reference)

**Last Updated**: 2026-03-13

## Source
This document references the authoritative Phase 1 results from FRESCO v3 EXP-039 (`EXP-039_feature_matrix_authoritative_v3`). See `FRESCO-v3/docs/feature_matrix.md` for the complete feature matrix, dtype drift diagnostics, and limitations.

## v3 safe feature set (EXP-039)
The authoritative Phase 1 run on `chunks-v3` identified the following safe features at the strict 0% missingness cutoff:

```text
ncores, nhosts, timelimit_sec, runtime_sec, queue_time_sec, runtime_fraction
```

Key statistics from EXP-039:
- Raw rows sampled: Anvil 171,959 / Conte 85,711 / Stampede 225,830
- Job rows profiled: Anvil 4,622 / Conte 5,015 / Stampede 8,741
- Union columns: 52
- Intersection columns: 52
- Safe columns (0% missingness): 32
- The six features above were selected from the safe set as the most relevant for cross-cluster transfer modeling.

## v4 safe feature set

FRESCO v4 uses the **same safe set minus `queue_time_sec`**:

```text
ncores, nhosts, timelimit_sec, runtime_sec, runtime_fraction
```

### Rationale for dropping `queue_time_sec`
The v3 experimental record (EXP-062 through EXP-069) demonstrated that `queue_time_sec` was a primary source of cross-universe instability:

- With `queue_time_sec` included, transfer results varied wildly across frozen universes and seeds (target R-squared ranged from +0.09 to -2.10).
- Removing `queue_time_sec` and freezing the sampling plan stabilized within-universe results: four modeling seeds on the first frozen universe all produced positive target R-squared with bootstrap CIs above zero (R-squared approximately 0.107-0.111).
- `queue_time_sec` is a scheduling artifact that reflects cluster load patterns rather than intrinsic workload characteristics, making it a poor feature for cross-cluster generalization.

The five remaining features capture job resource allocation (`ncores`, `nhosts`, `timelimit_sec`) and execution behavior (`runtime_sec`, `runtime_fraction`) without scheduling-system confounds.

## Feature descriptions

| Feature | Type | Description | Cross-cluster behavior |
|---------|------|-------------|----------------------|
| `ncores` | int64 | Number of CPU cores allocated | Comparable across clusters |
| `nhosts` | int64 | Number of hosts (nodes) allocated | Comparable across clusters |
| `timelimit_sec` | float64 | Requested wall-clock time limit (seconds) | Comparable; reflects user intent |
| `runtime_sec` | float64 | Actual wall-clock runtime (seconds) | Derived at analysis time; comparable |
| `runtime_fraction` | float64 | `runtime_sec / timelimit_sec` | Normalized; comparable |

## Dtype drift notes (from v3 EXP-039)
Even among safe features, dtype drift exists across clusters and must be normalized:
- `ncores`: int64 (Anvil) vs. double (Conte) vs. int32 (Stampede)
- `nhosts`: int64 (Anvil) vs. double (Conte) vs. int32 (Stampede)

Analysis code must apply explicit casts to a common type (float64 or int64) before modeling.

## Label column
The prediction target is `peak_memory_fraction`, which is **not** in the safe feature set (it is derived at analysis time from `value_memused_max` and hardware metadata). It is never used as a modeling feature.
