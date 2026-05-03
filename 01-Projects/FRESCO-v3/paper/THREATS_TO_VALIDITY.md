# Threats to Validity

**Last Updated**: 2026-02-03

## Measurement non-equivalence
Memory and performance metrics may be collected via different mechanisms across clusters (cgroups vs RSS vs accounting), affecting comparability.

## Temporal drift
Clusters span different eras (Conte 2015 vs Anvil 2022), introducing changes in hardware, software stacks, and user workloads.

## Covariate shift
Workload distributions can be disjoint (e.g., partitions/node types), making global transfer invalid.

## Hidden confounding
Unobserved factors (application type, user behavior, policy) may drive differences.

## Mitigations
- provenance metadata
- regime matching and overlap diagnostics
- sensitivity analyses
