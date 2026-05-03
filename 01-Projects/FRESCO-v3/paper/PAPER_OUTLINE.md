# Paper Outline: FRESCO v2 — Cross-Cluster Workload Comparability

**Last Updated**: 2026-03-17

---

## Title (Working)

**Beyond Unified Schemas: Why Zero-Shot Cross-Cluster Workload Transfer Fails and What It Takes to Make HPC Comparisons Defensible**

Alternative titles:
- FRESCO v2: A Provenance-Rich Dataset and 84-Experiment Investigation of Cross-Cluster Workload Transfer
- Making Cross-Cluster HPC Insights Defensible: A Dataset, Framework, and Rigorous Negative Result

---

## Thesis Statement

Cross-cluster workload comparison requires far more than a unified schema. Using a new provenance-rich version of the FRESCO dataset—extending the original ~19 schema fields to 65 columns with hardware-normalized memory metrics, and explicit measurement semantics across three HPC clusters spanning 75 months and 20.9 million jobs—we systematically investigate zero-shot cross-cluster memory prediction through 84 controlled experiments covering feature ablations, overlap-aware regime matching, and unsupervised domain adaptation. We find that even under best-case conditions—matched hardware regimes, frozen sampling plans, and overlap-aware cohort selection—zero-shot transfer remains unstable across data subsets and fails to generalize, due to fundamental domain shift in the response relationship that cannot be resolved by feature engineering or adaptation alone. This negative result, rigorously documented with full reproducibility artifacts, provides the first empirical evidence that defensible cross-cluster insights require explicit comparability frameworks rather than naive model transfer, and we contribute both the dataset and the framework to enable future work.

## Expanded Thesis Argument

The HPC community increasingly needs cross-cluster insights—for capacity planning, workload migration, and system procurement—but the published literature treats clusters as comparable without empirically validating that assumption. The original FRESCO dataset (v1) demonstrated the scope of available multi-cluster data and invited cross-cluster analysis, but as a dataset description paper it did not attempt such analysis itself, and it lacked the metadata infrastructure needed to test whether cross-cluster transfer was scientifically defensible: it had fewer than 20 schema fields, no measurement semantics, no hardware context, no memory normalization, and undocumented unit inconsistencies.

This paper presents FRESCO v2, which resolves those structural limitations, and then uses the improved dataset to answer the question v1 raised but could not address: *can a memory prediction model trained on one cluster generalize to another?* Through a systematic 84-experiment investigation—progressing from naive transfer (catastrophic: R² = −24 to −9), through regime matching (conditional: R² = +0.09 but unstable across seeds), to frozen-universe ablations and domain adaptation (CORAL, quantile-output—all failing cross-universe robustness)—we establish that the answer is *no*, not because the data is inadequate but because the clusters represent fundamentally different workload domains. The contribution is threefold: (1) the dataset itself, with provenance infrastructure absent from v1, (2) a comparability framework (workload taxonomy + overlap-aware matching + shift diagnostics) that makes failures diagnosable, and (3) rigorous evidence—with full experiment artifacts—that should discourage the community from making unsupported cross-cluster transfer claims.

---

## Paper Structure (10 sections, targeting 10–12 pages)

### §1. Introduction (1.5 pages)
- The need for cross-cluster workload insights in HPC operations
- Why naive cross-cluster transfer is tempting but dangerous
- What FRESCO v1 established and where it fell short
- Contributions of this paper (dataset, framework, negative result)
- Paper roadmap

### §2. Background and Related Work (1 page)
- HPC workload datasets (prior art)
- Cross-cluster and cross-domain transfer learning in systems
- Domain adaptation methods relevant to tabular workload data
- What distinguishes this work from prior dataset papers

### §3. The FRESCO Dataset: From v1 to v2 (1.5 pages)
- v1 recap: 20.9M jobs, 3 clusters (Conte 2015–2017, Anvil 07/2022–05/2023, Stampede 2013–2016), 75 months, ~19 schema fields, 6 performance metrics
- v1 was a dataset description paper: it invited cross-cluster analysis but did not attempt it
- v1 limitations discovered in our analysis: missing metadata, unit inconsistencies, 6–9× memory offsets, no measurement semantics
- v2 design: 65 columns, hardware metadata recovery, memory normalization (peak_memory_fraction), provenance fields
- Canonical schema and dtype stability
- Production pipeline and validation levels (L0–L3)

### §4. Comparability Framework (1.5 pages)
- Workload taxonomy (cpu_standard, cpu_largemem, gpu_standard, gpu_largemem, unknown)
- Overlap-aware cohort selection (domain classifier propensity, [0.2, 0.8] band)
- Required diagnostics: coverage, KS statistics, domain classifier AUC
- Shift reporting requirements for any cross-cluster claim
- The "safe feature" rule: 0% cross-cluster missingness requirement

