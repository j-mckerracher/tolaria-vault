# EXP-040 Run Log  Regime matching on authoritative v3 output

**Run ID**: EXP-040_regime_matching_authoritative_v3_band_02_08  
**Date**: 2026-03-11

## Objective
Re-run the Anvil -> Conte overlap analysis on authoritative `chunks-v3` data using sampled, job-level aggregates derived from the production parquet.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Source cluster: anvil
- Target cluster: conte
- Regime: `cpu_standard`

## Code & Environment
- Script: `scripts/regime_matching.py`
- Config: `experiments/EXP-040_regime_matching_authoritative_v3_band_02_08/config/exp040_regime_matching_authoritative_v3_band_02_08.json`
- Feature set:
  - `ncores`, `timelimit_sec`, `runtime_sec`, `queue_time_sec`
  - `value_block_cnt`, `value_block_sum`
  - `value_cpuuser_cnt`, `value_cpuuser_sum`
  - `value_gpu_cnt`, `value_gpu_sum`
  - `value_nfs_cnt`, `value_nfs_sum`

## Execution
Planned repro command:
```powershell
python scripts\regime_matching.py --config experiments\EXP-040_regime_matching_authoritative_v3_band_02_08\config\exp040_regime_matching_authoritative_v3_band_02_08.json
```

Submitted on Gilbreth:
- Initial SLURM job: `10404578` on `a100-80gb` (`AssocGrpGRES`, cancelled)
- First training retry: `10404589` (`COMPLETED`, but invalid due pre-fix undersampling)
- Final successful retry: `10404597`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=4 --mem=32G`

## Outputs
- Overlap report: `experiments/EXP-040_regime_matching_authoritative_v3_band_02_08/results/overlap_report.json`
- Matched indices:
  - `.../results/matched_source_indices.parquet`
  - `.../results/matched_target_indices.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10404589` completed but used the pre-fix sampler, leaving only `39` source jobs and `2` overlap source jobs; those outputs were not used.
- After fixing `scripts/fresco_data_loader.py`, job `10404597` completed successfully.
- Sampled job rows after regime filtering:
  - source (anvil): `13,220`
  - target (conte): `7,383`
- Overlap cohorts:
  - matched source: `4,732`
  - matched target: `1,915`
  - target overlap coverage: `25.94%`
- Domain classifier AUC on the sampled regime frame: `0.9962`, so the two clusters remain highly separable even inside this activity-based overlap slice.
- Overlap KS remains modest for `ncores` (`0.1052`) but still large for several scheduler/runtime features, especially `queue_time_sec` (`0.8086`), `timelimit_sec` (`0.5758`), and `runtime_sec` (`0.5057`).

## Known Issues / Caveats
- Regime is still an activity-based proxy (`value_gpu_max<=0` or count/sum fallback), not the full taxonomy intended in `docs/WORKLOAD_TAXONOMY_AND_MATCHING.md`.
- Uses authoritative v3 data but only sampled row groups, not the full distribution.
