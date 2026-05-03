# Paragraph Skeleton: First Sentence of Every Paragraph

**Paper**: FRESCO v2 — Cross-Cluster Workload Comparability
**Last Updated**: 2026-03-17
**Convention**: Each entry below is the **opening sentence** of a paragraph; the rest of the paragraph would develop the idea introduced by that sentence.

---

## Abstract (single block, ~250 words)

> Cross-cluster workload comparison is essential for capacity planning, workload migration, and system procurement, yet no published study has empirically validated whether predictive models trained on one HPC cluster can generalize to another. We present FRESCO v2, a provenance-rich evolution of the FRESCO dataset that extends the original schema to 65 columns with hardware-normalized memory metrics, explicit measurement semantics, and a workload comparability framework across three clusters spanning 75 months and 20.9 million jobs. Using this dataset, we conduct a systematic 84-experiment investigation of zero-shot cross-cluster memory prediction, progressing from naive transfer (R² as low as −24), through overlap-aware regime matching (conditionally positive at R² = 0.09 but unstable across data subsets), to unsupervised domain adaptation (CORAL and quantile-output matching—both failing robustness tests). We find that even under best-case conditions—matched hardware regimes, frozen sampling plans, and overlap-aware cohort selection—zero-shot transfer does not generalize, due to fundamental domain shift in the feature-to-memory relationship across clusters. We contribute the dataset with full provenance infrastructure, a comparability framework that makes cross-cluster failures diagnosable, and reproducible evidence that should caution the community against unsupported cross-cluster transfer claims.

---

## §1. Introduction

### ¶1 — The need for cross-cluster insights
High-performance computing centers routinely make operational decisions—capacity planning, workload migration, hardware procurement—that would benefit from comparing workload behavior across clusters, yet such comparisons are rarely attempted with empirical rigor.

### ¶2 — The temptation of naive transfer
The growing availability of public HPC workload datasets, including the original FRESCO dataset covering 20.9 million jobs across three major academic clusters, naturally raises the question of whether a predictive model trained on one cluster's labeled data can generalize to another—a question the original dataset paper invited but did not itself investigate.

### ¶3 — Why naive transfer is dangerous
This assumption is empirically false: in our baseline experiments, cross-cluster memory prediction models produce R² values as low as −24, meaning they perform far worse than simply predicting the target cluster's mean—a failure driven by severe covariate shift (completely disjoint partitions and node types), conditional shift (different feature-to-memory relationships), and era shift (a 2015 CPU cluster versus a 2022 GPU/AI-era cluster).

### ¶4 — What FRESCO v1 established and where it fell short
The original FRESCO dataset demonstrated the scope and value of multi-institutional HPC operational data but provided fewer than 20 schema fields focused on collection and integration, without the metadata infrastructure required to diagnose or correct cross-cluster incompatibilities: it had no measurement semantics, no hardware context, no memory normalization, and undocumented unit inconsistencies that—as we discover in this work—produce 6–9× systematic offsets between clusters.

### ¶5 — This paper's contributions
In this paper, we present three contributions: (1) FRESCO v2, an extended dataset with 65 columns including hardware metadata, normalized memory fractions, and explicit measurement provenance; (2) a comparability framework comprising workload taxonomy, overlap-aware cohort matching, and mandatory shift diagnostics; and (3) a rigorous 84-experiment negative result demonstrating that zero-shot cross-cluster memory prediction fails even under best-case conditions.

### ¶6 — Paper roadmap
The remainder of this paper is organized as follows: §2 surveys related work on HPC workload datasets and cross-domain transfer; §3 describes the dataset evolution from v1 to v2; §4 presents our comparability framework; §5 details the experimental design; §6 presents results; §7 discusses implications; §8 addresses threats to validity; §9 describes reproducibility artifacts; and §10 concludes.

---

## §2. Background and Related Work

