# FRESCO v4 Configuration

**Last Updated**: 2026-03-13

## 1. Config files
All runs must be parameterized by a single config file, stored with the run artifacts.

Recommended: JSON at `configs/<run_name>.json` (or YAML at `configs/<run_name>.yaml`).

## 2. Required config fields

### 2.1 Inherited from v3
These fields are carried over from the v3 configuration format:

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Experiment identifier, `EXP-XXX` format |
| `dataset_version` | string | e.g., `"v3.0"` |
| `dataset_label` | string | Human-readable dataset tag |
| `source_cluster` | string | Source domain cluster (e.g., `"anvil"`) |
| `target_cluster` | string | Target domain cluster (e.g., `"conte"`) |
| `regime` | string | Workload regime filter (e.g., `"hardware_cpu_standard"`) |
| `feature_columns` | list[string] | Features for overlap and/or modeling |
| `overlap_band` | list[float] | Propensity overlap band, e.g., `[0.2, 0.8]` |
| `propensity_model` | string | Domain classifier type (e.g., `"logistic"`) |
| `random_seed` | int | General/model RNG seed (bootstrap, model fitting, other non-data randomness) |
| `data_seed` | int | Data sampling seed used when loading source/target rows via `read_job_level_frame()` |
| `inputs_manifest` | string | Path to input manifest |
| `sampling_plan_path` | string | Path to frozen sampling plan JSON |
| `label_column` | string | Target variable (e.g., `"peak_memory_fraction"`) |
| `label_transform` | string | Label transform (e.g., `"log"`, `"none"`) |
| `label_proxy` | string | If applicable, proxy label definition |
| `model` | string | Base model type (e.g., `"ridge"`, `"huber"`) |
| `adaptation` | string | Domain adaptation method (e.g., `"none"`, `"coral"`) |
| `split` | dict | Source train/test split config, including `split.seed` |
| `n_boot` | int | Number of bootstrap iterations for CI |
| `max_rows_source` | int | Max raw rows to sample from source |
| `max_rows_target` | int | Max raw rows to sample from target |
| `overlap_run` | string | Path to Phase 2 overlap results (matched indices) |

### 2.2 New few-shot fields (v4)
These fields are new in v4 and control few-shot calibration:

| Field | Type | Description |
|-------|------|-------------|
| `few_shot.n_target_labels` | int | Number of labeled target jobs for calibration (N). Set to 0 for zero-shot baseline. |
| `few_shot.strategy` | string | Calibration strategy. One of: `output_recal`, `fine_tune`, `stacked`, `target_only`, `zero_shot` |
| `few_shot.target_label_seed` | int | Seed for sampling the N target calibration jobs |
| `few_shot.min_target_eval_rows` | int | Minimum number of held-out target evaluation rows to preserve; requests that would violate this are capped safely |
| `few_shot.target_weight` | float | Weight multiplier for target rows in `fine_tune` strategy. Typically `len(source_train) / N`. |
| `few_shot.recal_prior` | dict (optional) | Bayesian prior for `output_recal`. Keys: `a_mean`, `a_std`, `b_mean`, `b_std`. Default: uninformative (OLS). |

### 2.3 Strategy-specific field requirements

| Strategy | Required fields | Optional fields |
|----------|----------------|-----------------|
| `zero_shot` | `n_target_labels=0` | — |
| `output_recal` | `n_target_labels`, `target_label_seed` | `recal_prior` |
| `fine_tune` | `n_target_labels`, `target_label_seed`, `target_weight` | — |
| `stacked` | `n_target_labels`, `target_label_seed` | — |
| `target_only` | `n_target_labels`, `target_label_seed` | — |

## 3. Run naming
- Experiments: `EXP-XXX` (consistent with v3 research system)
- Production runs (if any): `PROD-YYYYMMDD-<tag>`

## 4. Environment capture
Config must include or accompany:
- conda env name
- Python version
- package lock (pip freeze / conda env export)
- git commit hash for pipeline and analysis code

## 5. Example config (few-shot output recalibration)

