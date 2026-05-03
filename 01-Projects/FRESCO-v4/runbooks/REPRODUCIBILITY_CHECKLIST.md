# FRESCO v4 Reproducibility Checklist

## A. Code
- [ ] Pipeline & analysis code pinned to git commit (`git rev-parse HEAD`)
- [ ] No uncommitted changes (`git status` clean or diffs documented)
- [ ] v3 inherited scripts (fresco_data_loader.py, regime_matching.py) at known commit

## B. Environment
- [ ] Python version recorded
- [ ] pip freeze captured
- [ ] conda export captured
- [ ] OS and hostname recorded

## C. Data Provenance
- [ ] Input manifest path documented (chunks-v3 manifest)
- [ ] Sampling plan documented (if using frozen sampling)
- [ ] Overlap cohort source documented (regime matching experiment ID)
- [ ] Hardware metadata source: config/clusters.json version

## D. Determinism
- [ ] Random seed fixed and recorded in config
- [ ] Data sampling seed (`data_seed`) fixed and recorded in config
- [ ] Few-shot target label sampling seed documented
- [ ] Source/target split seeds documented
- [ ] Any non-deterministic operations identified

## E. Few-Shot Specific (NEW)
- [ ] N (number of target labels) explicitly recorded
- [ ] Calibration strategy documented
- [ ] Calibration set sampling method documented (stratified by label quartile, seed)
- [ ] Calibration set indices saved (which jobs were used for calibration)
- [ ] Evaluation set is strictly the complement of calibration set
- [ ] Zero-shot baseline (N=0) recorded as reference
- [ ] Target-only baseline (same N) recorded as reference
- [ ] Full-target upper bound recorded as reference

## F. Validation
- [ ] Schema checks passed
- [ ] Sanity checks passed (non-negative constraints)
- [ ] Metrics computed without NaN/Inf

## G. Paper Artifacts
- [ ] Methods reference exact config files and git commits
- [ ] Claims tied to specific experiment run IDs
- [ ] Threats to validity documented
- [ ] Reproduction instructions provided

## H. Reproduction Instructions
- [ ] Step-by-step guide to rerun each experiment
- [ ] Expected output checksums or tolerance ranges
- [ ] Compute requirements documented
