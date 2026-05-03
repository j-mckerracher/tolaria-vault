# Seed instability diagnosis: Anvil→Conte hardware_cpu_standard / peak_memory_fraction baseline

## Scope and method

- Workstream A only; no jobs were submitted and no existing experiment artifacts were modified.
- Cohort membership came from the saved overlap artifacts `matched_indices.parquet`, `matched_source_indices.parquet`, and `matched_target_indices.parquet` for EXP-044/046/048/050.
- Feature and label values were reloaded from the authoritative manifest with the same loader/regime semantics used by `scripts\fresco_data_loader.py` and the same positive-label filter used by `scripts\model_transfer.py` (`peak_memory_fraction > 0`).
- All analysis against saved experiment artifacts was performed on Gilbreth under `/home/jmckerra/Code/FRESCO-Pipeline`; model `R^2` values below are taken from the saved local run logs for EXP-045/047/049/051.

## Executive summary

- **Primary seed-instability driver:** the matched cohorts are almost completely different across seeds before modeling. Across the union of overlap jobs, **85.1% of source jobs** and **90.6% of target jobs** appear in **only one** of the four seeds; **0.0% of source jobs** and only **0.7% of target jobs** appear in **all four** seeds.
- **Primary within-cohort mismatch:** `queue_time_sec` is the largest source-vs-target discrepancy inside the overlap band in **all 4 seeds** (KS = 0.6299 to 0.8176; mean KS = 0.7108), and it also has the largest cross-seed KS range (0.1877).
- **Label shift is real but not the main explanation for the `R^2` swing:** overlap-cohort `peak_memory_fraction` source-vs-target KS ranges from 0.3442 to 0.5548 and the source/target median ratio ranges from 1.54x to 2.39x, but those shifts do not track the observed target `R^2` collapse consistently.
- **Recommendation:** remove `queue_time_sec` from both matching and modeling for this baseline first; then simplify the remaining timing block (`timelimit_sec`, `runtime_sec`, `runtime_fraction`) rather than keeping all three raw timing variables. Separately, fix the stochastic row-group sampling so all seeds start from the same sampled job universe.

## Per-seed cohort summary

| Seed | Overlap run | Source overlap jobs | Target overlap jobs | Target overlap coverage | Domain AUC | Target transfer R^2 |
|---|---|---:|---:|---:|---:|---:|
| 1337 | `EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08` | 7,011 | 2,439 | 33.0% | 0.9398 | 0.0878 |
| 2024 | `EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024` | 2,516 | 1,652 | 26.9% | 0.9394 | -0.0346 |
| 2025 | `EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025` | 7,888 | 3,312 | 58.9% | 0.9073 | -2.1030 |
| 2026 | `EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026` | 3,433 | 2,461 | 40.4% | 0.9271 | -0.2882 |

**Interpretation:** overlap size and target coverage swing materially across seeds (1,652 to 3,312 target jobs; 26.9% to 58.9% coverage), and target `R^2` swings from **+0.0878** to **-2.1030**.

## Cohort membership overlap across seeds

| Seed pair | Source intersection | Source Jaccard | Target intersection | Target Jaccard |
|---|---:|---:|---:|---:|
| 1337 vs 2024 | 212 | 0.0228 | 198 | 0.0509 |
| 1337 vs 2025 | 0 | 0.0000 | 168 | 0.0301 |
| 1337 vs 2026 | 209 | 0.0204 | 335 | 0.0734 |
| 2024 vs 2025 | 188 | 0.0184 | 176 | 0.0368 |
| 2024 vs 2026 | 197 | 0.0342 | 438 | 0.1192 |
| 2025 vs 2026 | 2,252 | 0.2483 | 152 | 0.0270 |

**Especially low-overlap cases:**

