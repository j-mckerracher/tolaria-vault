# FRESCO v4: Master Index

**Last Updated**: 2026-03-13

## Purpose
This folder contains the **required documentation** for FRESCO v4, which extends v3 zero-shot cross-cluster transfer with **few-shot calibration** methods. FRESCO v4 inherits the v3 dataset (no new production pipeline); see `FRESCO-v3/docs/` for dataset production documentation.

## Core Docs (Required)

### Dataset & Schema (inherited from v3)
1. `docs/DATASET_PRODUCTION_SPEC.md` – short reference pointing to v3 production spec
2. `docs/SCHEMA_AND_PROVENANCE.md` – v4-relevant schema fields and provenance caveats
3. `docs/DATA_QUALITY_AND_VALIDATION.md` – validation levels and acceptance criteria (inherited from v3)
4. `docs/feature_matrix.md` – safe feature set for v4 (derived from v3 EXP-039)

### Few-Shot Methodology (new in v4)
5. `docs/FEW_SHOT_METHODOLOGY.md` – core methodology: problem formulation, calibration strategies, evaluation protocol
6. `docs/WORKLOAD_TAXONOMY_AND_MATCHING.md` – regime matching context and v3 findings relevant to few-shot

### Configuration & Experiment Tracking
7. `docs/CONFIGURATION.md` – v4 config format (extends v3 with few-shot fields)
8. `docs/EXPERIMENT_LOG_TEMPLATE.md` – per-run log template with few-shot-specific sections

### Paper-Ready Documentation
9. `paper/PAPER_OUTLINE.md` – section-by-section outline (when created)
10. `paper/METHODS.md` – reproducible methods text (when created)
11. `paper/EXPERIMENTS_AND_EVAL.md` – evaluation protocol and reporting (when created)

### Research Artifacts (Examples)
12. `experiments/` – experiment run folders following EXP-XXX naming

## v3 Reference Docs (Dataset Production)
The following v3 documents remain authoritative for dataset production and are **not** duplicated here:
- `FRESCO-v3/docs/DATASET_PRODUCTION_SPEC.md` – full production specification
- `FRESCO-v3/docs/SCHEMA_AND_PROVENANCE.md` – complete canonical schema
- `FRESCO-v3/docs/DATA_QUALITY_AND_VALIDATION.md` – full validation rules
- `FRESCO-v3/docs/WORKLOAD_TAXONOMY_AND_MATCHING.md` – complete taxonomy and all EXP results
- `FRESCO-v3/docs/feature_matrix.md` – full Phase 1 feature availability matrix
- `FRESCO-v3/runbooks/PRODUCTION_RUNBOOK.md` – step-by-step operational procedure
- `FRESCO-v3/runbooks/REPRODUCIBILITY_CHECKLIST.md` – reproducibility verification
- `FRESCO-v3/docs/FRESCO_Repository_Description.pdf` – authoritative source schema

## Quick Links
- v3 master index: `../FRESCO-v3/docs/MASTER_INDEX.md`
- v3 transfer plan: `../FRESCO-v3/ZERO_SHOT_CROSS_CLUSTER_TRANSFER_PLAN.md`
