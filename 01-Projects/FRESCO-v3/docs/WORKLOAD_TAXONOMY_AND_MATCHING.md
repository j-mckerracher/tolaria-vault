# Workload Taxonomy & Regime Matching (Required for Cross-Cluster Insights)

**Last Updated**: 2026-03-12

## Purpose
Enable **defensible cross-cluster insights** by ensuring we compare **like with like**.

## 1. Taxonomy
Define a shared taxonomy label `workload_regime`:
- `cpu_standard`
- `cpu_largemem`
- `gpu_standard`
- `gpu_largemem`
- `unknown`

Derivation signals:
- `gpu_count_per_node`, `gpus_allocated`, `gpu_model`
- `node_memory_gb`, `node_cores`
- `node_type`
- `partition` (cluster-specific → mapped into taxonomy)

## 2. Overlap-aware cohort builder
For any cross-cluster experiment comparing A vs B:

1. Choose feature set F.
2. Standardize continuous features.
3. Compute overlap score via domain classifier propensity:
   - train classifier to predict domain (A vs B) using F
   - define overlap as samples with P(domain=A|x) in [0.2, 0.8]
4. Evaluate models only within overlap region (primary) and outside (secondary).

## 3. Reporting requirements
Every cross-cluster claim must report:
- regime definition
- overlap coverage (% of target jobs)
- feature support diagnostics (KS stats, domain classifier AUC)
- residual bias and calibration

## 4. Non-negotiable constraint
No “global cross-cluster” claims without regime matching + overlap reporting.

## 5. Proxy-only authoritative baseline (historical)
- The authoritative v3 parquet still does **not** store `partition`, `node_type`, `node_memory_gb`, or `gpu_count_per_node`, so current regime labels remain **proxy-based** even on authoritative data.
- The current proxy is:
  - `cpu_standard := value_gpu_max <= 0` when available
  - otherwise `cpu_standard := (value_gpu_cnt <= 0) AND (value_gpu_sum <= 0)`
- Authoritative EXP-040 (alloc + perf counters) still produced severe domain separability:
  - domain AUC = `0.9962`
  - target overlap coverage = `25.94%`
- Authoritative EXP-041 then still showed very poor transfer on raw `value_memused_max`:
  - source-test `R^2 = 0.3103`
  - target `R^2 = -11.8921`

## 6. Safe-feature proxy baseline
Before hardware metadata was recovered at analysis time, the default authoritative overlap feature set used only the strict 0% missingness safe columns confirmed by Phase 1:

```text
ncores, nhosts, timelimit_sec, runtime_sec, queue_time_sec, runtime_fraction
```

Do **not** include raw performance counters or memory columns in the overlap feature set for primary transfer claims.

The authoritative safe-feature comparison pair is:
- `EXP-042_regime_matching_authoritative_v3_safe_features_band_02_08`
- `EXP-043_modeling_authoritative_v3_safe_features_band_02_08`

Results from that pair:
- EXP-042:
  - domain AUC = `0.9369`
  - target overlap coverage = `33.18%`
- EXP-043:
  - source-test `R^2 = 0.2282`
  - target `R^2 = -4.2053`

Interpretation:
- Restricting to safe overlap features helps, but it does **not** make raw `value_memused_max` transfer viable across Anvil -> Conte.
- Treat alloc+perf overlap runs such as EXP-040/041 as exploratory ablations, not the default publication path.
- Treat EXP-042/043 as the current best proxy-only baseline, not a publication-ready transfer result.

## 7. Recovered hardware-metadata path
We now recover hardware metadata at analysis time via `config/clusters.json`:
- `partition := queue`
- `node_type`, `node_cores`, `node_memory_gb`, `gpu_count_per_node`, `gpu_model` come from per-cluster defaults and known Anvil partition mappings
- Conte and Stampede queue identifiers remain anonymized, so those clusters use cluster-wide defaults
- `peak_memory_fraction := peak_memory_gb / (node_memory_gb * nhosts)`

