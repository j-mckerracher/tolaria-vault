# FRESCO v3: Master Index

**Last Updated**: 2026-03-13

## Purpose
This folder contains the **required documentation** to (1) produce the FRESCO v3 dataset and (2) publish a paper describing the process.

## Core Docs (Required)

### Dataset Production
1. `docs/DATASET_PRODUCTION_SPEC.md` – what v3 is, outputs, guarantees, and invariants
2. `runbooks/PRODUCTION_RUNBOOK.md` – step-by-step operational procedure
3. `runbooks/REPRODUCIBILITY_CHECKLIST.md` – what must be logged + verified
4. `docs/FRESCO_Repository_Description.pdf` – authoritative source schema (copied from Gilbreth)
5. `docs/SCHEMA_AND_PROVENANCE.md` – schema, dtype stability rules, provenance columns
6. `docs/DATA_QUALITY_AND_VALIDATION.md` – validation rules + known caveats
7. `docs/WORKLOAD_TAXONOMY_AND_MATCHING.md` – how cross-cluster comparisons are made defensible
8. `docs/CONFIGURATION.md` – config file formats, parameters, and defaults

### Paper-Ready Documentation
9. `paper/PAPER_OUTLINE.md` – section-by-section outline + claims we can defend
10. `paper/METHODS.md` – reproducible methods text (draftable into a paper)
11. `paper/EXPERIMENTS_AND_EVAL.md` – evaluation protocol, experiments, and reporting requirements
12. `paper/THREATS_TO_VALIDITY.md` – limitations (covariate shift, measurement equivalence)
13. `paper/ARTIFACTS_AND_REPRO_GUIDE.md` – how reviewers reproduce results

### Research Artifacts (Examples)
14. `docs/EXPERIMENT_LOG_TEMPLATE.md` – template for each experiment/production run
15. `experiments/EXP-015_baseline/` – frozen baseline reference + single-command replay reproducer
16. `experiments/EXP-016_feature_matrix/` – Phase 1 run folder (config/manifests/validation/logs/results)
17. `docs/feature_matrix.md` – Phase 1 feature availability matrix (EXP-016)
18. `experiments/EXP-017_regime_matching/` – Phase 2 overlap diagnostics + matched cohort indices (local proxy)
19. `experiments/EXP-018_regime_matching_alloc_only/` – Phase 2 sensitivity: allocations-only overlap
20. `docs/regime_matching.md` – Phase 2 summary (EXP-017)
21. `experiments/EXP-019_modeling_alloc_only/` – Phase 3 baseline transfer model (proxy label, allocations-only)
22. `experiments/EXP-020_regime_matching_alloc_perf_nomem/` – Phase 2 ablation: alloc+perf overlap (job-level, no memused)
23. `experiments/EXP-021_modeling_alloc_perf_nomem/` – Phase 3 ablation: alloc+perf transfer (job-level, no memused)
24. `experiments/EXP-022_regime_matching_alloc_only_joblevel/` – Phase 2 rerun: allocations-only overlap (job-level)
25. `experiments/EXP-023_modeling_alloc_only_joblevel/` – Phase 3 rerun: allocations-only transfer (job-level)
26. `experiments/EXP-024_regime_matching_alloc_perf_nomem_band_01_09/` – Phase 2 ablation: alloc+perf overlap (job-level, no memused, overlap band [0.1,0.9])
27. `experiments/EXP-025_modeling_alloc_perf_nomem_band_01_09/` – Phase 3 ablation: alloc+perf transfer (job-level, no memused, overlap band [0.1,0.9])
28. `experiments/EXP-026_modeling_alloc_perf_nomem_band_01_09_huber/` – Phase 3 ablation: robust regression (HuberRegressor) rerun on EXP-024 cohorts
29. `experiments/EXP-027_modeling_alloc_perf_nomem_band_01_09_coral/` – Phase 4 ablation: CORAL adaptation baseline on EXP-024 cohorts
30. `experiments/EXP-028_modeling_alloc_perf_nomem_band_01_09_no_adapt/` – Phase 5 ablation: no-adaptation baseline on EXP-024 cohorts
31. `experiments/EXP-029_regime_matching_alloc_perf_nomem_band_005_095/` – Phase 5 overlap sensitivity: band [0.05,0.95]
32. `experiments/EXP-030_modeling_alloc_perf_nomem_band_005_095/` – Phase 5 overlap sensitivity: modeling on band [0.05,0.95]
33. `experiments/EXP-031_regime_matching_alloc_perf_nomem_band_02_08/` – Phase 5 overlap sensitivity: band [0.2,0.8]
34. `experiments/EXP-032_modeling_alloc_perf_nomem_band_02_08/` – Phase 5 overlap sensitivity: modeling on band [0.2,0.8]
35. `experiments/EXP-033_regime_matching_conte_to_stampede_band_02_08/` – Phase 5 single-month pair: Conte→Stampede overlap
36. `experiments/EXP-034_modeling_conte_to_stampede_band_02_08/` – Phase 5 single-month pair: Conte→Stampede modeling
37. `experiments/EXP-035_regime_matching_stampede_to_anvil_band_02_08/` – Phase 5 single-month pair: Stampede→Anvil overlap
38. `experiments/EXP-036_modeling_stampede_to_anvil_band_02_08/` – Phase 5 single-month pair: Stampede→Anvil modeling
39. `experiments/EXP-037_regime_matching_anvil_to_stampede_band_02_08/` – Phase 5 single-month pair: Anvil→Stampede overlap
40. `experiments/EXP-038_modeling_anvil_to_stampede_band_02_08/` – Phase 5 single-month pair: Anvil→Stampede modeling
41. `experiments/EXP-079_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral/` – authoritative CORAL adaptation model on the first frozen no-queue universe
42. `experiments/EXP-080_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_plan2024/` – authoritative CORAL adaptation model on the second frozen no-queue universe
43. `experiments/EXP-081_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3/` – higher-regularization CORAL sensitivity model on the first frozen no-queue universe
44. `experiments/EXP-082_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_coral_reg1e3_plan2024/` – higher-regularization CORAL sensitivity model on the second frozen no-queue universe
45. `experiments/EXP-083_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output/` – authoritative quantile-output adaptation model on the first frozen no-queue universe
46. `experiments/EXP-084_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_no_queuetime_quantile_output_plan2024/` – authoritative quantile-output adaptation model on the second frozen no-queue universe

## Quick Links
- Planning: `../ZERO_SHOT_CROSS_CLUSTER_TRANSFER_PLAN.md`