### ¶1 — HPC workload datasets
Several public HPC workload datasets exist—including those from the Parallel Workloads Archive, the Google cluster traces, and institutional logs from LANL, NERSC, and TACC—but none provides the multi-cluster provenance metadata needed to validate whether cross-cluster comparisons are scientifically defensible.

### ¶2 — Cross-domain transfer learning in systems
Transfer learning and domain adaptation have been applied extensively in computer vision and NLP, and more recently in systems settings such as database workload prediction and cloud resource estimation, but these applications typically assume moderate domain shift and access to large target datasets—conditions that do not hold for HPC cross-cluster scenarios.

### ¶3 — Domain adaptation methods for tabular data
For tabular data with continuous features, the most commonly applied unsupervised adaptation methods are CORAL (covariance alignment), MMD-based kernel matching, and output-space calibration; each assumes the domains share a common feature-to-label relationship up to a distributional shift in the feature space—an assumption we will test empirically.

### ¶4 — What distinguishes this work
Unlike prior dataset papers that describe schema and collection methodology, this work uses the dataset as a testbed to rigorously evaluate a specific scientific claim—that cross-cluster workload transfer is feasible—and demonstrates through controlled experimentation that it is not.

---

## §3. The FRESCO Dataset: From v1 to v2

### ¶1 — FRESCO v1 overview
The original FRESCO dataset aggregated scheduler accounting and telemetry data from three academic HPC clusters—Purdue's Anvil (July 2022–May 2023) and Conte (2015–2017), and TACC's Stampede (2013–2016)—into a single public resource comprising 20.9 million job records over 75 months.

### ¶2 — The six structural limitations of v1
Despite its scale, FRESCO v1 had structural limitations that rendered cross-cluster analysis scientifically unreliable: (1) fewer than 20 schema fields with no hardware context, (2) no documentation of measurement semantics (whether memory measurements included OS cache), (3) no unit normalization (timelimit stored in minutes for some clusters, seconds for others), (4) systematic 6–9× memory offsets between clusters due to different collection mechanisms (discovered in our analysis), (5) no explicit cluster identifier column, and (6) no provenance fields linking measurements to their collection methodology.

### ¶3 — FRESCO v2 design principles
FRESCO v2 addresses all six limitations through three design principles: every column has an explicit dtype contract enforced at write time, every measurement carries provenance metadata documenting how it was collected, and every derived metric (such as normalized memory fraction) is computed through a documented, reproducible transformation.

### ¶4 — Schema extension: 22 to 65 columns
The v2 schema extends the original fields to 65 columns organized into seven groups: identifiers (jid, cluster), allocations (ncores, nhosts, timelimit_sec), timing (submit_time, start_time, end_time, runtime_sec, queue_time_sec, runtime_fraction), memory (peak_memory_gb, node_memory_gb, peak_memory_fraction), hardware context (partition, node_type, node_cores, gpu_count_per_node, gpu_model), measurement provenance (memory_includes_cache, memory_collection_method, memory_aggregation), and workload classification (workload_regime).

### ¶5 — Hardware metadata recovery
Because the raw FRESCO shards do not contain hardware specifications, v2 recovers node-level metadata at analysis time from a structured configuration file (clusters.json) that maps each cluster's queue names to partition types, node memory, core counts, and GPU configurations—with Anvil providing full per-partition mappings and Conte and Stampede using cluster-wide defaults.

### ¶6 — Memory normalization
The central derived metric in v2 is peak_memory_fraction, computed as peak_memory_gb divided by the product of node_memory_gb and nhosts, which normalizes raw memory usage to the fraction of available node memory consumed—transforming a measure that differed by 6–9× across clusters into one that is dimensionless and architecturally comparable.

### ¶7 — Production pipeline and validation
The v2 production pipeline processes raw FRESCO shards through extraction, transformation, schema enforcement (union-by-name with explicit dtype casts), and four levels of validation: schema correctness (L0), sanity constraints (L1), cross-field consistency (L2), and distributional monitoring (L3).

