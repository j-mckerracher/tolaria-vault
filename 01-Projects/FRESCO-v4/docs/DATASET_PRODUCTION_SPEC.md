# FRESCO v4 Dataset Production Specification

**Last Updated**: 2026-03-13

## Dataset Inheritance

FRESCO v4 uses the **authoritative chunks-v3 dataset** produced by the FRESCO v3 pipeline. No new production pipeline is needed for v4.

See `FRESCO-v3/docs/DATASET_PRODUCTION_SPEC.md` for the full production specification, including:
- Scope and design rationale
- Input sources and output schema
- Cross-cluster comparability requirements
- Reproducibility contract
- Extensibility model for new clusters

## Authoritative data location (Gilbreth)

| Artifact | Path |
|----------|------|
| Dataset root | `/depot/sbagchi/data/josh/FRESCO/chunks-v3/` |
| Output manifest | `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl` |
| Run metadata | `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/run_metadata.json` |
| Validation artifacts | `/depot/sbagchi/data/josh/FRESCO/chunks-v3/validation/` |

## Partitioning
The dataset is partitioned as `chunks-v3/<YYYY>/<MM>/<DD>/<HH>.parquet` with mixed clusters in a single schema per file.

## What v4 adds
FRESCO v4 does not modify the underlying dataset. Instead, v4 adds:
- **Few-shot calibration methods** that use a small number of labeled target-cluster jobs to improve cross-cluster transfer predictions.
- **New experiment configs and scripts** for sampling target labels, fitting calibration models, and evaluating few-shot strategies.
- All v4 experiments read from the same authoritative chunks-v3 dataset and derive analysis-time features using the same logic established in v3.
