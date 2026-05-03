# Reproducibility Checklist (Publication Required)

**Last Updated**: 2026-02-03

## A. Code
- [ ] Pipeline code pinned to commit hash
- [ ] Analysis code pinned to commit hash
- [ ] No uncommitted diffs OR diffs saved as artifact

## B. Environment
- [ ] Python version recorded
- [ ] OS/host recorded
- [ ] `pip freeze` saved
- [ ] `conda env export` saved (if conda)

## C. Data provenance
- [ ] Input root path recorded
- [ ] Date ranges recorded
- [ ] List of input shards processed (manifest)
- [ ] List of output shards produced (manifest)

## D. Determinism
- [ ] Random seeds fixed
- [ ] Sampling procedure documented
- [ ] Any nondeterministic steps identified

## E. Validation
- [ ] Schema report saved
- [ ] Dtype report saved
- [ ] Missingness report saved
- [ ] Sanity checks saved

## F. Paper artifacts
- [ ] Methods text references exact configs and commits
- [ ] Claims tie to specific experiments/runs
- [ ] Threats-to-validity documented

## G. Reproduction instructions
- [ ] Step-by-step reproduction guide written
- [ ] Expected outputs and checksums described