---

## §4. Comparability Framework

### ¶1 — The core premise
Our central methodological premise is that HPC clusters are not independent and identically distributed: they differ in hardware, era, workload mix, and measurement methodology, and any cross-cluster insight must explicitly account for these differences rather than assume them away.

### ¶2 — Workload taxonomy
We define a shared workload taxonomy with five regimes—cpu_standard, cpu_largemem, gpu_standard, gpu_largemem, and unknown—derived from hardware signals (gpu_count_per_node, node_memory_gb, node_cores) and partition mappings, which partitions the job space into subsets that are plausibly comparable across clusters.

### ¶3 — Overlap-aware cohort selection
Within a matched regime, we use a domain classifier (logistic regression on standardized features) to score each job's propensity of belonging to the source versus target cluster, and retain only jobs falling within the [0.2, 0.8] propensity band—a conservative criterion that excludes jobs the classifier can confidently assign to one cluster, selecting only those with genuinely overlapping feature distributions.

### ¶4 — Feature selection: the safe-feature rule
Not all columns are available across all clusters: of the 52 union columns in v2, 32 have zero missingness across all three clusters, and we further restrict cross-cluster overlap features to the six that are both universally present and semantically comparable—ncores, nhosts, timelimit_sec, runtime_sec, queue_time_sec, and runtime_fraction—though our experiments will reveal that even this conservative set contains problematic features.

### ¶5 — Required shift diagnostics
Every cross-cluster comparison must report four diagnostics: the overlap coverage (percentage of target jobs retained after matching), per-feature Kolmogorov-Smirnov statistics within the overlap band, the domain classifier AUC (measuring residual separability), and the feature-by-feature distributional summaries for both the matched and unmatched populations.

### ¶6 — What this framework enables
This framework does not guarantee that cross-cluster transfer will succeed; rather, it guarantees that if transfer fails, the failure is diagnosable—the overlap report reveals which features remain mismatched, the coverage metric quantifies what fraction of the target cluster the comparison addresses, and the KS statistics pinpoint where distributional assumptions break down.

---

## §5. Experimental Design

### ¶1 — Evaluation protocols
We define four evaluation protocols of increasing ambition: E1 (within-cluster prediction using time-based holdout), E2 (cross-cluster transfer without target labels), E3 (regime-matched zero-shot transfer with overlap-aware cohorts), and E4 (unsupervised domain adaptation using unlabeled target features).

### ¶2 — Canonical split protocol
All experiments use a canonical split protocol: within each cluster, unique year-months are sorted and the last 20% form the test set, with a minimum of one month; balanced subsampling with fixed seeds prevents any single cluster from dominating pooled analyses.

### ¶3 — Model and metric choices
We use Ridge regression (α=1.0) on log1p-transformed peak_memory_fraction as the baseline model, reporting R², MAE in log space, SMAPE, signed bias, calibration slope and intercept, and bootstrap 95% confidence intervals (1,000 resamples) for all target-domain metrics.

### ¶4 — Reproducibility controls
Each experiment produces a frozen configuration file, input and output manifests, a run metadata record (including git commit hash, environment lock, and SLURM job ID), and machine-readable validation artifacts, enabling single-command replay of any result reported in this paper.

### ¶5 — Experiment progression
Our 84 experiments are organized into a progressive ablation: naive cross-cluster transfer (EXP-015), feature set variations (EXP-016–043), hardware-regime matching with repeated seeds (EXP-044–051), frozen-universe ablations with queue-time removal (EXP-062–069), cross-universe robustness tests (EXP-070–078), and domain adaptation (EXP-079–084).

---

## §6. Results: Characterizing Cross-Cluster Transfer Failure

### §6.1 Within-Cluster Baselines

