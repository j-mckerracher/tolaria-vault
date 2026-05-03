# Artifact & Reproducibility Guide (for Reviewers)

**Last Updated**: 2026-03-13

This document describes how to reproduce all results from the paper "How Many Labels? Sample-Efficient Cross-Cluster HPC Memory Prediction." It covers provided artifacts, reproduction steps, compute requirements, and dataset access.

---

## What We Provide

### Code
- Pipeline code at a **pinned git commit** (recorded in every `run_metadata.json`).
- All experiment scripts, including `few_shot_transfer.py` and supporting utilities.
- Configuration files for every experiment run.

### Run Artifacts (per experiment)
- **Run config** (`config.json`): all hyperparameters, seeds, N values, strategy selection.
- **Input manifest** (`input_manifest.jsonl`): every input file with path and SHA-256 hash.
- **Output manifest** (`output_manifest.jsonl`): every output file with path and SHA-256 hash.
- **Run metadata** (`run_metadata.json`): git commit, timestamps, hostname, config snapshot.
- **Environment lock**: `pip freeze` output and conda environment export for exact package versions.
- **Validation report**: schema conformance and sanity check results.

### Results
- **Full results table** (CSV): all 72+ runs with complete reporting fields (see `EXPERIMENTS_AND_EVAL.md`).
- **Summary tables** (CSV): strategy comparison, break-even analysis.
- **Figures** (PNG/PDF): sample efficiency curves, strategy comparison heatmaps, regime matching ablation.
- **Bootstrap samples** (serialized): raw bootstrap resamples for reproducible CI computation.

---

## How to Reproduce

### Step 0: Prerequisites
- Access to the Gilbreth HPC cluster (Purdue RCAC) or equivalent system.
- Python 3.10+ environment.
- Git access to the FRESCO pipeline repository.

### Step 1: Checkout Code
```bash
git clone <FRESCO_REPO_URL>
cd FRESCO-v4
git checkout <PINNED_COMMIT_HASH>   # from run_metadata.json
```

### Step 2: Create Environment
```bash
# Option A: pip (recommended)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Verify: pip freeze should match provided environment lock

# Option B: conda
conda env create -f environment.lock.yml
conda activate fresco-v4
```

### Step 3: Verify Dataset Access
```bash
# On Gilbreth:
ls /depot/sbagchi/data/josh/FRESCO/chunks-v3/
# Should contain cluster-specific parquet shard directories
```

### Step 4: Reproduce Zero-Shot Baseline (E0)
```bash
python scripts/few_shot_transfer.py \
    --config config/experiments/E0_zero_shot.json \
    --output-dir results/E0/
```
- Compare output metrics to provided E0 results table.
- Verify R² < 0.3 and calibration slope ≠ 1.

### Step 5: Reproduce Few-Shot Sweep (E1)
```bash
# Run full sweep (72 runs):
python scripts/few_shot_transfer.py \
    --config config/experiments/E1_few_shot_sweep.json \
    --output-dir results/E1/

# Or run individual configurations:
python scripts/few_shot_transfer.py \
    --config config/experiments/E1_few_shot_sweep.json \
    --strategy output_recal \
    --n-cal 50 \
    --seed 42 \
    --output-dir results/E1/output_recal_N50_seed42/
```

### Step 6: Reproduce Regime Matching Ablation (E2)
```bash
python scripts/few_shot_transfer.py \
    --config config/experiments/E2_regime_ablation.json \
    --output-dir results/E2/
```

### Step 7: Verify Results
```bash
# Compare produced CSVs to provided outputs:
python scripts/validate_results.py \
    --produced results/E1/results.csv \
    --expected artifacts/E1_expected_results.csv \
    --tolerance 0.01
```
- Metrics should match within tolerance (small differences due to floating-point ordering are expected).
- Bootstrap CIs should overlap.

---

## Compute Requirements

### Hardware
- **Recommended**: Gilbreth A100-80GB GPU node (used for all reported experiments).
- **Minimum**: Any node with ≥ 48 GB system RAM. GPU is used only for data loading acceleration; all models are CPU-based (Ridge regression).
- **Storage**: ~50 GB for dataset + ~5 GB for all experiment outputs.

### Time Estimates
| Experiment | Runs | Est. Time per Run | Est. Total |
|-----------|------|-------------------|------------|
| E0: Zero-shot baseline | 2 | ~5 min | ~10 min |
| E1: Few-shot sweep | 72 | ~10 min | ~12 hours |
| E2: Regime ablation | 24 | ~10 min | ~4 hours |
| E3: Second pair (if run) | 18 | ~10 min | ~3 hours |
| **Total** | **~116** | | **~19 hours** |

### SLURM Job Submission (Gilbreth)
```bash
# Example SLURM submission for E1:
sbatch --partition=a100-80gb \
       --qos=normal \
       --account=sbagchi \
       --gres=gpu:1 \
       --mem=64G \
       --time=14:00:00 \
       --job-name=fresco-v4-E1 \
       scripts/slurm/run_E1_sweep.sh
```

For the current `sbagchi` allocation, submit jobs with the explicit `a100-80gb` partition. Do not use generic `gpu` partition names or `sbbest` auto-selection here; if the job is accepted but remains pending with `AssocGrpGRES`, that indicates temporary shared GPU quota saturation rather than an invalid partition/QoS setting.

---

## Dataset Access

### Location
- **Primary**: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/` on Gilbreth (Purdue RCAC).
- **Structure**: cluster-specific directories containing hourly parquet shards with unified schema.

### Hardware Metadata
- `config/clusters.json`: per-cluster, per-partition hardware specifications (node_memory_gb, cores_per_node, etc.).
- Required for computing `peak_memory_fraction` at analysis time.

### Access Requirements
- Purdue RCAC account with access to the `sbagchi` depot allocation.
- For external reviewers: contact the corresponding author for dataset access arrangements.

---

## Artifact Checklist

| Artifact | Location | Verification |
|----------|----------|--------------|
| Pipeline code | Git repo at pinned commit | `git log --oneline -1` matches `run_metadata.json` |
| Experiment configs | `config/experiments/` | SHA-256 matches `input_manifest.jsonl` |
| Environment lock | `environment.lock.txt` | `pip freeze` matches after setup |
| Input manifests | `results/*/input_manifest.jsonl` | SHA-256 of input files match |
| Output manifests | `results/*/output_manifest.jsonl` | SHA-256 of output files match |
| Results tables | `results/*/results.csv` | Metrics within tolerance of reported values |
| Figures | `paper/figures/` | Regenerable from results tables |
| Validation reports | `results/*/validation_report.json` | All checks pass |
| clusters.json | `config/clusters.json` | Used for memory normalization |
