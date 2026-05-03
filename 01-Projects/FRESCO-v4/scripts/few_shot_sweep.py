#!/usr/bin/env python3
"""Generate experiment configs and folder scaffolding for a few-shot sweep.

Reads a sweep config that specifies:
  - A base experiment config (template)
  - Sweep axes: N values, strategies, seeds
  - Experiment numbering start

Outputs:
  - One JSON config per (strategy, N, seed) combination
  - Experiment folder scaffolding (config/, logs/, results/, manifests/, validation/)
  - Optional SLURM array job script
  - A sweep manifest listing all generated experiments
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

DEFAULT_BASELINE_STRATEGIES = ("zero_shot", "full_target")
DEFAULT_SLURM_SETTINGS = {
    "job_name": "fresco_v4_sweep",
    "partition": "a100-80gb",
    "account": "sbagchi",
    "gres": "gpu:1",
    "cpus_per_task": 8,
    "mem": "48G",
    "time": "00:30:00",
}
DEFAULT_SLURM_SETUP_COMMANDS = (
    "source /home/jmckerra/anaconda3/etc/profile.d/conda.sh",
    "conda activate fresco_v2",
)


def main() -> int:
    ap = argparse.ArgumentParser(description="FRESCO v4 few-shot sweep generator")
    ap.add_argument("--config", required=True, help="Path to sweep config JSON")
    ap.add_argument(
        "--generate-slurm", action="store_true",
        help="Also generate a SLURM array job script",
    )
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    sweep_path = Path(args.config)
    if not sweep_path.is_absolute():
        sweep_path = repo_root / sweep_path
    sweep_cfg = json.loads(sweep_path.read_text(encoding="utf-8"))

    # ---- Load base config template ----
    base_cfg_path = Path(sweep_cfg["base_config"])
    if not base_cfg_path.is_absolute():
        base_cfg_path = repo_root / base_cfg_path
    base_cfg = json.loads(base_cfg_path.read_text(encoding="utf-8"))

    # ---- Sweep parameters ----
    n_values = sweep_cfg.get("n_values", [10, 25, 50, 100, 200, 500])
    strategies = sweep_cfg.get("strategies", [
        "output_recal", "fine_tune", "stacked", "target_only",
    ])
    seeds = sweep_cfg.get("seeds", [1337, 2024, 2025])
    exp_start = int(sweep_cfg.get("exp_number_start", 3))
    overlap_run_id = sweep_cfg.get("overlap_run_id", base_cfg.get("overlap_run", {}).get("run_id"))
    description_prefix = sweep_cfg.get("description_prefix", "few_shot")
    baseline_strategies = _get_baseline_strategies(sweep_cfg)
    manifest_path = _resolve_repo_path(
        sweep_cfg.get("manifest_path", "config/sweep_manifest.json"),
        repo_root,
    )
    config_list_path = _resolve_repo_path(
        sweep_cfg.get("config_list_path", "config/sweep_config_paths.txt"),
        repo_root,
    )
    slurm_script_path = _resolve_repo_path(
        sweep_cfg.get("slurm_script_path", "scripts/few_shot_sweep.slurm"),
        repo_root,
    )

    if overlap_run_id:
        base_cfg.setdefault("overlap_run", {})
        base_cfg["overlap_run"]["run_id"] = overlap_run_id

    experiments: list[dict] = []
    exp_num = exp_start

    # ---- Generate baseline configs (zero_shot and/or full_target per seed) ----
    if baseline_strategies:
        for seed_val in seeds:
            for strat in baseline_strategies:
                cfg = copy.deepcopy(base_cfg)
                tag = f"{description_prefix}_{strat}_seed{seed_val}"
                run_id = f"EXP-{exp_num:03d}_{tag}"

                cfg["run_id"] = run_id
                _apply_sweep_overrides(cfg, sweep_cfg, seed_val)
                cfg["few_shot"]["strategy"] = strat
                cfg["few_shot"]["n_target_labels"] = 0 if strat == "zero_shot" else -1

                exp_dir = repo_root / "experiments" / run_id
                _scaffold_experiment(exp_dir, cfg, run_id)
                experiments.append(_experiment_manifest_entry(exp_num, run_id, cfg, exp_dir))
                exp_num += 1

    # ---- Generate sweep configs ----
    for strat in strategies:
        for n_val in n_values:
            for seed_val in seeds:
                cfg = copy.deepcopy(base_cfg)
                tag = f"{description_prefix}_{strat}_n{n_val}_seed{seed_val}"
                run_id = f"EXP-{exp_num:03d}_{tag}"

                cfg["run_id"] = run_id
                _apply_sweep_overrides(cfg, sweep_cfg, seed_val)
                cfg["few_shot"]["strategy"] = strat
                cfg["few_shot"]["n_target_labels"] = n_val

                exp_dir = repo_root / "experiments" / run_id
                _scaffold_experiment(exp_dir, cfg, run_id)
                experiments.append(_experiment_manifest_entry(exp_num, run_id, cfg, exp_dir))
                exp_num += 1

    # ---- Write sweep manifest ----
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "sweep_config": str(sweep_path),
        "base_config": str(base_cfg_path),
        "total_experiments": len(experiments),
        "experiments": experiments,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(experiments)} experiment configs")
    print(f"Sweep manifest: {manifest_path}")

    # ---- Optional SLURM array script ----
    if args.generate_slurm:
        _write_slurm_array(
            slurm_script_path,
            experiments,
            repo_root,
            config_list_path,
            sweep_cfg.get("slurm", {}),
        )
        print(f"SLURM array script: {slurm_script_path}")

    return 0


def _resolve_repo_path(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = repo_root / path
    return path


def _get_baseline_strategies(sweep_cfg: dict) -> list[str]:
    if "baseline_strategies" in sweep_cfg:
        baseline_strategies = sweep_cfg.get("baseline_strategies", [])
    elif bool(sweep_cfg.get("include_baselines", True)):
        baseline_strategies = list(DEFAULT_BASELINE_STRATEGIES)
    else:
        baseline_strategies = []

    normalized = [str(strategy).lower() for strategy in baseline_strategies]
    invalid = [
        strategy for strategy in normalized
        if strategy not in DEFAULT_BASELINE_STRATEGIES
    ]
    if invalid:
        raise ValueError(
            f"Unsupported baseline strategies: {', '.join(invalid)}"
        )
    return list(dict.fromkeys(normalized))


def _apply_sweep_overrides(cfg: dict, sweep_cfg: dict, label_seed: int) -> None:
    cfg.setdefault("split", {})
    cfg.setdefault("few_shot", {})

    sweep_few_shot_cfg = dict(sweep_cfg.get("few_shot", {}))
    if "min_target_eval_rows" in sweep_cfg and "min_target_eval_rows" not in sweep_few_shot_cfg:
        sweep_few_shot_cfg["min_target_eval_rows"] = sweep_cfg["min_target_eval_rows"]
    for key, value in sweep_few_shot_cfg.items():
        cfg["few_shot"][key] = copy.deepcopy(value)

    if "split_seed" in sweep_cfg:
        cfg["split"]["seed"] = int(sweep_cfg["split_seed"])
    elif "seed" not in cfg["split"]:
        cfg["split"]["seed"] = int(cfg.get("random_seed", label_seed))

    if "random_seed" in sweep_cfg:
        cfg["random_seed"] = int(sweep_cfg["random_seed"])
    elif "random_seed" not in cfg:
        cfg["random_seed"] = int(cfg.get("split", {}).get("seed", label_seed))

    if "data_seed" in sweep_cfg:
        cfg["data_seed"] = int(sweep_cfg["data_seed"])
    else:
        cfg["data_seed"] = int(
            cfg.get("data_seed", cfg.get("random_seed", cfg["split"]["seed"]))
        )

    cfg["few_shot"]["target_label_seed"] = int(label_seed)


def _experiment_manifest_entry(
    exp_num: int,
    run_id: str,
    cfg: dict,
    exp_dir: Path,
) -> dict:
    return {
        "exp_number": exp_num,
        "run_id": run_id,
        "strategy": cfg["few_shot"]["strategy"],
        "n_labels": cfg["few_shot"]["n_target_labels"],
        "seed": cfg["few_shot"]["target_label_seed"],
        "target_label_seed": cfg["few_shot"]["target_label_seed"],
        "random_seed": cfg.get("random_seed"),
        "data_seed": cfg.get("data_seed"),
        "split_seed": cfg.get("split", {}).get("seed"),
        "min_target_eval_rows": cfg.get("few_shot", {}).get("min_target_eval_rows"),
        "config_path": str(exp_dir / "config" / f"{run_id}.json"),
    }


def _scaffold_experiment(exp_dir: Path, cfg: dict, run_id: str) -> None:
    """Create experiment folder with standard subfolders and config."""
    for sub in ["config", "logs", "results", "manifests", "validation"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    cfg_out = exp_dir / "config" / f"{run_id}.json"
    cfg_out.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _write_slurm_array(
    slurm_path: Path,
    experiments: list[dict],
    repo_root: Path,
    config_list_path: Path,
    slurm_cfg: dict | None = None,
) -> None:
    """Generate a SLURM array job script for all experiments."""
    n = len(experiments)
    config_list_path.parent.mkdir(parents=True, exist_ok=True)
    config_list_path.write_text(
        "\n".join(e["config_path"] for e in experiments) + "\n",
        encoding="utf-8",
    )

    slurm_settings = dict(DEFAULT_SLURM_SETTINGS)
    extra_slurm_cfg = dict(slurm_cfg or {})
    setup_commands = extra_slurm_cfg.pop(
        "setup_commands",
        list(DEFAULT_SLURM_SETUP_COMMANDS),
    )
    python_command = str(extra_slurm_cfg.pop("python_command", "python"))
    transfer_script = _resolve_repo_path(
        str(extra_slurm_cfg.pop("transfer_script", "scripts/few_shot_transfer.py")),
        repo_root,
    )
    output_path = _resolve_repo_path(
        str(extra_slurm_cfg.pop("output", "experiments/sweep_logs/sweep_%A_%a.out")),
        repo_root,
    )
    error_path = _resolve_repo_path(
        str(extra_slurm_cfg.pop("error", "experiments/sweep_logs/sweep_%A_%a.err")),
        repo_root,
    )
    slurm_settings.update(extra_slurm_cfg)
    slurm_settings["array"] = f"1-{n}"
    slurm_settings["output"] = str(output_path)
    slurm_settings["error"] = str(error_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    error_path.parent.mkdir(parents=True, exist_ok=True)
    slurm_path.parent.mkdir(parents=True, exist_ok=True)

    directive_lines = _render_slurm_directives(slurm_settings)
    setup_lines = _normalize_setup_commands(setup_commands)
    script_lines = [
        "#!/bin/bash",
        *directive_lines,
        "",
        "# Read the config path for this array task",
        f'CONFIG=$(sed -n "${{SLURM_ARRAY_TASK_ID}}p" "{config_list_path}")',
        "",
        'echo "Task $SLURM_ARRAY_TASK_ID: $CONFIG"',
        "",
        *setup_lines,
        "",
        f'{python_command} "{transfer_script}" --config "$CONFIG"',
        "",
    ]
    slurm_path.write_text("\n".join(script_lines), encoding="utf-8")


def _normalize_setup_commands(setup_commands: str | list[str]) -> list[str]:
    if isinstance(setup_commands, str):
        return [setup_commands]
    return [str(command) for command in setup_commands]


def _render_slurm_directives(slurm_settings: dict) -> list[str]:
    preferred_order = [
        "job_name",
        "partition",
        "qos",
        "account",
        "gres",
        "cpus_per_task",
        "mem",
        "time",
        "array",
        "output",
        "error",
    ]
    lines: list[str] = []
    emitted: set[str] = set()

    for key in preferred_order:
        if key in slurm_settings and slurm_settings[key] is not None:
            lines.append(f"#SBATCH --{key.replace('_', '-')}={slurm_settings[key]}")
            emitted.add(key)

    for key, value in slurm_settings.items():
        if key in emitted or value is None:
            continue
        lines.append(f"#SBATCH --{key.replace('_', '-')}={value}")

    return lines


if __name__ == "__main__":
    raise SystemExit(main())