This enables explicit hardware-based regime filters such as:
- `hardware_cpu_standard`
- `hardware_cpu_largemem`
- `hardware_gpu_standard`

## 8. Current best authoritative baseline
The first hardware-normalized comparison pair is:
- `EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08`
- `EXP-045_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08`

Results from that pair:
- EXP-044:
  - domain AUC = `0.9398`
  - target overlap coverage = `33.04%`
- EXP-045:
  - source-test `R^2 = 0.1414`
  - target `R^2 = 0.0878`
  - target bootstrap `R^2` 95% CI = `[0.0556, 0.1132]`

Interpretation:
- Recovering hardware metadata and switching to normalized `peak_memory_fraction` changed the Anvil -> Conte target result from clearly negative to modestly positive.
- This is the strongest authoritative transfer result so far, but it is still a baseline rather than a final claim because:
  - Conte and Stampede hardware metadata still rely on cluster-wide defaults,
  - Conte queue names remain anonymized,
  - memory measurement semantics still differ across clusters.

Repeated-seed validation runs then checked whether that positive split was stable:
- `EXP-046` / `EXP-047` (seed `2024`)
  - overlap AUC = `0.9394`
  - target overlap coverage = `26.92%`
  - target `R^2 = -0.0346`
  - bootstrap 95% CI = `[-0.0741, -0.0063]`
- `EXP-048` / `EXP-049` (seed `2025`)
  - overlap AUC = `0.9073`
  - target overlap coverage = `58.89%`
  - target `R^2 = -2.1030`
  - bootstrap 95% CI = `[-2.3111, -1.9280]`
- `EXP-050` / `EXP-051` (seed `2026`)
  - overlap AUC = `0.9271`
  - target overlap coverage = `40.37%`
  - target `R^2 = -0.2882`
  - bootstrap 95% CI = `[-0.3788, -0.2020]`

Updated interpretation before the frozen no-queue correction:
- EXP-045 is now best read as a promising single split, not a stable matched-regime result.
- Higher overlap coverage alone did not guarantee transfer: the seed-2025 repeat widened overlap substantially but still produced the worst target `R^2`.
- The normalized-label path remained the right direction, but the sampled authoritative baseline on its own was still too unstable for a publication claim.

Completed frozen no-queue-time follow-up (EXP-062..069):
- `EXP-062` (`experiments/EXP-062_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime/results/overlap_report.json`) nearly reproduced the original EXP-044 geometry while dropping `queue_time_sec`: domain AUC = `0.9366`, target overlap coverage = `33.31%`, source overlap = `6995 / 12649`, target overlap = `2459 / 7383`.
- The frozen sampling artifact `experiments/ANALYSIS_seed_instability/frozen_sampling_plan_exp044_hwcpu_standard_300k_24_seed1337.json` fixed the EXP-044-equivalent `300k / 24` row-group universe as 24 Anvil row groups (`286,843` raw rows -> `13,260` jobs) and 24 Conte row groups (`131,122` raw rows -> `7,383` jobs), removing the raw sampling drift diagnosed in Workstream A.
- The meaningful repeated-split comparison is `EXP-063/065/067/069` on the shared `EXP-062` overlap cohort; `EXP-064/066/068` remain provenance placeholders because the frozen plan makes Phase 2 deterministic for this design.
- `EXP-063` (`.../EXP-063.../results/metrics.json`), `EXP-065` (`.../EXP-065.../results/metrics.json`), `EXP-067` (`.../EXP-067.../results/metrics.json`), and `EXP-069` (`.../EXP-069.../results/metrics.json`) all returned positive target `R^2`: `0.1070`, `0.1099`, `0.1089`, and `0.1108`, respectively.
- All four no-queue modeling repeats also kept their bootstrap 95% intervals strictly above zero (`[0.0788, 0.1291]`, `[0.0861, 0.1351]`, `[0.0812, 0.1354]`, `[0.0804, 0.1365]`) and target slopes near `1.0` (`0.9593` to `1.0498`), so the result was stable across modeling split seeds on that first frozen cohort.
- Updated interpretation after EXP-062..069 alone: the earlier failure was not an unavoidable label-semantics collapse. Queue-time-driven overlap drift plus seed-dependent sampling drift clearly mattered, and removing `queue_time_sec` on the frozen EXP-062 universe revealed one clean positive zero-shot result.
- Important caveat: that success was only established on one frozen universe, not yet across alternate frozen universes or cluster pairs.

