#!/usr/bin/env python3
"""Reproduce EXP-015 baseline artifacts from the frozen snapshot.

This is a *replay reproducer*: it regenerates the EXP-015 output artifacts
(results CSV, covariate shift JSON, and a summary markdown) from the copied
snapshot under:
  experiments/EXP-015_baseline/source/

It also captures reproducibility metadata (git commit/status, python version,
pip freeze) and writes a manifest with SHA256 hashes.

Usage (from 01-Projects/FRESCO-v3):
  python scripts\\reproduce_exp015_baseline.py --config experiments\\EXP-015_baseline\\config\\reproduce_exp015_baseline.json

NOTE: This does NOT recompute EXP-015 from raw shards (the original scripts/logs
referenced in EXP015_FINAL_REPORT.md are not present in the snapshot). It is
intended to provide a single-command, provenance-rich regeneration of the
published baseline artifacts.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _git_info(repo_root: Path) -> dict:
    info: dict = {}

    rc, out, _ = _run(["git", "rev-parse", "HEAD"], repo_root)
    info["git_commit"] = out.strip() if rc == 0 else None

    rc, out, _ = _run(["git", "status", "--porcelain=v1"], repo_root)
    info["git_status_porcelain"] = out if rc == 0 else None

    return info


def _read_results_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _select_rows(rows: list[dict], model_names: set[str]) -> list[dict]:
    return [r for r in rows if r.get("model_name") in model_names]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]  # .../01-Projects/FRESCO-v3
    cfg_path = (repo_root / args.config).resolve()

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    run_id = cfg["run_id"]
    baseline_dir = (repo_root / cfg["baseline_dir"]).resolve()

    paths = {k: (repo_root / v).resolve() for k, v in cfg["paths"].items()}

    # Ensure directories exist
    for d in [
        baseline_dir / "logs",
        baseline_dir / "results",
        baseline_dir / "manifests",
        baseline_dir / "validation",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    log_file = (baseline_dir / "logs" / "reproduce_exp015_baseline.log").resolve()
    def log(msg: str):
        line = f"[{_utc_now_iso()}] {msg}"
        print(line)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    log(f"run_id={run_id}")
    log(f"config={cfg_path}")

    # Basic input existence checks
    required_inputs = [
        paths["source_report_md"],
        paths["source_results_csv"],
        paths["source_covariate_shift_json"],
    ]
    for p in required_inputs:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    # Capture environment artifacts
    (baseline_dir / "validation" / "python_version.txt").write_text(
        sys.version.replace("\n", " ") + "\n",
        encoding="utf-8",
    )

    try:
        rc, out, err = _run([sys.executable, "-m", "pip", "freeze"], repo_root)
        (baseline_dir / "validation" / "pip_freeze.txt").write_text(
            out if rc == 0 else (out + "\n" + err),
            encoding="utf-8",
        )
    except Exception as e:
        (baseline_dir / "validation" / "pip_freeze.txt").write_text(
            f"pip freeze failed: {e}\n",
            encoding="utf-8",
        )

    # Copy baseline artifacts into results/ (this is the actual "reproduction" output)
    out_results_csv = baseline_dir / "results" / "exp015_results.csv"
    out_shift_json = baseline_dir / "results" / "exp015_covariate_shift.json"
    out_report_md = baseline_dir / "results" / "EXP015_FINAL_REPORT.md"

    shutil.copy2(paths["source_results_csv"], out_results_csv)
    shutil.copy2(paths["source_covariate_shift_json"], out_shift_json)
    shutil.copy2(paths["source_report_md"], out_report_md)

    # Create a small derived summary (deterministic) from the results table
    rows = _read_results_csv(out_results_csv)
    key = _select_rows(
        rows,
        {
            "conte",
            "anvil",
            "conte→anvil",
            "anvil→conte",
            "pooled_no_id",
            "pooled_with_id",
        },
    )

    summary_md = baseline_dir / "results" / "exp015_baseline_summary.md"
    lines = []
    lines.append(f"# {run_id}: EXP-015 baseline replay summary")
    lines.append("")
    lines.append("This file is generated by `scripts/reproduce_exp015_baseline.py` from the frozen snapshot.")
    lines.append("")
    lines.append("## Included files")
    lines.append(f"- `exp015_results.csv`")
    lines.append(f"- `exp015_covariate_shift.json`")
    lines.append(f"- `EXP015_FINAL_REPORT.md`")
    lines.append("")
    lines.append("## Key rows (subset)")
    lines.append("")
    lines.append("| model_name | train_cluster | test_cluster | r2 | mae_log | mean_residual | slope | calibration_r2 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")

    def _f(x: str) -> str:
        if x is None:
            return ""
        try:
            return f"{float(x):.3f}"
        except Exception:
            return str(x)

    for r in key:
        lines.append(
            "| {model_name} | {train_cluster} | {test_cluster} | {r2} | {mae_log} | {mean_residual} | {slope} | {calibration_r2} |".format(
                model_name=r.get("model_name", ""),
                train_cluster=r.get("train_cluster", ""),
                test_cluster=r.get("test_cluster", ""),
                r2=_f(r.get("r2")),
                mae_log=_f(r.get("mae_log")),
                mean_residual=_f(r.get("mean_residual")),
                slope=_f(r.get("slope")),
                calibration_r2=_f(r.get("calibration_r2")),
            )
        )

    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Write reproducibility metadata and manifests
    meta = {
        "run_id": run_id,
        "created_utc": _utc_now_iso(),
        "reproducer": str((repo_root / "scripts" / "reproduce_exp015_baseline.py").resolve()),
        "config": str(cfg_path),
        "inputs": {k: str(v) for k, v in paths.items()},
        "git": _git_info(repo_root.parents[1]),  # git repo root is .../ObsidianNotes/Main
    }

    (baseline_dir / "manifests" / "run_metadata.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    manifest = {
        "run_id": run_id,
        "created_utc": _utc_now_iso(),
        "files": [],
    }

    for p in [
        cfg_path,
        log_file,
        out_results_csv,
        out_shift_json,
        out_report_md,
        summary_md,
        baseline_dir / "validation" / "python_version.txt",
        baseline_dir / "validation" / "pip_freeze.txt",
        baseline_dir / "manifests" / "run_metadata.json",
    ]:
        if p.exists():
            manifest["files"].append(
                {
                    "path": os.path.relpath(p, repo_root),
                    "sha256": _sha256(p),
                    "bytes": p.stat().st_size,
                }
            )

    (baseline_dir / "manifests" / "baseline_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    validation = {
        "run_id": run_id,
        "created_utc": _utc_now_iso(),
        "checks": [
            {
                "name": "inputs_exist",
                "passed": True,
                "details": [str(p) for p in required_inputs],
            },
            {
                "name": "results_csv_nonempty",
                "passed": len(rows) > 0,
                "details": {"row_count": len(rows)},
            },
        ],
        "limitations": [
            "This replay does not recompute EXP-015 from raw shards; it regenerates the baseline artifacts from the frozen snapshot.",
            "EXP015_FINAL_REPORT.md references scripts/logs that are not present in the snapshot.",
        ],
    }

    (baseline_dir / "validation" / "replay_validation.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    log(f"Wrote manifest: {baseline_dir / 'manifests' / 'baseline_manifest.json'}")
    log(f"Wrote summary:  {summary_md}")
    log("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