#### ¶1 — Within-cluster prediction works
Within-cluster memory prediction using time-based holdout produces credible and reproducible results: Conte achieves R² = 0.646 (95% CI: [0.604, 0.685]) and Anvil achieves R² = 0.493 (95% CI: [0.446, 0.536]), establishing that the prediction target—peak_memory_fraction—is learnable given sufficient same-cluster training data.

#### ¶2 — This is the upper bound
These within-cluster results serve as upper bounds for cross-cluster transfer: any transfer result exceeding zero is meaningful, and approaching the within-cluster R² would indicate that the source cluster provides nearly as much information as local training data.

### §6.2 Naive Transfer

#### ¶1 — Naive transfer fails catastrophically
Training on Anvil and evaluating on Conte without any matching or adaptation produces R² = −9.31, while the reverse direction (Conte → Anvil) yields R² = −4.33—in both cases, the model performs dramatically worse than the trivial baseline of predicting the target cluster's mean memory usage.

#### ¶2 — Covariate shift is extreme
The failure is explained by extreme covariate shift: partitions are completely disjoint (KS = 1.00), node types are nearly disjoint (KS = 0.999), and even continuous allocation features like log_ncores show KS = 0.88—meaning the model is asked to extrapolate entirely outside its training support.

#### ¶3 — Conditional shift compounds the problem
Beyond covariate shift, the conditional relationship E[memory | features] differs between clusters: transfer models exhibit large signed biases in log space (+1.61 for Conte → Anvil, −2.31 for Anvil → Conte) and calibration slopes near zero or negative, indicating that even within overlapping feature ranges, the same features predict different memory outcomes.

### §6.3 Regime-Matched Transfer

#### ¶1 — Hardware regime matching produces the first positive result
Restricting both source and target to the cpu_standard hardware regime—jobs on CPU-only partitions with standard memory—and applying overlap-aware cohort selection with a [0.2, 0.8] propensity band yields the first positive Anvil → Conte transfer result: R² = 0.088 (95% CI: [0.056, 0.113]) on a matched cohort covering 33% of Conte's cpu_standard jobs.

#### ¶2 — The result is not stable across random seeds
However, repeating this experiment with three additional random seeds reveals that the positive result is an outlier: seed 2024 produces R² = −0.035, seed 2025 produces R² = −2.103, and seed 2026 produces R² = −0.288—all with bootstrap confidence intervals strictly below zero.

#### ¶3 — Seed instability is driven by cohort membership
Analysis of cohort overlap across seeds reveals that 85% of source jobs and 91% of target jobs appear in only one of the four seeds, with near-zero Jaccard similarity between seed pairs—indicating that the stochastic row-group sampling creates fundamentally different job populations rather than different random partitions of the same population.

### §6.4 Queue Time as a Confound

#### ¶1 — Queue time is the dominant within-overlap mismatch
Across all four seeds, queue_time_sec ranks as the #1 mismatched feature within the overlap band, with a mean KS statistic of 0.711 and KS range of 0.188—far exceeding all other features, with source cluster median queue times of 23–55 seconds versus target cluster medians of 515–1,510 seconds.

#### ¶2 — Queue time encodes cluster identity, not workload similarity
Unlike allocation features (ncores, nhosts) which describe the job itself, queue_time_sec reflects scheduler behavior, system load, and queuing policy—properties that are inherently cluster-specific and should not be used to define workload similarity.

### §6.5 Frozen-Universe Ablations

#### ¶1 — Removing queue time and freezing the universe
To isolate the effect of queue-time-driven instability, we freeze the sampled job universe (fixing which row groups are read from the raw data) and remove queue_time_sec from both the overlap and modeling feature sets, producing a deterministic cohort of 6,995 source jobs and 2,459 target jobs.

#### ¶2 — Universe 1 shows stable positive transfer
On the first frozen universe (seed 1337), all four modeling seeds produce consistently positive target R² values: 0.107, 0.110, 0.109, and 0.111, with bootstrap confidence intervals strictly above zero and target calibration slopes near 1.0—the strongest positive signal in our entire investigation.