Second frozen-universe sensitivity check (EXP-070..074):
- `EXP-070` (`experiments/EXP-070_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_no_queuetime_plan2024/results/overlap_report.json`) reused the same no-queue feature recipe on a different fixed `300k / 24` universe (`frozen_sampling_plan_exp070_hwcpu_standard_300k_24_seed2024.json`) and produced a materially different matched cohort: domain AUC = `0.9294`, target overlap coverage = `27.66%`, source overlap = `11898 / 16680`, target overlap = `1697 / 6136`.
- Relative to EXP-062, the second frozen universe barely overlapped at the job level (`source` Jaccard = `0.2061`, `target` Jaccard = `0.0616`; see `experiments/ANALYSIS_seed_instability/exp062_vs_exp070_overlap_comparison.json`), so it is a genuine universe-robustness check rather than a replay.
- The remaining time-derived overlap mismatches worsened substantially on EXP-070: `runtime_fraction KS = 0.6093`, `runtime_sec KS = 0.5492`, and `timelimit_sec KS = 0.5416`.
- `EXP-071` through `EXP-074` all moved target transfer back to zero or negative on this second universe: target `R^2 = -0.0639`, `-0.0990`, `-0.0909`, and `-0.0060`.
- The corresponding bootstrap 95% intervals were mostly strictly negative (`[-0.1096, -0.0161]`, `[-0.1567, -0.0487]`, `[-0.1555, -0.0465]`) with the last split straddling zero (`[-0.0452, 0.0346]`), and target slopes collapsed to `0.41`-`0.52`.
- Updated interpretation after EXP-070..074: removing `queue_time_sec` and freezing the sampled universe is necessary but not sufficient. The positive no-queue result does **not** generalize across frozen sampled universes, and the remaining timing block (`timelimit_sec`, `runtime_sec`, `runtime_fraction`) is still the main instability suspect.

Runtime-sec-only follow-up (EXP-075..078):
- `EXP-075` (`experiments/EXP-075_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only/results/overlap_report.json`) pruned the timing block down to `runtime_sec` alone on the first frozen universe: domain AUC = `0.8990`, target overlap coverage = `81.69%`, source overlap = `7504 / 12649`, target overlap = `6031 / 7383`.
- `EXP-076` (`experiments/EXP-076_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only/results/metrics.json`) stayed positive on that first universe, but only weakly: target `R^2 = 0.0502` with bootstrap 95% CI `[0.0260, 0.0708]`, which is materially below the earlier `EXP-063` no-queue result (`0.1070`).
- `EXP-077` (`experiments/EXP-077_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08_runtime_sec_only_plan2024/results/overlap_report.json`) produced similarly broad overlap on the second frozen universe (AUC = `0.8987`, target coverage = `75.39%`), but the single retained timing feature became dramatically mismatched inside the overlap band (`runtime_sec KS = 0.8092`).
- `EXP-078` (`experiments/EXP-078_modeling_authoritative_v3_hardware_cpu_standard_peakmem_band_02_08_runtime_sec_only_plan2024/results/metrics.json`) then failed catastrophically on that second universe: target `R^2 = -1.6086`, bootstrap 95% CI `[-1.7662, -1.4565]`, and target slope `-0.9409`.
- `EXP-078` also exposed a label-availability asymmetry: `model_transfer.py` dropped `765 / 12526` source overlap jobs (`6.1%`) and `51 / 4626` target overlap jobs (`1.1%`) because `peak_memory_fraction` must be present and positive before training, whereas EXP-076 kept all `7504` first-universe source overlap jobs and dropped only `34 / 6031` target overlap jobs (`0.56%`) at the same filter. That means the EXP-076 vs. EXP-078 comparison still points to a failed timing-only fix, but it should be read with an explicit label-filter caveat rather than as a perfectly like-for-like source-cohort comparison.
- Updated interpretation after EXP-075..078: further timing-only pruning is **not** the rescue path. Broad overlap coverage alone can still be semantically broken, and reducing the feature set to `runtime_sec` alone made the second-universe transfer substantially worse rather than better even before considering the extra label-filter asymmetry.
A denser-sampling stabilization attempt then tested whether the instability was mainly a row-group sampling artifact:
- `EXP-052` / `EXP-053` (seed `1337`, `max_rows=600000`, `sample_n_row_groups_per_file=128`)
  - overlap AUC = `0.9378`
  - target overlap coverage = `37.36%`
  - target `R^2 = -0.8817`
  - bootstrap 95% CI = `[-0.9372, -0.8255]`
