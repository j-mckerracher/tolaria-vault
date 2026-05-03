# EXP-015 Baseline (Frozen Reference)

Purpose: provide a frozen, citation-friendly baseline for Phase 0 acceptance (“reproduce EXP-015 from v3 with a single command”).

## Source of truth
- Original experiment folder: `01-Projects/FRESCO-Research/Experiments/EXP-015_enhanced_validation/`
- Copied snapshot (this folder): `experiments/EXP-015_baseline/source/`

## Included artifacts (copied)
- `source/EXP015_FINAL_REPORT.md`
- `source/results/exp015_results.csv`
- `source/results/exp015_covariate_shift.json`

## Reproduction (single command)
From `01-Projects/FRESCO-v3/`:
- `python scripts\\reproduce_exp015_baseline.py --config experiments\\EXP-015_baseline\\config\\reproduce_exp015_baseline.json`

This generates provenance-rich artifacts under:
- `experiments/EXP-015_baseline/results/`
- `experiments/EXP-015_baseline/manifests/`
- `experiments/EXP-015_baseline/validation/`
- `experiments/EXP-015_baseline/logs/`

## Notes / limitations
- This is a **replay reproducer**: it regenerates the baseline artifacts from the frozen snapshot in `source/`.
- The final report references original scripts (`scripts/exp015_enhanced_validation.py`, `scripts/exp015.slurm`) and SLURM stdout/stderr, but those are not present in the snapshot, so we cannot recompute EXP-015 from raw shards here.