#### ¶3 — Universe 2 fails completely
On the second frozen universe (seed 2024, different sampled rows), the same methodology produces uniformly negative results: R² = −0.064, −0.099, −0.091, and −0.006, with most bootstrap intervals strictly below zero and target slopes collapsed to 0.41–0.52.

#### ¶4 — The universes differ in overlap quality
The two frozen universes produce substantially different overlap cohorts (source Jaccard = 0.21, target Jaccard = 0.06), with the second universe showing worse residual timing mismatches: runtime_fraction KS = 0.61 (vs 0.49 in universe 1), runtime_sec KS = 0.55 (vs 0.41), and timelimit_sec KS = 0.54 (vs 0.41).

#### ¶5 — Further feature simplification makes things worse
Simplifying to runtime_sec as the only timing feature widens overlap coverage dramatically (82% on universe 1, 75% on universe 2) but degrades or destroys transfer: universe 1 drops from R² = 0.107 to 0.050, while universe 2 collapses catastrophically to R² = −1.609 with inverted predictions (negative calibration slope).

### §6.6 Domain Adaptation Attempts

#### ¶1 — CORAL adaptation fails
Applying CORAL (CORrelation ALignment) to align the source feature covariance to the target produces catastrophic results on universe 1 (R² = −46,521) and trivial changes on universe 2 (R² = −0.061 vs −0.064 unadapted), with higher regularization (λ = 10⁻³) reducing the catastrophe on universe 1 to R² = −60 but still failing entirely.

#### ¶2 — Output-space quantile matching fails
Quantile-output adaptation—mapping source predictions through a quantile transform fitted on the target prediction distribution—eliminates the catastrophic CORAL failures but flips the previously positive universe 1 result negative (R² = −0.103) and provides only marginal improvement on universe 2 (R² = −0.029 vs −0.064).

#### ¶3 — No adaptation method passes the cross-universe robustness test
Across all tested adaptation families—none, CORAL (two regularization strengths), and quantile-output—no method achieves positive R² on both frozen universes simultaneously, indicating that the transfer failure is not an artifact of a specific adaptation choice but reflects a structural incompatibility that unsupervised methods cannot resolve.

---

## §7. Discussion

### ¶1 — Why the response relationship differs
The fundamental obstacle to cross-cluster transfer is not feature-space overlap but the conditional relationship between features and memory usage: Conte's cpu_standard jobs consume a substantially lower fraction of available node memory (median peak_memory_fraction ≈ 0.07–0.09) than matched Anvil jobs (median ≈ 0.21), even after hardware normalization—a difference that cannot be explained by a simple scaling factor and likely reflects different workload compositions, software environments, and user behaviors across a seven-year hardware era gap.

### ¶2 — What overlap coverage means and doesn't mean
High overlap coverage (the fraction of target jobs retained after propensity matching) does not guarantee transfer success: our runtime-only ablation achieved 82% target coverage on universe 1 yet produced only R² = 0.050, and 75% on universe 2 with catastrophic R² = −1.61—demonstrating that coverage measures distributional similarity in feature space, not semantic validity of the feature-to-label mapping.

### ¶3 — Implications for the community
These results have direct implications for the growing body of work that implicitly or explicitly assumes cross-cluster comparability: any study that trains on one cluster's labels and evaluates on another—whether for memory prediction, runtime estimation, or failure analysis—should report the diagnostics our framework requires (overlap coverage, KS statistics, domain AUC) or risk drawing conclusions from extrapolation.

### ¶4 — Practical guidance
We recommend that cross-cluster claims be restricted to matched hardware regimes with explicit overlap reporting, that queue-time and other scheduler-specific features be excluded from comparability metrics, and that any positive cross-cluster result be validated across at least two independently sampled data subsets before being reported as stable.

