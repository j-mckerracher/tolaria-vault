# EXP-039 Run Log  Feature matrix on authoritative v3 output

**Run ID**: EXP-039_feature_matrix_authoritative_v3  
**Date**: 2026-03-11

## Objective
Measure column availability, dtype stability, and missingness on the authoritative `chunks-v3` production output instead of the local proxy snapshot.

## Inputs
- Dataset label: `chunks-v3-authoritative`
- Input manifest: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`
- Clusters: anvil / conte / stampede
- Date range: 2015-01-01 to 2023-12-31

## Code & Environment
- Script: `scripts/feature_matrix.py`
- Config: `experiments/EXP-039_feature_matrix_authoritative_v3/config/exp039_feature_matrix_authoritative_v3.json`
- Notes:
  - Reads the mixed-cluster v3 parquet and samples row groups, then collapses rows to job-level.
  - Materializes derived `value_*_{cnt,sum,max}` and runtime-derived fields at analysis time.

## Execution
Planned repro command:
```powershell
python scripts\feature_matrix.py --config experiments\EXP-039_feature_matrix_authoritative_v3\config\exp039_feature_matrix_authoritative_v3.json
```

Submitted on Gilbreth:
- Initial SLURM job: `10404577` on `a100-80gb` (`AssocGrpGRES`, cancelled)
- First training retry: `10404588` (`FAILED`)
- Final successful retry: `10404596`
- Partition/account/qos: `training` / `sbagchi` / `training`
- Resources: `--gres=gpu:1 --cpus-per-task=4 --mem=32G`

## Outputs
- Results: `experiments/EXP-039_feature_matrix_authoritative_v3/results/feature_matrix.json`
- Provenance: `.../manifests/run_metadata.json`, `.../manifests/input_files.json`
- Validation: `.../validation/python_version.txt`, `.../validation/pip_freeze.txt`

## Results Summary
- Job `10404588` failed because the first authoritative sampler implementation stopped after the first shuffled row groups instead of continuing until it found non-empty groups for the requested cluster; `anvil` therefore sampled zero rows.
- After fixing `scripts/fresco_data_loader.py`, job `10404596` completed successfully.
- Raw rows sampled:
  - anvil: `171,959`
  - conte: `85,711`
  - stampede: `225,830`
- Job rows profiled:
  - anvil: `4,622`
  - conte: `5,015`
  - stampede: `8,741`
- Column inventory on the sampled job-level frames:
  - union columns: `52`
  - intersection columns: `52`
  - safe columns at 0% missingness cutoff: `32`
- Safe columns include the shared provenance/time fields plus derived runtime columns such as `runtime_sec`, `queue_time_sec`, and `runtime_fraction`.

## Known Issues / Caveats
- Uses authoritative v3 data, but still lacks node/hardware metadata (`node_type`, `node_memory_gb`, `gpu_count_per_node`) because `clusters.json` is not available.
- Missingness and safe-column decisions are sample-based over row groups, not a full scan of every row.