- Source cohorts are near-disjoint for most seed pairs; the most extreme case is **1337 vs 2025 source overlap = 0 jobs (Jaccard 0.0000)**.
- Target overlap is also very weak; the lowest target Jaccard is **2025 vs 2026 = 0.0270** with only **152 shared target jobs**.
- The only comparatively less-bad source pair is **2025 vs 2026** (2,252 shared source jobs; Jaccard 0.2483), but even that is far from stable.

## Subpopulation stability across all four seeds

| Cohort | Union size | In 1 seed only | In 2 seeds | In 3 seeds | In all 4 seeds |
|---|---:|---:|---:|---:|---:|
| target | 8,748 | 90.6% (7,922) | 6.8% (597) | 1.9% (168) | 0.7% (61) |
| source | 17,978 | 85.1% (15,296) | 13.9% (2,494) | 1.0% (188) | 0.0% (0) |

**Interpretation:** seed changes are selecting substantially different jobs, not modest perturbations of the same overlap cohort.

## Feature distribution comparison inside the overlap cohorts

### Allocation features (more stable)

| Feature | Seed | Source median [p25, p75] | Target median [p25, p75] | Notes |
|---|---|---|---|---|
| `ncores` | 1337 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | Median is 1 on both sides in 3/4 seeds; only seed 2026 source p75 reaches 2. |
| `ncores` | 2024 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | Median is 1 on both sides in 3/4 seeds; only seed 2026 source p75 reaches 2. |
| `ncores` | 2025 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | Median is 1 on both sides in 3/4 seeds; only seed 2026 source p75 reaches 2. |
| `ncores` | 2026 | 1.00 [1.00, 2.00] | 1.00 [1.00, 1.00] | Median is 1 on both sides in 3/4 seeds; only seed 2026 source p75 reaches 2. |
| `nhosts` | 1337 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | Mostly identical single-node/single-core support; not a likely instability driver. |
| `nhosts` | 2024 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | Mostly identical single-node/single-core support; not a likely instability driver. |
| `nhosts` | 2025 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | Mostly identical single-node/single-core support; not a likely instability driver. |
| `nhosts` | 2026 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | Mostly identical single-node/single-core support; not a likely instability driver. |

### Timing features (stronger mismatch)

| Feature | Seed | Source median [p25, p75] | Target median [p25, p75] | Source/target median ratio |
|---|---|---|---|---:|
| `timelimit_sec` | 1337 | 345600.00 [345600.00, 345600.00] | 14400.00 [14400.00, 540000.00] | 24.000 |
| `timelimit_sec` | 2024 | 345600.00 [345600.00, 345600.00] | 14400.00 [14400.00, 720000.00] | 24.000 |
| `timelimit_sec` | 2025 | 345600.00 [345600.00, 345600.00] | 14400.00 [14400.00, 259200.00] | 24.000 |
| `timelimit_sec` | 2026 | 345600.00 [279000.00, 345600.00] | 36000.00 [14400.00, 432000.00] | 9.600 |
| `runtime_sec` | 1337 | 345617.00 [170021.00, 345621.00] | 12203.00 [6553.00, 396534.50] | 28.322 |
| `runtime_sec` | 2024 | 299076.00 [285765.00, 299178.00] | 12893.00 [7566.75, 595132.00] | 23.197 |
| `runtime_sec` | 2025 | 345609.00 [229683.75, 345616.00] | 8079.00 [1884.75, 172833.75] | 42.779 |
| `runtime_sec` | 2026 | 345608.00 [162964.00, 345609.00] | 24979.00 [8027.00, 356423.00] | 13.836 |
| `queue_time_sec` | 1337 | 28.00 [24.00, 46.00] | 1510.00 [100.00, 9856.50] | 0.019 |
| `queue_time_sec` | 2024 | 55.00 [41.75, 55.00] | 712.50 [69.00, 22091.00] | 0.077 |
| `queue_time_sec` | 2025 | 31.00 [9.00, 51.00] | 605.00 [83.00, 9614.00] | 0.051 |
| `queue_time_sec` | 2026 | 23.00 [3.00, 45.00] | 515.00 [72.00, 10245.00] | 0.045 |
| `runtime_fraction` | 1337 | 1.00 [0.56, 1.00] | 0.56 [0.46, 0.90] | 1.801 |
| `runtime_fraction` | 2024 | 0.87 [0.83, 0.87] | 0.70 [0.52, 0.89] | 1.240 |
| `runtime_fraction` | 2025 | 1.00 [0.73, 1.00] | 0.50 [0.23, 0.81] | 1.991 |
| `runtime_fraction` | 2026 | 1.00 [0.60, 1.00] | 0.76 [0.53, 1.00] | 1.322 |