### §5. Experimental Design (1 page)
- Evaluation protocol: within-cluster (E1), cross-cluster (E2), regime-matched (E3), adaptation (E4)
- Canonical split protocol (time-based holdout, balanced subsampling, fixed seeds)
- Metrics: R², MAE, bias, calibration slope, bootstrap CIs
- Reproducibility controls: frozen sampling plans, manifests, environment locks

### §6. Results: Characterizing Cross-Cluster Transfer Failure (2 pages)
- **§6.1 Within-cluster baselines** (Conte R²=0.646, Anvil R²=0.493 — transfer is meaningful to attempt)
- **§6.2 Naive transfer** (R² = −24 to −9; covariate shift: partition KS=1.0, node_type KS=0.999)
- **§6.3 Regime-matched transfer** (hardware CPU-standard: first positive R²=0.088, but seed instability)
- **§6.4 Seed instability diagnosis** (85% source / 91% target jobs appear in only 1 of 4 seeds; queue_time_sec is dominant mismatch)
- **§6.5 Frozen-universe ablations** (no-queue-time: R²=+0.107 on universe 1, R²=−0.064 on universe 2; runtime-only: catastrophic on universe 2)
- **§6.6 Adaptation attempts** (CORAL: catastrophic or trivial; quantile-output: still negative; none robust across universes)

### §7. Discussion (1 page)
- Why the response relationship differs (measurement semantics, hardware era, workload composition)
- What overlap coverage means and doesn't mean
- Implications for the community: when can you compare clusters?
- Practical guidance: what comparisons are defensible

### §8. Threats to Validity (0.5 pages)
- Measurement non-equivalence (cgroups vs RSS vs accounting)
- Temporal confounding (Conte 2015 vs Anvil 2022)
- Hidden confounding (application type, user behavior, policy)
- Selection bias from regime matching (only ~33% of target covered)
- Generalizability (two clusters, one direction)

### §9. Reproducibility and Artifact Evaluation (0.5 pages)
- Dataset availability (FRESCO v2 on Gilbreth depot + public release plan)
- All 84 experiment configs, manifests, and result artifacts
- Environment locks and pipeline code at pinned commits
- Single-command replay for key experiments

### §10. Conclusion (0.5 pages)
- Summary of contributions
- The negative result as a contribution
- Future work: few-shot transfer, anomaly detection, multi-source generalization

---

## Key Evidence Mapping

| Paper claim | Supporting experiments | Key metric |
|---|---|---|
| v1 cross-cluster transfer fails catastrophically | EXP-015 | R² = −24 to −9 |
| Within-cluster prediction is viable | EXP-015 | Conte R²=0.646, Anvil R²=0.493 |
| Hardware regime matching yields conditional positive | EXP-044/045 | R²=0.088, CI=[0.056, 0.113] |
| Positive result is seed-unstable | EXP-046–051 | 3 of 4 seeds negative |
| Queue_time_sec is dominant mismatch | ANALYSIS_seed_instability | Mean KS=0.711, #1 in all seeds |
| Removing queue_time helps one universe | EXP-062/063 | R²=+0.107 |
| ...but not the other | EXP-070/071 | R²=−0.064 |
| Dense sampling doesn't help | EXP-052–055 | Positive seed → R²=−0.88 |
| Feature simplification doesn't help | EXP-056–061 | All negative |
| CORAL adaptation fails | EXP-079–082 | Catastrophic or trivial |
| Quantile-output adaptation fails | EXP-083/084 | Still negative |

---

## Key Facts from v1 Paper (verified against source)
- **Full title**: "Fresco: A Public Multi-Institutional Dataset for Understanding HPC System Behavior and Dependability"
- **Venue**: PEARC '25 (Practice and Experience in Advanced Research Computing), July 2025, Columbus, OH
- **Authors**: Joshua Stephen McKerracher, Preeti Mukherjee, Rajesh Kalyanam, Saurabh Bagchi (all Purdue)
- **DOI**: 10.1145/3708035.3736090
- **Format**: 6-page dataset description paper
- **Clusters**: Conte (2015–2017), Anvil (07/2022–05/2023), Stampede (2013–2016)
- **Scale**: 20.9 million jobs, 75 months
- **Schema**: ~19 fields in 5 categories (temporal, resource allocation, execution context, identification, performance metrics)
- **Six performance metrics**: CPU usage, GPU usage, memory usage, memory-minus-diskcache, NFS, block I/O
- **v1 scope**: Dataset collection, integration, and access; does NOT attempt cross-cluster prediction or claim comparability
- **v1 does not include**: measurement semantics, hardware context (node_memory_gb, node_type), memory normalization, unit documentation, or a comparability framework

### Important framing note
v1 is a dataset paper that *invites* cross-cluster analysis. It does not itself make transfer claims. Our v2 paper is the first to empirically test whether cross-cluster comparison is feasible and to demonstrate that it is not (in the zero-shot setting).
