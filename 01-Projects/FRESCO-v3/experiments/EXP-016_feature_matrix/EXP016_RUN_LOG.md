# EXP-016 Feature Availability Matrix — Run Log

**Run ID**: EXP-016_feature_matrix  
**Date**: 2026-02-03  
**Owner**: jmckerra

## Objective
Compute a feature availability/missingness + dtype drift matrix across clusters to identify a conservative set of **cross-cluster-safe** features.

## Inputs
- Local parquet snapshot (not `/depot/...`):
  - `..\FRESCO-Research\Experiments\EXP-001_baseline_statistical_analysis\results\tmp\job_partials\start_year=2023\start_month=06\source_token=NONE\*.parquet` (Anvil proxy)
  - `..\FRESCO-Research\Experiments\EXP-001_baseline_statistical_analysis\results\tmp\job_partials\start_year=2016\start_month=07\source_token=C\*.parquet` (Conte proxy)
  - `..\FRESCO-Research\Experiments\EXP-001_baseline_statistical_analysis\results\tmp\job_partials\start_year=2016\start_month=10\source_token=S\*.parquet` (Stampede proxy)

Sampling:
- 20 files per cluster (`random_seed=1337`), as recorded in config.

## Code & Environment
- Script: `scripts\feature_matrix.py`
- Config: `experiments\EXP-016_feature_matrix\config\exp016_feature_matrix.json`
- Environment capture:
  - `experiments\EXP-016_feature_matrix\validation\python_version.txt`
  - `experiments\EXP-016_feature_matrix\validation\pip_freeze.txt`

## Execution
Command:
```powershell
python scripts\feature_matrix.py --config experiments\EXP-016_feature_matrix\config\exp016_feature_matrix.json
```

Log:
- `experiments\EXP-016_feature_matrix\logs\feature_matrix.log`

## Outputs
- Results:
  - `experiments\EXP-016_feature_matrix\results\feature_matrix.json`
- Manifests:
  - `experiments\EXP-016_feature_matrix\manifests\input_files.json` (SHA256 per input)
  - `experiments\EXP-016_feature_matrix\manifests\run_metadata.json`

## Results Summary (high level)
See `docs\feature_matrix.md` for the interpreted summary and the strict safe-feature rule (0% missingness per cluster).

## Known Issues / Caveats
- Results are based on a local snapshot (EXP-001 job_partials), not the authoritative v3 dataset on HPC.
- Safe-feature rule is strict (0% missingness). This will exclude many useful but partially-available features.