- `EXP-054` / `EXP-055` (seed `2024`, same dense-sampling controls)
  - overlap AUC = `0.9536`
  - target overlap coverage = `24.25%`
  - target `R^2 = -0.1047`
  - bootstrap 95% CI = `[-0.1272, -0.0881]`

Dense-sampling interpretation:
- Increasing the sample depth alone did not stabilize the normalized baseline.
- On the original positive seed (`1337`), denser sampling actually pushed the target result decisively negative.
- That makes it unlikely that the earlier instability was only a 300k/24-row-group sampling artifact.

An alloc-only + Huber diagnosis then tested whether the remaining problem was still coming from timing-feature mismatch:
- `EXP-056` / `EXP-057` (seed `1337`, overlap/model features = `ncores`, `nhosts`, `timelimit_sec`)
  - overlap AUC = `0.8571`
  - target overlap coverage = `82.52%`
  - target `R^2 = -0.6492`
  - bootstrap 95% CI = `[-0.6831, -0.6182]`
- `EXP-058` / `EXP-059` (seed `2024`, same alloc-only + Huber design)
  - overlap AUC = `0.8607`
  - target overlap coverage = `83.03%`
  - target `R^2 = -1.4949`
  - bootstrap 95% CI = `[-1.5563, -1.4371]`

Alloc-only diagnosis interpretation:
- Simplifying the overlap feature set did reduce separability and dramatically widen target coverage, but it also collapsed source holdout signal (`source-test R^2` near `0`).
- Within-overlap `timelimit_sec` mismatch remained large (`KS ≈ 0.60`) even after removing queue and runtime-derived features.
- The tracked Huber runs therefore suggest the remaining failure is not just a queue-time artifact; the cross-cluster response relationship for normalized memory is still badly misspecified.

Post-hoc label-semantics diagnosis on the saved prediction artifacts then clarified the failure mode:
- On the dense alloc-only runs, the source-test median `peak_memory_fraction` stayed near `0.205`, while the true Conte target median was much lower (`0.074` for seed `1337`, `0.086` for seed `2024`).
- The alloc-only Huber model still predicted source-like target medians (`0.209` and `0.259`), so the transfer failure was dominated by source-centered prediction collapse rather than by overlap scarcity alone.
- A simple hidden-denominator correction did **not** explain the error: applying the expected `log(256 / 64) = log(4)` node-memory shift made target `R^2` dramatically worse.
- The positive single-split baseline (`EXP-045`) still showed some target calibration (`slope ≈ 0.90`) with the richer timing feature set, while the dense runs compressed target predictions into a narrow source-like band.

Label-semantics interpretation:
- Conte hardware CPU-standard jobs occupy a substantially lower normalized-memory median than the matched Anvil source jobs, even when they remain inside the overlap band.
- The current dense alloc-only model is too weak to learn that lower-median target regime, so it defaults toward a source-like prediction level.
- The next corrective experiment should therefore **decouple Phase 2 and Phase 3 feature sets**: keep safer overlap features if needed, but restore richer modeling features to test whether the low-median Conte label regime is actually predictable.

