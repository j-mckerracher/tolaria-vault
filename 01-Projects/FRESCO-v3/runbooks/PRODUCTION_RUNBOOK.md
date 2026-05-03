# Production Runbook: Build FRESCO v3 Dataset

**Last Updated**: 2026-02-03

## Goal
Produce `/depot/sbagchi/data/josh/FRESCO/chunks-v3/` with full reproducibility artifacts suitable for publication.

## Pre-flight (Required)
1. Confirm input root exists and is readable.
2. Confirm output root exists or can be created.
3. Confirm conda env name + versions.
	1. Confirm pipeline code is pinned to a git commit. 
4. Confirm config file created (see `docs/CONFIGURATION.md`).
5. **Confirm production SLURM scripts target `--partition=a100-80gb`** — the `sbagchi` account has zero allocation on `a10`, `a30`, `a100-40gb`, and `h100`. Jobs submitted to any other GPU partition will queue indefinitely with `AssocGrpGRES`. Run `slist` to check current group GPU usage before submitting.
   - For short development or diagnostic jobs only, `--partition=training --qos=training --account=sbagchi --gres=gpu:1` is a verified fallback when `a100-80gb` quota is saturated.

## Step-by-step

### 1) Create run ID
- `PROD-YYYYMMDD-<tag>`
- Create output folders:
  - `manifests/`, `validation/`, `logs/`

### 2) Capture environment
On the execution host:
- `python --version`
- `pip freeze > validation/pip_freeze.txt`
- `conda env export > validation/conda_env.yml` (if available)
- Record OS + hostname

### 3) Capture code version
- `git rev-parse HEAD` for pipeline repo
- `git diff` should be empty (or saved as artifact)

### 4) Execute production pipeline
- Run extract→transform→validate→write for all targeted months.
- Use SLURM array jobs for parallelization.

### 5) Validation outputs
Must produce:
- schema/dtype report
- missingness report (per cluster)
- sanity checks
- Current workflow: run `scripts/finalize_production_v3.py` after the parquet build (this is already wired into `scripts/production_v3.slurm`) so the output directory gets the full validation + reproducibility bundle.

### 6) Manifests
Write:
- `manifests/input_manifest.jsonl`: every input file processed
- `manifests/output_manifest.jsonl`: every output file written
- `manifests/run_metadata.json`: config + hashes + env paths

### 7) Post-run verification
- Randomly sample N=100 output shards across years/clusters
- Verify schema/dtypes and basic invariants

### 8) Archive & snapshot
- Copy run artifacts to a persistent location in `/depot/.../FRESCO-Research/` under the run ID.

## Stop conditions
- Any dtype mismatch during parquet append/write
- Schema drift not accounted for by union-by-name
- Validation Level 0 or 1 fails

## Required records for publication
- run ID, config, manifests, env lock, code commit hashes