```json
{
  "run_id": "EXP-101",
  "dataset_version": "v3.0",
  "dataset_label": "chunks-v3 authoritative",
  "source_cluster": "anvil",
  "target_cluster": "conte",
  "regime": "hardware_cpu_standard",
  "feature_columns": ["ncores", "nhosts", "timelimit_sec", "runtime_sec", "runtime_fraction"],
  "overlap_band": [0.2, 0.8],
  "propensity_model": "logistic",
  "random_seed": 1337,
  "data_seed": 1337,
  "inputs_manifest": "/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl",
  "sampling_plan_path": "experiments/frozen_sampling_plan.json",
  "label_column": "peak_memory_fraction",
  "label_transform": "log",
  "label_proxy": null,
  "model": "ridge",
  "adaptation": "none",
  "split": {"test_size": 0.2, "seed": 42},
  "n_boot": 200,
  "max_rows_source": 300000,
  "max_rows_target": 300000,
  "overlap_run": "experiments/EXP-062_regime_matching_.../results/overlap_report.json",
  "few_shot": {
    "n_target_labels": 50,
    "strategy": "output_recal",
    "target_label_seed": 7777,
    "min_target_eval_rows": 50,
    "recal_prior": null
  }
}
```

## 6. Backward compatibility with v3
When `few_shot.strategy` is `"zero_shot"` (or the `few_shot` block is absent), v4 behaves identically to v3. This ensures v3 baselines can be reproduced within the v4 framework. For backward compatibility, if `data_seed` is omitted, data loading falls back to `random_seed`.

## 7. Sweep generator config (`scripts/few_shot_sweep.py`)
The sweep generator expands a base experiment config into a set of per-run configs and can also emit a SLURM array script.

| Field | Type | Description |
|-------|------|-------------|
| `base_config` | string | Path to the base experiment config used as the template for every generated run. |
| `exp_number_start` | int | First experiment number to assign (e.g., `3` creates `EXP-003_...`). |
| `description_prefix` | string | Prefix appended to generated run IDs after `EXP-XXX_`. |
| `strategies` | list[string] | Main few-shot strategies to generate. |
| `n_values` | list[int] | Calibration-set sizes to sweep for the main strategies. |
| `seeds` | list[int] | Label-sampling seeds. Each value is written to `few_shot.target_label_seed` for generated runs. |
| `data_seed` | int | Optional fixed data-sampling seed written into every generated config, keeping sampled source/target cohorts stable across `seeds`. |
| `split_seed` | int | Optional fixed source train/test split seed written into every generated config. |
| `random_seed` | int | Optional fixed general/model RNG seed written into every generated config. If omitted, the base config value is preserved. |
| `few_shot.min_target_eval_rows` | int | Optional minimum target holdout to merge into each generated run config. |
| `baseline_strategies` | list[string] | Optional subset of baselines to generate before the main grid. Allowed values: `zero_shot`, `full_target`. Use an empty list (or `include_baselines=false`) to skip them. |
| `manifest_path` | string | Optional output path for the generated sweep manifest. Defaults to `config/sweep_manifest.json`. |
| `config_list_path` | string | Optional output path for the generated config list used by the SLURM array script. Defaults to `config/sweep_config_paths.txt`. |
| `slurm_script_path` | string | Optional output path for the generated SLURM script. Defaults to `scripts/few_shot_sweep.slurm`. |
| `slurm` | dict | Optional SLURM settings. Common keys: `job_name`, `partition`, `qos`, `account`, `gres`, `cpus_per_task`, `mem`, `time`, `output`, `error`, `setup_commands`, `python_command`, `transfer_script`. |

For the current `sbagchi` allocation on Gilbreth, the validated sweep default is `partition: "a100-80gb"` with `qos: "normal"`. Do not leave `partition` implicit, do not use generic `"gpu"` aliases, and do not rely on `sbbest` to pick a partition for this account. If a submitted job stays pending with reason `AssocGrpGRES`, interpret that as temporary shared GPU quota saturation rather than a bad partition/QoS config. Earlier `training` / `qos=training` attempts should not be used as the default unless they are re-verified for this account.

### Example sweep config
```json
{
  "base_config": "config/exp002_zero_shot_baseline.json",
  "exp_number_start": 3,
  "description_prefix": "few_shot_main",
  "strategies": ["output_recal", "fine_tune", "stacked", "target_only"],
  "n_values": [10, 25, 50, 100, 200, 500],
  "seeds": [1337, 2024, 2025],
  "data_seed": 1337,
  "split_seed": 1337,
  "baseline_strategies": ["full_target"],
  "few_shot": {
    "min_target_eval_rows": 50
  },
  "slurm": {
    "partition": "a100-80gb",
    "qos": "normal",
    "account": "sbagchi",
    "gres": "gpu:1",
    "setup_commands": [
      "source /home/jmckerra/anaconda3/etc/profile.d/conda.sh",
      "conda activate fresco_v2"
    ]
  }
}
```