### ¶5 — The negative result as a contribution
Publishing rigorous negative results protects the community from wasted effort: our 84-experiment ablation, with full reproducibility artifacts, provides a concrete lower bound on the difficulty of zero-shot cross-cluster transfer that future methods must demonstrably exceed.

---

## §8. Threats to Validity

### ¶1 — Measurement non-equivalence
The most significant threat is that memory measurements across clusters may not be semantically equivalent: Anvil's cgroups-based accounting includes OS page cache in memory totals (memory_includes_cache = true), while Conte's accounting may exclude it—a difference that our peak_memory_fraction normalization reduces but cannot fully eliminate.

### ¶2 — Temporal confounding
Conte operated from 2015–2017 and Anvil from 2022–2023, creating a seven-year gap during which HPC workloads, software stacks, and user communities evolved substantially—meaning our experiments conflate cross-cluster and cross-era effects.

### ¶3 — Hidden confounding
Unobserved factors—including application type, programming model, library versions, and institutional usage policies—likely differ between clusters and may drive memory usage patterns that no set of scheduler-observable features can capture.

### ¶4 — Selection bias from regime matching
Our overlap-aware cohort selection retains only 27–33% of target cluster jobs, and our conclusions apply only to this comparable subset; the remaining 67–73% of jobs are explicitly excluded as non-comparable, and our framework's guidance does not extend to them.

### ¶5 — Generalizability
We study a single transfer direction (Anvil → Conte) within a single hardware regime (cpu_standard) using one prediction target (peak_memory_fraction); other directions, regimes, and targets may behave differently, and our results should be interpreted as evidence of difficulty rather than impossibility.

---

## §9. Reproducibility and Artifact Evaluation

### ¶1 — What we provide
We release the complete FRESCO v2 dataset, the production pipeline code at a pinned commit, configuration files for all 84 experiments, input and output manifests for every run, environment lock files (pip freeze and conda export), and machine-readable validation reports.

### ¶2 — How to reproduce the dataset
Reproducing the v2 dataset requires checking out the pipeline repository at the specified commit, creating the conda environment from the provided lock file, and running a single production command with the provided configuration against the raw FRESCO shards on Gilbreth.

### ¶3 — How to reproduce the experiments
Each experiment can be replayed by running the corresponding analysis script (regime_matching.py or model_transfer.py) with its frozen configuration file; the frozen sampling plans and deterministic seeds ensure that the same job cohorts and train/test splits are produced regardless of execution environment.

### ¶4 — Minimum compute requirements
All experiments in this paper were executed on Purdue's Gilbreth cluster using a single NVIDIA A100-80GB GPU partition; total compute time across all 84 experiments was approximately [X] GPU-hours, and storage requirements for the full dataset plus all experiment artifacts total approximately [X] GB.

---

## §10. Conclusion

### ¶1 — Summary of contributions
We have presented FRESCO v2, a provenance-rich extension of the FRESCO dataset with 65 columns of hardware-normalized metrics and measurement semantics, a comparability framework for defensible cross-cluster insights, and an 84-experiment investigation establishing that zero-shot cross-cluster memory prediction fails even under best-case conditions.

### ¶2 — The negative result matters
The inability to transfer memory predictions from Anvil to Conte—despite matched hardware regimes, frozen sampling, and multiple adaptation strategies—is itself a contribution: it provides the first rigorous empirical evidence that cross-cluster workload transfer in HPC requires either labeled target data or fundamentally different approaches, and it cautions against the implicit assumption of cluster comparability that pervades the literature.

### ¶3 — Future work
Three directions emerge from these findings: few-shot transfer (using a small number of labeled target jobs for calibration), cross-cluster anomaly detection (flagging unusual jobs relative to their regime without requiring prediction), and multi-source generalization (training jointly on multiple clusters to learn representations that are robust to cluster-specific effects).
