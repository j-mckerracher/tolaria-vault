# EXP-042 Run Log  Regime matching on authoritative v3 with safe features

**Run ID**: EXP-042_regime_matching_authoritative_v3_safe_features_band_02_08  
**Date**: 2026-03-12

## Objective
Re-run the authoritative Anvil -> Conte overlap analysis using only the strict 0% missingness safe features from Phase 1.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Source cluster: anvil
- Target cluster: conte
- Regime: `cpu_standard`

## Code & Environment
- Script: `scripts/regime_matching.py`
- Config: `experiments/EXP-042_regime_matching_authoritative_v3_safe_features_band_02_08/config/exp042_regime_matching_authoritative_v3_safe_features_band_02_08.json`
- Safe feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`

## Execution
Planned repro command:
```powershell
python scripts\regime_matching.py --config experiments\EXP-042_regime_matching_authoritative_v3_safe_features_band_02_08\config\exp042_regime_matching_authoritative_v3_safe_features_band_02_08.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10404961`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Overlap report: `experiments/EXP-042_regime_matching_authoritative_v3_safe_features_band_02_08/results/overlap_report.json`
- Matched indices:
  - `.../results/matched_source_indices.parquet`
  - `.../results/matched_target_indices.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10404961` completed successfully.
- Final cohort sizes:
  - source jobs: `13,220`
  - target jobs: `7,383`
  - source overlap jobs: `7,189`
  - target overlap jobs: `2,450`
- Overlap diagnostics:
  - domain classifier AUC: `0.9369`
  - target overlap coverage: `33.18%`
- KS statistics on the full sampled cohorts:
  - `ncores`: `0.5211`
  - `nhosts`: `0.1245`
  - `timelimit_sec`: `0.3739`
  - `runtime_sec`: `0.2728`
  - `queue_time_sec`: `0.6870`
  - `runtime_fraction`: `0.3114`
- KS statistics within the overlap band:
  - `ncores`: `0.1559`
  - `nhosts`: `0.0074`
  - `timelimit_sec`: `0.4035`
  - `runtime_sec`: `0.4052`
  - `queue_time_sec`: `0.8083`
  - `runtime_fraction`: `0.4709`
- Interpretation:
  - Restricting overlap to the strict safe-feature set improved separability relative to EXP-040 (`AUC 0.9962 -> 0.9369`) and increased target overlap coverage (`25.94% -> 33.18%`).
  - Even so, the overlap region still exhibits strong timing-distribution drift, especially for `queue_time_sec`, so this remains only a partially matched proxy regime.

## Known Issues / Caveats
- Regime is still proxy-based because the authoritative parquet still does not materialize `partition`, `node_type`, `node_memory_gb`, or `gpu_count_per_node`.
- This run is intended to test whether removing raw performance counters from the overlap feature set reduces domain separability relative to EXP-040.
