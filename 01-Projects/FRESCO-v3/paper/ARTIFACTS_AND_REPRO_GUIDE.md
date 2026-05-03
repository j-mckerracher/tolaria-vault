# Artifact & Reproducibility Guide (for reviewers)

**Last Updated**: 2026-02-03

## What we provide
- Pipeline code at a pinned commit
- Config files for all runs
- Manifests listing all inputs and outputs
- Environment lock files (pip freeze / conda export)
- Validation reports
- Experiment result tables

## How to reproduce dataset generation
1. Checkout pipeline repo at commit <HASH>
2. Create/activate environment (use provided lock)
3. Run production command with provided config
4. Verify checks:
   - schema report matches
   - manifests match

## How to reproduce experiments
1. Run analysis scripts with provided config
2. Compare produced CSVs to provided outputs

## Minimum compute requirements
- Storage and CPU requirements documented per run
- Cluster scheduler details included