**Timing-feature takeaways:**

- `queue_time_sec` remains severely shifted in every seed: source medians stay **23–55 sec**, while target medians stay **515–1,510 sec**.
- `runtime_sec`, `timelimit_sec`, and `runtime_fraction` also move meaningfully across seeds, but less uniformly than `queue_time_sec`.
- `ncores` and `nhosts` are comparatively benign; they do not explain the seed-sensitive behavior.

## Propensity score summary from saved overlap artifacts

| Seed | Source overlap propensity mean | Source overlap p50 | Target overlap propensity mean | Target overlap p50 |
|---|---:|---:|---:|---:|
| 1337 | 0.6513 | 0.7542 | 0.4314 | 0.4087 |
| 2024 | 0.6537 | 0.6923 | 0.4632 | 0.4070 |
| 2025 | 0.6337 | 0.7237 | 0.4298 | 0.4261 |
| 2026 | 0.5843 | 0.6619 | 0.4528 | 0.4388 |

**Interpretation:** all four seeds still leave visibly separated overlap propensities, consistent with the high domain AUC values and the large residual timing mismatch.

## Within-overlap KS analysis

| Seed | ncores | nhosts | timelimit_sec | runtime_sec | queue_time_sec | runtime_fraction |
|---|---:|---:|---:|---:|---:|---:|
| 1337 | 0.1582 | 0.0066 | 0.4054 | 0.4079 | 0.8176 | 0.4876 |
| 2024 | 0.1483 | 0.0024 | 0.5573 | 0.5316 | 0.6299 | 0.4068 |
| 2025 | 0.1658 | 0.0000 | 0.5861 | 0.5375 | 0.7045 | 0.5495 |
| 2026 | 0.2511 | 0.0106 | 0.4170 | 0.3701 | 0.6912 | 0.3758 |

| Feature | Mean KS across seeds | KS range across seeds | Finding |
|---|---:|---:|---|
| `queue_time_sec` | 0.7108 | 0.1877 | Highest mean KS and highest range; top KS feature in all 4 seeds. |
| `timelimit_sec` | 0.4914 | 0.1807 | Second-highest mean KS; still very large in every seed. |
| `runtime_sec` | 0.4618 | 0.1674 | Large persistent mismatch, but consistently below queue_time_sec. |
| `runtime_fraction` | 0.4549 | 0.1737 | Large persistent mismatch; cross-seed range is close to runtime_sec/timelimit_sec. |
| `ncores` | 0.1808 | 0.1028 | Moderate mismatch only; driven by rare larger Anvil jobs. |
| `nhosts` | 0.0049 | 0.0106 | Essentially matched; negligible KS. |

**Queue-time dominance test:** `queue_time_sec` ranks **#1 by mean KS**, **#1 by KS range**, and is the **largest KS feature in all four seeds**. On the feature-mismatch question alone, it is the dominant instability driver.

## Label distribution comparison (`peak_memory_fraction`, positive-label rows only)

| Seed | Source rows | Target rows | Source median | Target median | Source p90 | Target p90 | Label KS | Target transfer R^2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1337 | 7,011 | 2,435 | 0.1726 | 0.0723 | 0.2292 | 0.4506 | 0.5548 | 0.0878 |
| 2024 | 2,486 | 1,640 | 0.1910 | 0.1185 | 0.2637 | 0.4293 | 0.4391 | -0.0346 |
| 2025 | 6,241 | 3,271 | 0.2032 | 0.0942 | 0.4168 | 0.3840 | 0.4869 | -2.1030 |
| 2026 | 1,885 | 2,441 | 0.1742 | 0.1129 | 0.3858 | 0.3072 | 0.3442 | -0.2882 |

