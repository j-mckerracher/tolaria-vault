# EXP-044 Run Log  Regime matching on authoritative v3 with recovered hardware CPU-standard regime

**Run ID**: EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08  
**Date**: 2026-03-12

## Objective
Re-run the authoritative Anvil -> Conte overlap analysis using recovered hardware metadata and a real CPU-standard regime instead of the prior GPU-activity proxy.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Source cluster: anvil
- Target cluster: conte
- Regime: `hardware_cpu_standard`

## Code & Environment
- Script: `scripts/regime_matching.py`
- Config: `experiments/EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08/config/exp044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08.json`
- Hardware metadata source: `config/clusters.json`
- Overlap feature set:
  - `ncores`
  - `nhosts`
  - `timelimit_sec`
  - `runtime_sec`
  - `queue_time_sec`
  - `runtime_fraction`

## Notes
- `partition` is recovered from the raw `queue` field at analysis time.
- `node_memory_gb`, `node_cores`, `gpu_count_per_node`, and `node_type` are recovered from `config/clusters.json`.
- Conte queue identifiers remain anonymized, so recovered hardware metadata uses cluster-wide defaults there.

## Execution
Planned repro command:
```powershell
python scripts\regime_matching.py --config experiments\EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08\config\exp044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08.json
```

Submitted on Gilbreth:
- Final successful SLURM job: `10405058`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=8 --mem=48G`

## Outputs
- Overlap report: `experiments/EXP-044_regime_matching_authoritative_v3_hardware_cpu_standard_band_02_08/results/overlap_report.json`
- Matched indices:
  - `.../results/matched_source_indices.parquet`
  - `.../results/matched_target_indices.parquet`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files_used.json`

## Results Summary
- Job `10405058` completed successfully.
- Final cohort sizes:
  - source jobs: `12,649`
  - target jobs: `7,383`
  - source overlap jobs: `7,011`
  - target overlap jobs: `2,439`
- Overlap diagnostics:
  - domain classifier AUC: `0.9398`
  - target overlap coverage: `33.04%`
- KS statistics on the full sampled cohorts:
  - `ncores`: `0.5219`
  - `nhosts`: `0.1222`
  - `timelimit_sec`: `0.3739`
  - `runtime_sec`: `0.2690`
  - `queue_time_sec`: `0.7010`
  - `runtime_fraction`: `0.3141`
- KS statistics within the overlap band:
  - `ncores`: `0.1582`
  - `nhosts`: `0.0066`
  - `timelimit_sec`: `0.4054`
  - `runtime_sec`: `0.4079`
  - `queue_time_sec`: `0.8176`
  - `runtime_fraction`: `0.4876`
- Interpretation:
  - Recovering hardware metadata and filtering to `hardware_cpu_standard` removed Anvil GPU/high-memory jobs, but the overlap geometry remained close to EXP-042.
  - This regime definition is more defensible than the GPU-activity proxy, even though the timing distributions are still strongly mismatched inside the overlap band.