A decoupled-feature follow-up then tested that hypothesis directly:
- `EXP-060` (seed `1337`, alloc-only overlap from `EXP-056`, Phase 3 restored to the full safe timing feature set with Ridge)
  - source-test `R^2 = 0.0121`
  - target `R^2 = -1.5721`
  - bootstrap 95% CI = `[-1.6360, -1.5091]`
  - target slope = `-1.5997`
- `EXP-061` (seed `2024`, alloc-only overlap from `EXP-058`, same decoupled Phase 3 design)
  - source-test `R^2 = 0.0359`
  - target `R^2 = -0.8824`
  - bootstrap 95% CI = `[-0.9218, -0.8433]`
  - target slope = `-0.4331`

Decoupled-feature interpretation:
- Restoring the richer timing features did recover modest positive source holdout signal, so Phase 3 feature richness does matter.
- But both target slopes stayed negative and both target intervals remained fully below zero, so decoupling overlap and modeling features alone is still not enough.
- The remaining issue now looks more like unresolved domain shift inside the feature geometry than simple overlap scarcity or an underpowered source model.
## 9. Immediate next requirement
The immediate next requirement is now to **decide whether the adaptation search should stop here or justify a fundamentally new branch before extending to new cluster pairs**:
- `EXP-075..078` tested the cleanest remaining timing-only simplification that the current scripts support without code changes, and it still failed the cross-universe robustness test badly.
- The first frozen universe stayed weakly positive, but the second frozen universe became dramatically worse, which means further timing-only pruning is no longer the most defensible next branch.
- `EXP-079` and `EXP-080` executed that first explicit-adaptation branch by reusing the stronger five-feature no-queue model space from `EXP-063/071`, keeping the frozen `EXP-062` and `EXP-070` overlap cohorts fixed, and turning on CORAL adaptation in Phase 3 only.
- `EXP-079` then failed catastrophically on the previously positive first frozen universe (`target R^2 = -46520.6724`) even though source holdout signal stayed healthy (`source-test R^2 = 0.2081`), while target median absolute log error remained small (`mdae_log = 0.0816`). That combination strongly suggests a small number of extreme target failures or numerical outliers rather than a clean global calibration shift.
- `EXP-080` did not rescue the harder universe either: target `R^2 = -0.0613` with bootstrap CI `[-0.1066, -0.0139]`, which is only a trivial change from the non-adapted `EXP-071` baseline (`-0.0639`).
- `EXP-081` and `EXP-082` then completed that regularization-sensitivity branch. Raising CORAL regularization from `1e-6` to `1e-3` reduced the magnitude of the universe-1 blow-up (`-46520.6724 -> -59.6547`) but still left it catastrophically negative with target slope near zero (`0.0091`), while the second universe stayed essentially unchanged (`-0.0613 -> -0.0633`).
- `EXP-083` and `EXP-084` then executed that output-space branch on the same frozen cohorts. `EXP-083` removed the catastrophic CORAL failure mode on the first universe, but it still turned the previously positive `EXP-063` result negative (`+0.1070 -> -0.1026`) even though target slope remained nonzero (`0.8099`).
- `EXP-084` improved the harder second universe relative to both the non-adapted baseline (`-0.0639 -> -0.0285`) and the CORAL retries (`-0.0613` and `-0.0633`), and target slope improved from `0.4456` to `0.6150`, but its bootstrap interval still remained fully below zero.
- The current evidence therefore says that none of the tested zero-label families (`none`, CORAL, or direct `quantile_output`) is robust across both frozen universes.
- The most defensible next step is to stop at the negative result unless there is a strong reason to implement a substantially different adaptation family with explicit shrinkage or guardrails; simple parameter sweeps are no longer the right use of Gilbreth time.
- Keep the measurement-semantics caveat explicit in any final interpretation of this negative result.