**Interpretation:** label shift is present in every seed, but it does **not** explain the `R^2` instability by itself.

- Seed **1337** has the **largest** source/target median ratio (**2.39x**) yet the **best** target `R^2` (**+0.0878**).
- Seed **2025** has another large ratio (**2.16x**) and the worst target `R^2` (**-2.1030**).
- Seeds **2024** and **2026** have smaller median ratios (**1.61x** and **1.54x**) but still produce negative target `R^2`.
- Therefore, label shift plausibly contributes to transfer difficulty, but the observed seed-to-seed failure mode is more consistent with **cohort-membership instability plus persistent timing-feature mismatch**, not with label shift alone.

## Primary root-cause findings

1. **The overlap cohorts themselves are unstable.** Different seeds are not selecting near-neighbor cohorts from the same job pool; they are selecting mostly different source and target jobs because the saved overlap runs were built from stochastic row-group sampling (`sample_n_row_groups_per_file = 24`).
2. **`queue_time_sec` is the dominant within-overlap mismatch.** It remains the largest source-vs-target discrepancy after overlap filtering in every seed and should not be treated as a stable shared-support feature for this baseline.
3. **The rest of the timing block is also problematic.** `timelimit_sec`, `runtime_sec`, and `runtime_fraction` all retain large within-overlap KS values (mean KS 0.49, 0.46, and 0.45 respectively), so queue-time removal alone may not fully solve transfer instability.
4. **Label shift is secondary.** `peak_memory_fraction` differs across clusters, but its variation does not line up cleanly with the target `R^2` swings.

## Concrete recommendation

1. **Drop `queue_time_sec` from both regime matching and model features for the next baseline.** The evidence here is strong enough to treat it as the first feature to remove, not just a feature to transform.
2. **Simplify or modify the remaining timing block.** Prefer one transformed duration-control feature (for example, log-runtime or one bounded runtime-ratio feature) instead of the current raw trio of `timelimit_sec`, `runtime_sec`, and `runtime_fraction`, which are partly redundant and remain badly mismatched.
3. **Do not interpret further seed sweeps on the current sampling setup as robust stability evidence.** Before making claims, freeze the sampled row groups/job universe once and reuse that exact cohort-construction input across seeds.
4. **Keep `ncores` and `nhosts`.** They are not the instability problem in this regime.

## Artifact paths used as evidence

- Authoritative manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Loader / regime semantics: `scripts\fresco_data_loader.py`, `scripts\model_transfer.py`
- Seed 1337 overlap artifacts: `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08/results/matched_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08/results/matched_source_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08/results/matched_target_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08/results/overlap_report.json`
- Seed 1337 model outcome log: `experiments\EXP-045_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08\EXP045_RUN_LOG.md`
- Seed 2024 overlap artifacts: `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/results/matched_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/results/matched_source_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/results/matched_target_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-046_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2024/results/overlap_report.json`
- Seed 2024 model outcome log: `experiments\EXP-047_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2024\EXP047_RUN_LOG.md`
- Seed 2025 overlap artifacts: `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/results/matched_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/results/matched_source_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/results/matched_target_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-048_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2025/results/overlap_report.json`
- Seed 2025 model outcome log: `experiments\EXP-049_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2025\EXP049_RUN_LOG.md`
- Seed 2026 overlap artifacts: `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/results/matched_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/results/matched_source_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/results/matched_target_indices.parquet`, `/home/jmckerra/Code/FRESCO-Pipeline/experiments/EXP-050_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_seed_2026/results/overlap_report.json`
- Seed 2026 model outcome log: `experiments\EXP-051_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_seed_2026\EXP051_RUN_LOG.md`

