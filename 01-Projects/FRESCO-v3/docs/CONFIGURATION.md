# FRESCO v3 Configuration

**Last Updated**: 2026-02-03

## 1. Config files
All runs must be parameterized by a single config file, stored with the run artifacts.

Recommended: YAML (or JSON) at `configs/<run_name>.yaml`.

## 2. Required config fields
- dataset_version: "v3.0"
- input_root: "/depot/.../FRESCO/chunks"
- output_root: "/depot/.../FRESCO/chunks-v3"
- clusters: [anvil, conte, stampede]
- date_ranges: per cluster (start/end months)
- threads
- cleaning thresholds (peak_memory_fraction bounds, etc.)
- schema enforcement flags
- validation levels enabled

## 3. Run naming
- production runs: `PROD-YYYYMMDD-<tag>`
- experiments: `EXP-XXX` consistent with research system

## 4. Environment capture
Config must include:
- conda env name
- Python version
- package lock (pip freeze/conda env export)
- git commit hashes for pipeline and analysis
