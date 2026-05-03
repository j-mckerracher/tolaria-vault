#!/usr/bin/env python3
"""Build consolidated post-repair analysis artifacts for the EXP-003..127 few-shot sweep."""

from __future__ import annotations

import argparse
import json
import numbers
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

DEFAULT_BASELINE_R2 = 0.1070
EXPECTED_ORIGINAL_ROWS = 25
EXPECTED_REPAIR_ROWS = 50
EXPECTED_GROUPS = 25
SOURCE_USING_STRATEGIES = ("output_recal", "fine_tune", "stacked")
STRATEGY_ORDER = {
    "full_target": 0,
    "output_recal": 1,
    "fine_tune": 2,
    "stacked": 3,
    "target_only": 4,
}
STRING_COLUMNS = (
    "analysis_origin",
    "source_artifact",
    "run_id",
    "experiment_dir",
    "created_utc",
    "strategy",
    "source_cluster",
    "target_cluster",
    "regime",
    "overlap_run_id",
    "overlap_band",
    "row_status",
    "status_reason",
    "limitations",
)
INT_COLUMNS = (
    "exp_number",
    "n_target_labels",
    "requested_n_target_labels",
    "effective_n_target_labels",
    "seed",
    "source_overlap_n",
    "target_overlap_n",
    "actual_cal_n",
    "actual_eval_n",
    "min_target_eval_rows",
)
BOOL_COLUMNS = (
    "min_target_eval_rows_satisfied",
    "below_min_target_eval_rows",
    "calibration_n_capped",
)
FLOAT_COLUMNS = (
    "target_r2",
    "delta_vs_exp002",
    "target_mae_log",
    "target_smape",
    "target_slope",
    "target_intercept",
    "target_bias_log",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate original seed-1337 and repaired non-1337 few-shot results."
    )
    parser.add_argument(
        "--summary-csv",
        default="results\\exp003_main_few_shot_summary.csv",
        help="Main sweep summary CSV (EXP-003..077).",
    )
    parser.add_argument(
        "--original-grouped-json",
        default="results\\exp003_main_few_shot_grouped_stats.json",
        help="Existing EXP-003 grouped-stats JSON for provenance/reference.",
    )
    parser.add_argument(
        "--repair-csv",
        default="results\\exp078_127_repair_harvest.csv",
        help="Repair harvest CSV (EXP-078..127).",
    )
    parser.add_argument(
        "--repair-json",
        default="results\\exp078_127_repair_harvest.json",
        help="Existing repair harvest JSON for provenance/reference.",
    )
    parser.add_argument(
        "--base-config",
        default="config\\exp002_zero_shot_baseline.json",
        help="Baseline config used for source/target/regime metadata.",
    )
    parser.add_argument(
        "--main-sweep-config",
        default="config\\exp003_main_few_shot_sweep.json",
        help="Main sweep config used to recover min_target_eval_rows.",
    )
    parser.add_argument(
        "--baseline-r2",
        type=float,
        default=DEFAULT_BASELINE_R2,
        help="Target R² for the EXP-002 zero-shot baseline.",
    )
    parser.add_argument(
        "--output-stem",
        default="results\\exp003_127_post_repair",
        help="Output file stem, without suffix.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    summary_csv_path = resolve_repo_path(args.summary_csv, repo_root)
    original_grouped_json_path = resolve_repo_path(args.original_grouped_json, repo_root)
    repair_csv_path = resolve_repo_path(args.repair_csv, repo_root)
    repair_json_path = resolve_repo_path(args.repair_json, repo_root)
    base_config_path = resolve_repo_path(args.base_config, repo_root)
    main_sweep_config_path = resolve_repo_path(args.main_sweep_config, repo_root)
    output_stem = resolve_repo_path(args.output_stem, repo_root)

    baseline_cfg = load_json(base_config_path)
    main_sweep_cfg = load_json(main_sweep_config_path)
    original_grouped_reference = load_json_if_exists(original_grouped_json_path)
    repair_grouped_reference = load_json_if_exists(repair_json_path)

    baseline_r2 = float(args.baseline_r2)
    min_target_eval_rows = int(
        main_sweep_cfg.get("few_shot", {}).get("min_target_eval_rows", 50)
    )

    original_rows = cast_standard_row_dtypes(
        load_original_rows(
        summary_csv_path=summary_csv_path,
        baseline_cfg=baseline_cfg,
        baseline_r2=baseline_r2,
        min_target_eval_rows=min_target_eval_rows,
        )
    )
    repair_rows = cast_standard_row_dtypes(
        load_repair_rows(
        repair_csv_path=repair_csv_path,
        baseline_cfg=baseline_cfg,
        baseline_r2=baseline_r2,
        )
    )
    combined_rows = pd.concat([original_rows, repair_rows], ignore_index=True)
    combined_rows = sort_row_frame(combined_rows)

    validate_combined_panel(
        combined_rows=combined_rows,
        min_target_eval_rows=min_target_eval_rows,
    )

    grouped_records = build_grouped_records(
        combined_rows=combined_rows,
        baseline_r2=baseline_r2,
    )
    grouped_csv_frame = flatten_grouped_records(grouped_records)

    best_repair_only_source_group = extract_best_group(
        build_grouped_records(repair_rows, baseline_r2),
        lambda record: record["strategy"] in SOURCE_USING_STRATEGIES,
    )
    best_consolidated_source_group = extract_best_group(
        grouped_records,
        lambda record: record["strategy"] in SOURCE_USING_STRATEGIES,
    )
    best_consolidated_nonfull_group = extract_best_group(
        grouped_records,
        lambda record: record["n_target_labels"] != -1,
    )
    best_single_run = extract_best_single_run(combined_rows)

    source_artifacts = {
        "summary_csv": str(summary_csv_path),
        "original_grouped_stats_json": str(original_grouped_json_path),
        "repair_csv": str(repair_csv_path),
        "repair_json": str(repair_json_path) if repair_json_path.exists() else None,
        "base_config": str(base_config_path),
        "main_sweep_config": str(main_sweep_config_path),
    }

    row_payload = build_row_payload(
        combined_rows=combined_rows,
        source_artifacts=source_artifacts,
        baseline_cfg=baseline_cfg,
        baseline_r2=baseline_r2,
        min_target_eval_rows=min_target_eval_rows,
    )
    grouped_payload = build_grouped_payload(
        combined_rows=combined_rows,
        grouped_records=grouped_records,
        source_artifacts=source_artifacts,
        baseline_cfg=baseline_cfg,
        baseline_r2=baseline_r2,
        min_target_eval_rows=min_target_eval_rows,
        original_grouped_reference=original_grouped_reference,
        repair_grouped_reference=repair_grouped_reference,
        best_repair_only_source_group=best_repair_only_source_group,
        best_consolidated_source_group=best_consolidated_source_group,
        best_consolidated_nonfull_group=best_consolidated_nonfull_group,
        best_single_run=best_single_run,
    )
    summary_text = build_summary_text(
        grouped_payload=grouped_payload,
        best_repair_only_source_group=best_repair_only_source_group,
        best_consolidated_source_group=best_consolidated_source_group,
    )

    rows_csv_path = output_stem.with_name(f"{output_stem.name}_consolidated_rows.csv")
    rows_json_path = output_stem.with_name(f"{output_stem.name}_consolidated_rows.json")
    grouped_csv_path = output_stem.with_name(f"{output_stem.name}_grouped_stats.csv")
    grouped_json_path = output_stem.with_name(f"{output_stem.name}_grouped_stats.json")
    summary_txt_path = output_stem.with_name(f"{output_stem.name}_summary.txt")

    rows_csv_path.parent.mkdir(parents=True, exist_ok=True)
    combined_rows.to_csv(rows_csv_path, index=False)
    write_json(rows_json_path, row_payload)
    grouped_csv_frame.to_csv(grouped_csv_path, index=False)
    write_json(grouped_json_path, grouped_payload)
    summary_txt_path.write_text(summary_text, encoding="utf-8")

    print(f"Wrote {len(combined_rows)} consolidated rows to {rows_csv_path}")
    print(f"Wrote row-level JSON to {rows_json_path}")
    print(f"Wrote {len(grouped_records)} grouped records to {grouped_csv_path}")
    print(f"Wrote grouped JSON to {grouped_json_path}")
    print(f"Wrote summary to {summary_txt_path}")
    if best_consolidated_source_group is not None:
        print(
            "Best consolidated source-using mean target R2: "
            f"{best_consolidated_source_group['target_r2_mean']:.6f} "
            f"({best_consolidated_source_group['strategy']}, "
            f"N={best_consolidated_source_group['n_target_labels']})"
        )
    print(
        "Any grouped mean above EXP-002 baseline: "
        f"{grouped_payload['conclusion_flags']['any_group_mean_above_exp002']}"
    )
    print(
        "Repair overlap unique values: "
        f"{grouped_payload['structural_repair_summary']['repair_target_overlap_n_unique']}"
    )
    return 0


def resolve_repo_path(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = repo_root / path
    return path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_json(path)


def load_original_rows(
    summary_csv_path: Path,
    baseline_cfg: dict[str, Any],
    baseline_r2: float,
    min_target_eval_rows: int,
) -> pd.DataFrame:
    df = pd.read_csv(summary_csv_path)
    selected = df[
        (pd.to_numeric(df["seed"], errors="coerce") == 1337)
        & (df["status"] == "complete")
        & df["target_r2"].notna()
    ].copy()
    if len(selected) != EXPECTED_ORIGINAL_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ORIGINAL_ROWS} original valid seed-1337 rows, "
            f"found {len(selected)}."
        )

    overlap_cfg = baseline_cfg.get("overlap_run", {})
    selected["analysis_origin"] = "original_valid_seed1337"
    selected["source_artifact"] = str(summary_csv_path)
    selected["exp_number"] = pd.to_numeric(selected["exp_number"], errors="raise").astype(int)
    selected["seed"] = pd.to_numeric(selected["seed"], errors="raise").astype(int)
    selected["source_cluster"] = baseline_cfg.get("source_cluster")
    selected["target_cluster"] = baseline_cfg.get("target_cluster")
    selected["regime"] = baseline_cfg.get("regime")
    selected["overlap_run_id"] = overlap_cfg.get("run_id")
    selected["overlap_band"] = json.dumps(overlap_cfg.get("overlap_band"))
    selected["requested_n_target_labels"] = pd.to_numeric(
        selected["n_target_labels"], errors="raise"
    ).astype(int)
    selected["effective_n_target_labels"] = pd.to_numeric(
        selected["actual_cal_n"], errors="raise"
    ).astype(int)
    selected["source_overlap_n"] = pd.to_numeric(
        selected["source_overlap_n"], errors="raise"
    ).astype(int)
    selected["target_overlap_n"] = pd.to_numeric(
        selected["target_overlap_n"], errors="raise"
    ).astype(int)
    selected["actual_cal_n"] = pd.to_numeric(selected["actual_cal_n"], errors="raise").astype(int)
    selected["actual_eval_n"] = pd.to_numeric(
        selected["actual_eval_n"], errors="raise"
    ).astype(int)
    selected["min_target_eval_rows"] = int(min_target_eval_rows)
    selected["min_target_eval_rows_satisfied"] = selected["actual_eval_n"] >= min_target_eval_rows
    selected["below_min_target_eval_rows"] = ~selected["min_target_eval_rows_satisfied"]
    selected["calibration_n_capped"] = (
        (selected["requested_n_target_labels"] > 0)
        & (selected["effective_n_target_labels"] < selected["requested_n_target_labels"])
    )
    selected["experiment_dir"] = selected["experiment_dir"].fillna("")
    selected["created_utc"] = None
    selected["target_intercept"] = pd.to_numeric(
        selected["target_intercept"], errors="coerce"
    )
    selected["target_bias_log"] = None
    selected["delta_vs_exp002"] = pd.to_numeric(selected["target_r2"], errors="raise") - baseline_r2
    selected["row_status"] = selected["status"].fillna("complete")
    selected["status_reason"] = selected["status_reason"].fillna("")
    selected["limitations"] = ""

    return selected[
        [
            "analysis_origin",
            "source_artifact",
            "exp_number",
            "run_id",
            "experiment_dir",
            "created_utc",
            "strategy",
            "n_target_labels",
            "requested_n_target_labels",
            "effective_n_target_labels",
            "seed",
            "source_cluster",
            "target_cluster",
            "regime",
            "overlap_run_id",
            "overlap_band",
            "source_overlap_n",
            "target_overlap_n",
            "actual_cal_n",
            "actual_eval_n",
            "min_target_eval_rows",
            "min_target_eval_rows_satisfied",
            "below_min_target_eval_rows",
            "calibration_n_capped",
            "target_r2",
            "delta_vs_exp002",
            "target_mae_log",
            "target_smape",
            "target_slope",
            "target_intercept",
            "target_bias_log",
            "row_status",
            "status_reason",
            "limitations",
        ]
    ].copy()


def load_repair_rows(
    repair_csv_path: Path,
    baseline_cfg: dict[str, Any],
    baseline_r2: float,
) -> pd.DataFrame:
    df = pd.read_csv(repair_csv_path)
    selected = df[df["metrics_exists"].fillna(False) & df["target_r2"].notna()].copy()
    if len(selected) != EXPECTED_REPAIR_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_REPAIR_ROWS} repaired rows with metrics, found {len(selected)}."
        )

    overlap_records = selected["overlap"].apply(parse_overlap_json)
    selected["analysis_origin"] = "repair_non1337"
    selected["source_artifact"] = str(repair_csv_path)
    selected["exp_number"] = pd.to_numeric(selected["exp_num"], errors="raise").astype(int)
    selected["seed"] = pd.to_numeric(
        selected["target_label_seed"], errors="raise"
    ).astype(int)
    selected["source_cluster"] = selected["pair_source"].fillna(baseline_cfg.get("source_cluster"))
    selected["target_cluster"] = selected["pair_target"].fillna(baseline_cfg.get("target_cluster"))
    selected["regime"] = selected["regime"].fillna(baseline_cfg.get("regime"))
    selected["overlap_run_id"] = overlap_records.apply(lambda item: item.get("run_id", ""))
    selected["overlap_band"] = overlap_records.apply(
        lambda item: json.dumps(item.get("overlap_band"))
        if item.get("overlap_band") is not None
        else ""
    )
    selected["requested_n_target_labels"] = pd.to_numeric(
        selected["n_target_labels"], errors="raise"
    ).astype(int)
    selected["effective_n_target_labels"] = pd.to_numeric(
        selected["effective_n_target_labels"], errors="raise"
    ).astype(int)
    selected["source_overlap_n"] = overlap_records.apply(
        lambda item: int(item.get("matched_source_n")) if item.get("matched_source_n") is not None else None
    )
    selected["target_overlap_n"] = overlap_records.apply(
        lambda item: int(item.get("matched_target_n")) if item.get("matched_target_n") is not None else None
    )
    selected["actual_cal_n"] = pd.to_numeric(selected["actual_cal_n"], errors="raise").astype(int)
    selected["actual_eval_n"] = pd.to_numeric(
        selected["actual_eval_n"], errors="raise"
    ).astype(int)
    selected["min_target_eval_rows"] = pd.to_numeric(
        selected["min_target_eval_rows"], errors="raise"
    ).astype(int)
    selected["min_target_eval_rows_satisfied"] = selected[
        "min_target_eval_rows_satisfied"
    ].astype(bool)
    selected["below_min_target_eval_rows"] = ~selected["min_target_eval_rows_satisfied"]
    selected["calibration_n_capped"] = selected["calibration_n_capped"].astype(bool)
    selected["experiment_dir"] = selected["exp_dir"].fillna("")
    selected["created_utc"] = selected["created_utc"].fillna("")
    selected["target_intercept"] = None
    selected["target_bias_log"] = pd.to_numeric(
        selected["target_bias_log"], errors="coerce"
    )
    selected["delta_vs_exp002"] = pd.to_numeric(selected["target_r2"], errors="raise") - baseline_r2
    selected["row_status"] = "complete"
    selected["status_reason"] = ""
    selected["limitations"] = selected["limitations"].fillna("")

    return selected[
        [
            "analysis_origin",
            "source_artifact",
            "exp_number",
            "run_id",
            "experiment_dir",
            "created_utc",
            "strategy",
            "n_target_labels",
            "requested_n_target_labels",
            "effective_n_target_labels",
            "seed",
            "source_cluster",
            "target_cluster",
            "regime",
            "overlap_run_id",
            "overlap_band",
            "source_overlap_n",
            "target_overlap_n",
            "actual_cal_n",
            "actual_eval_n",
            "min_target_eval_rows",
            "min_target_eval_rows_satisfied",
            "below_min_target_eval_rows",
            "calibration_n_capped",
            "target_r2",
            "delta_vs_exp002",
            "target_mae_log",
            "target_smape",
            "target_slope",
            "target_intercept",
            "target_bias_log",
            "row_status",
            "status_reason",
            "limitations",
        ]
    ].copy()


def parse_overlap_json(raw_value: Any) -> dict[str, Any]:
    if raw_value is None:
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    text = str(raw_value).strip()
    if not text:
        return {}
    return json.loads(text)


def cast_standard_row_dtypes(frame: pd.DataFrame) -> pd.DataFrame:
    typed = frame.copy()
    for column in STRING_COLUMNS:
        typed[column] = typed[column].fillna("").astype(str)
    for column in INT_COLUMNS:
        typed[column] = pd.to_numeric(typed[column], errors="raise").astype("int64")
    for column in BOOL_COLUMNS:
        typed[column] = typed[column].astype(bool)
    for column in FLOAT_COLUMNS:
        typed[column] = pd.to_numeric(typed[column], errors="coerce").astype("float64")
    return typed


def sort_row_frame(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.copy()
    ordered["__strategy_order"] = ordered["strategy"].map(STRATEGY_ORDER).fillna(999)
    ordered["__origin_order"] = ordered["analysis_origin"].map(
        {
            "original_valid_seed1337": 0,
            "repair_non1337": 1,
        }
    ).fillna(99)
    ordered = ordered.sort_values(
        by=["__strategy_order", "n_target_labels", "__origin_order", "seed", "exp_number"],
        kind="mergesort",
    )
    return ordered.drop(columns=["__strategy_order", "__origin_order"]).reset_index(drop=True)


def validate_combined_panel(
    combined_rows: pd.DataFrame,
    min_target_eval_rows: int,
) -> None:
    if len(combined_rows) != EXPECTED_ORIGINAL_ROWS + EXPECTED_REPAIR_ROWS:
        raise ValueError(
            "Unexpected consolidated row count: "
            f"{len(combined_rows)} != {EXPECTED_ORIGINAL_ROWS + EXPECTED_REPAIR_ROWS}"
        )
    if combined_rows["target_r2"].isna().any():
        raise ValueError("Consolidated rows still contain null target_r2 values.")

    group_sizes = combined_rows.groupby(["strategy", "n_target_labels"]).size()
    if len(group_sizes) != EXPECTED_GROUPS:
        raise ValueError(f"Expected {EXPECTED_GROUPS} strategy/N groups, found {len(group_sizes)}.")
    if (group_sizes != 3).any():
        bad_groups = {
            f"{strategy}:{n}": int(count)
            for (strategy, n), count in group_sizes.items()
            if int(count) != 3
        }
        raise ValueError(f"Unexpected per-group row counts: {bad_groups}")

    repair_rows = combined_rows[combined_rows["analysis_origin"] == "repair_non1337"].copy()
    repair_overlap_values = sorted_unique_int(repair_rows["target_overlap_n"])
    if repair_overlap_values != [223]:
        raise ValueError(f"Repair target overlap is not fixed at 223: {repair_overlap_values}")
    if int((repair_rows["actual_eval_n"] == 0).sum()) != 0:
        raise ValueError("Repair rows still contain zero-evaluation failures.")

    below_min_repair = repair_rows[repair_rows["below_min_target_eval_rows"]]
    if not below_min_repair.empty:
        invalid_caveat_rows = below_min_repair[below_min_repair["strategy"] != "full_target"]
        if not invalid_caveat_rows.empty:
            raise ValueError(
                "Only repaired full_target rows should fall below min_target_eval_rows."
            )
    if (
        repair_rows.loc[repair_rows["strategy"] == "full_target", "actual_eval_n"]
        .drop_duplicates()
        .tolist()
        != [45]
    ):
        raise ValueError("Repaired full_target rows no longer match the expected 45-row holdout caveat.")

    if min_target_eval_rows != 50:
        raise ValueError(f"Expected min_target_eval_rows=50, found {min_target_eval_rows}.")


def build_grouped_records(
    combined_rows: pd.DataFrame,
    baseline_r2: float,
) -> list[dict[str, Any]]:
    grouped_records: list[dict[str, Any]] = []
    grouped = combined_rows.groupby(["strategy", "n_target_labels"], sort=False)
    for (strategy, n_target_labels), group in grouped:
        group = group.sort_values(by=["analysis_origin", "seed", "exp_number"], kind="mergesort")
        r2_series = pd.to_numeric(group["target_r2"], errors="raise")
        group_caveats = build_group_caveats(group)
        record: dict[str, Any] = {
            "strategy": str(strategy),
            "n_target_labels": int(n_target_labels),
            "count": int(len(group)),
            "seeds": sorted_unique_int(group["seed"]),
            "analysis_origins": sorted_unique_str(group["analysis_origin"]),
            "requested_n_target_labels_unique": sorted_unique_int(group["requested_n_target_labels"]),
            "effective_n_target_labels_unique": sorted_unique_int(group["effective_n_target_labels"]),
            "actual_cal_n_unique": sorted_unique_int(group["actual_cal_n"]),
            "actual_eval_n_unique": sorted_unique_int(group["actual_eval_n"]),
            "source_overlap_n_unique": sorted_unique_int(group["source_overlap_n"]),
            "target_overlap_n_unique": sorted_unique_int(group["target_overlap_n"]),
            "min_target_eval_rows": sorted_unique_int(group["min_target_eval_rows"]),
            "calibration_n_capped_count": int(group["calibration_n_capped"].sum()),
            "below_min_target_eval_rows_count": int(group["below_min_target_eval_rows"].sum()),
            "all_min_target_eval_rows_satisfied": bool((~group["below_min_target_eval_rows"]).all()),
            "mixed_target_overlap_n": len(sorted_unique_int(group["target_overlap_n"])) > 1,
            "mixed_actual_eval_n": len(sorted_unique_int(group["actual_eval_n"])) > 1,
            "mixed_effective_n_target_labels": len(sorted_unique_int(group["effective_n_target_labels"])) > 1,
            "target_r2_mean": float(r2_series.mean()),
            "target_r2_median": float(r2_series.median()),
            "target_r2_std": float(population_std(r2_series)),
            "target_r2_iqr": float(iqr(r2_series)),
            "target_r2_min": float(r2_series.min()),
            "target_r2_max": float(r2_series.max()),
            "target_r2_range": float(r2_series.max() - r2_series.min()),
            "delta_vs_exp002_mean": float(r2_series.mean() - baseline_r2),
            "delta_vs_exp002_median": float(r2_series.median() - baseline_r2),
            "rows_above_exp002": int((r2_series > baseline_r2).sum()),
            "rows_below_or_equal_exp002": int((r2_series <= baseline_r2).sum()),
            "mean_target_mae_log": float(pd.to_numeric(group["target_mae_log"], errors="coerce").mean()),
            "median_target_mae_log": float(pd.to_numeric(group["target_mae_log"], errors="coerce").median()),
            "mean_target_smape": float(pd.to_numeric(group["target_smape"], errors="coerce").mean()),
            "median_target_smape": float(pd.to_numeric(group["target_smape"], errors="coerce").median()),
            "mean_target_slope": float(pd.to_numeric(group["target_slope"], errors="coerce").mean()),
            "median_target_slope": float(pd.to_numeric(group["target_slope"], errors="coerce").median()),
            "best_run_id": str(group.loc[r2_series.idxmax(), "run_id"]),
            "best_run_origin": str(group.loc[r2_series.idxmax(), "analysis_origin"]),
            "best_run_seed": int(group.loc[r2_series.idxmax(), "seed"]),
            "best_run_target_r2": float(r2_series.max()),
            "group_caveats": group_caveats,
        }
        if strategy in SOURCE_USING_STRATEGIES:
            record["vs_target_only_same_n"] = compare_vs_target_only(
                combined_rows=combined_rows,
                strategy=str(strategy),
                n_target_labels=int(n_target_labels),
            )
        else:
            record["vs_target_only_same_n"] = None
        grouped_records.append(record)

    grouped_records.sort(
        key=lambda item: (
            STRATEGY_ORDER.get(item["strategy"], 999),
            int(item["n_target_labels"]),
        )
    )
    return grouped_records


def build_group_caveats(group: pd.DataFrame) -> list[str]:
    caveats: list[str] = []
    if len(sorted_unique_int(group["target_overlap_n"])) > 1:
        caveats.append(
            "Mixed cohort sizes: original seed-1337 uses target_overlap_n=2459 while repaired seeds use target_overlap_n=223."
        )
    if len(sorted_unique_int(group["actual_eval_n"])) > 1:
        caveats.append(
            "Evaluation-set sizes differ sharply across rows; across-seed dispersion is not a pure fixed-cohort estimate."
        )
    if len(sorted_unique_int(group["effective_n_target_labels"])) > 1:
        caveats.append(
            "Effective calibration sizes differ across rows, so requested N does not map to one shared calibration count."
        )
    capped_count = int(group["calibration_n_capped"].sum())
    if capped_count:
        caveats.append(
            f"{capped_count} row(s) cap calibration to preserve the evaluation holdout."
        )
    below_min_count = int(group["below_min_target_eval_rows"].sum())
    if below_min_count:
        caveats.append(
            f"{below_min_count} row(s) fall below min_target_eval_rows=50; repaired full_target rows have actual_eval_n=45."
        )
    return caveats


def compare_vs_target_only(
    combined_rows: pd.DataFrame,
    strategy: str,
    n_target_labels: int,
) -> dict[str, Any] | None:
    strategy_rows = combined_rows[
        (combined_rows["strategy"] == strategy)
        & (combined_rows["n_target_labels"] == n_target_labels)
    ][["analysis_origin", "seed", "run_id", "target_r2"]].copy()
    target_only_rows = combined_rows[
        (combined_rows["strategy"] == "target_only")
        & (combined_rows["n_target_labels"] == n_target_labels)
    ][["analysis_origin", "seed", "run_id", "target_r2"]].copy()
    if strategy_rows.empty or target_only_rows.empty:
        return None

    target_only_rows = target_only_rows.rename(
        columns={
            "run_id": "target_only_run_id",
            "target_r2": "target_only_r2",
        }
    )
    merged = strategy_rows.merge(
        target_only_rows,
        on=["analysis_origin", "seed"],
        how="inner",
    )
    if merged.empty:
        return None

    merged["delta_r2"] = pd.to_numeric(merged["target_r2"], errors="raise") - pd.to_numeric(
        merged["target_only_r2"], errors="raise"
    )
    merged = merged.sort_values(by=["analysis_origin", "seed"], kind="mergesort")
    return {
        "common_seed_count": int(len(merged)),
        "wins": int((merged["delta_r2"] > 0).sum()),
        "losses_or_ties": int((merged["delta_r2"] <= 0).sum()),
        "mean_delta_r2": float(merged["delta_r2"].mean()),
        "median_delta_r2": float(merged["delta_r2"].median()),
        "per_seed": [
            {
                "analysis_origin": str(row.analysis_origin),
                "seed": int(row.seed),
                "strategy_run_id": str(row.run_id),
                "target_only_run_id": str(row.target_only_run_id),
                "strategy_r2": float(row.target_r2),
                "target_only_r2": float(row.target_only_r2),
                "delta_r2": float(row.delta_r2),
            }
            for row in merged.itertuples(index=False)
        ],
    }


def build_row_payload(
    combined_rows: pd.DataFrame,
    source_artifacts: dict[str, Any],
    baseline_cfg: dict[str, Any],
    baseline_r2: float,
    min_target_eval_rows: int,
) -> dict[str, Any]:
    return {
        "generated_utc": utc_now(),
        "source_artifacts": source_artifacts,
        "baseline_exp002": {
            "run_id": baseline_cfg.get("run_id", "EXP-002_zero_shot_baseline"),
            "target_r2": baseline_r2,
        },
        "selection_rules": [
            "Keep only EXP-003..077 rows where seed=1337, status=complete, and target_r2 is present.",
            "Keep only EXP-078..127 rows where metrics_exists=true and target_r2 is present.",
        ],
        "row_count": int(len(combined_rows)),
        "min_target_eval_rows": int(min_target_eval_rows),
        "rows": dataframe_to_records(combined_rows),
    }


def build_grouped_payload(
    combined_rows: pd.DataFrame,
    grouped_records: list[dict[str, Any]],
    source_artifacts: dict[str, Any],
    baseline_cfg: dict[str, Any],
    baseline_r2: float,
    min_target_eval_rows: int,
    original_grouped_reference: dict[str, Any] | None,
    repair_grouped_reference: dict[str, Any] | None,
    best_repair_only_source_group: dict[str, Any] | None,
    best_consolidated_source_group: dict[str, Any] | None,
    best_consolidated_nonfull_group: dict[str, Any] | None,
    best_single_run: dict[str, Any] | None,
) -> dict[str, Any]:
    repair_rows = combined_rows[combined_rows["analysis_origin"] == "repair_non1337"].copy()
    original_rows = combined_rows[combined_rows["analysis_origin"] == "original_valid_seed1337"].copy()

    pairwise_vs_target_only = build_pairwise_strategy_summary(grouped_records)
    best_mean_source_strategy_per_n = build_best_source_strategy_per_n(grouped_records)

    payload = {
        "generated_utc": utc_now(),
        "source_artifacts": source_artifacts,
        "baseline_exp002": {
            "run_id": baseline_cfg.get("run_id", "EXP-002_zero_shot_baseline"),
            "target_r2": baseline_r2,
            "source_cluster": baseline_cfg.get("source_cluster"),
            "target_cluster": baseline_cfg.get("target_cluster"),
            "regime": baseline_cfg.get("regime"),
        },
        "counts": {
            "original_valid_seed1337_rows": int(len(original_rows)),
            "repair_non1337_rows": int(len(repair_rows)),
            "consolidated_rows": int(len(combined_rows)),
            "strategy_n_groups": int(len(grouped_records)),
        },
        "structural_repair_summary": {
            "repair_rows": int(len(repair_rows)),
            "repair_target_overlap_n_unique": sorted_unique_int(repair_rows["target_overlap_n"]),
            "repair_source_overlap_n_unique": sorted_unique_int(repair_rows["source_overlap_n"]),
            "repair_actual_eval_n_zero_count": int((repair_rows["actual_eval_n"] == 0).sum()),
            "repair_rows_below_min_target_eval_rows": int(repair_rows["below_min_target_eval_rows"].sum()),
            "repair_below_min_run_ids": repair_rows.loc[
                repair_rows["below_min_target_eval_rows"], "run_id"
            ].tolist(),
            "repair_capped_calibration_rows": int(repair_rows["calibration_n_capped"].sum()),
        },
        "provenance_summary": {
            "original_valid_seed1337": {
                "seeds": sorted_unique_int(original_rows["seed"]),
                "target_overlap_n_unique": sorted_unique_int(original_rows["target_overlap_n"]),
                "actual_eval_n_range": [
                    int(original_rows["actual_eval_n"].min()),
                    int(original_rows["actual_eval_n"].max()),
                ],
            },
            "repair_non1337": {
                "seeds": sorted_unique_int(repair_rows["seed"]),
                "target_overlap_n_unique": sorted_unique_int(repair_rows["target_overlap_n"]),
                "actual_eval_n_range": [
                    int(repair_rows["actual_eval_n"].min()),
                    int(repair_rows["actual_eval_n"].max()),
                ],
            },
        },
        "best_repair_only_source_group": best_repair_only_source_group,
        "best_consolidated_source_group": best_consolidated_source_group,
        "best_consolidated_nonfull_group": best_consolidated_nonfull_group,
        "best_single_run": best_single_run,
        "grouped_r2_stats": grouped_records,
        "best_mean_source_strategy_per_n": best_mean_source_strategy_per_n,
        "pairwise_vs_target_only": pairwise_vs_target_only,
        "conclusion_flags": {
            "repair_overlap_constant_223": sorted_unique_int(repair_rows["target_overlap_n"]) == [223],
            "repair_zero_eval_failures_resolved": int((repair_rows["actual_eval_n"] == 0).sum()) == 0,
            "any_group_mean_above_exp002": any(
                record["target_r2_mean"] > baseline_r2 for record in grouped_records
            ),
            "any_group_median_above_exp002": any(
                record["target_r2_median"] > baseline_r2 for record in grouped_records
            ),
            "full_target_rows_below_min_target_eval_rows": int(
                combined_rows[
                    (combined_rows["strategy"] == "full_target")
                    & combined_rows["below_min_target_eval_rows"]
                ].shape[0]
            ),
            "mixed_target_overlap_panel": True,
        },
        "analysis_scope": {
            "min_target_eval_rows": int(min_target_eval_rows),
            "mixed_panel_note": (
                "The consolidated panel is not a pure frozen-universe seed study: "
                "original seed-1337 rows use target_overlap_n=2459, while repaired 2024/2025 rows use target_overlap_n=223."
            ),
            "calibration_capping_note": (
                "Repaired N=200 and N=500 rows cap effective_n_target_labels at 173 to preserve a 50-row evaluation holdout."
            ),
        },
        "reference_artifact_summary": {
            "original_grouped_json_present": original_grouped_reference is not None,
            "repair_grouped_json_present": repair_grouped_reference is not None,
            "existing_repair_only_best_mean_target_r2": extract_existing_repair_best_mean(
                repair_grouped_reference
            ),
        },
        "interpretation_notes": [
            "The repaired reruns are structurally sound: all repaired rows have metrics, overlap_total stays fixed at 223, and no repaired row collapses to actual_eval_n=0.",
            "Structural soundness does not translate into strong predictive results: no consolidated strategy/N grouped mean or median target R² exceeds the EXP-002 zero-shot baseline of 0.1070.",
            "Best repair-only two-seed source-using mean target R² remains weak; the repaired panel peaks at stacked N=100 with mean target R² near 0.0613.",
            "Adding the original valid seed-1337 row raises the best consolidated source-using grouped mean to stacked N=100 at about 0.0763, still below the zero-shot baseline.",
            "The repaired full_target rows are included for completeness but remain caveated because actual_eval_n=45 is below min_target_eval_rows=50.",
            "Across-seed dispersion in the consolidated artifact reflects both target-label sampling and the cohort-size shift between the original seed-1337 row and the repaired non-1337 reruns.",
        ],
    }
    return payload


def build_summary_text(
    grouped_payload: dict[str, Any],
    best_repair_only_source_group: dict[str, Any] | None,
    best_consolidated_source_group: dict[str, Any] | None,
) -> str:
    repair_summary = grouped_payload["structural_repair_summary"]
    counts = grouped_payload["counts"]
    baseline_r2 = grouped_payload["baseline_exp002"]["target_r2"]
    best_repair_text = "n/a"
    if best_repair_only_source_group is not None:
        best_repair_text = (
            f"{best_repair_only_source_group['strategy']} at N={best_repair_only_source_group['n_target_labels']} "
            f"(mean target R2={best_repair_only_source_group['target_r2_mean']:.4f})"
        )
    best_consolidated_text = "n/a"
    if best_consolidated_source_group is not None:
        best_consolidated_text = (
            f"{best_consolidated_source_group['strategy']} at N={best_consolidated_source_group['n_target_labels']} "
            f"(mean target R2={best_consolidated_source_group['target_r2_mean']:.4f}, "
            f"median={best_consolidated_source_group['target_r2_median']:.4f})"
        )

    return "\n".join(
        [
            "Post-repair consolidation summary",
            "================================",
            "",
            f"- Consolidated rows: {counts['consolidated_rows']} total = "
            f"{counts['original_valid_seed1337_rows']} original valid seed-1337 rows + "
            f"{counts['repair_non1337_rows']} repaired non-1337 rows.",
            f"- Structural repair status: repaired overlap stays fixed at {repair_summary['repair_target_overlap_n_unique']}, "
            f"zero repaired rows have actual_eval_n=0, and {repair_summary['repair_capped_calibration_rows']} repaired rows are calibration-capped.",
            f"- Full-target caveat: {repair_summary['repair_rows_below_min_target_eval_rows']} repaired full_target row(s) "
            f"still fall below min_target_eval_rows=50 because actual_eval_n=45.",
            f"- Best repair-only source-using grouped mean: {best_repair_text}.",
            f"- Best consolidated source-using grouped mean: {best_consolidated_text}.",
            f"- EXP-002 zero-shot reference: target R2={baseline_r2:.4f}. "
            f"No consolidated grouped mean or median exceeds this baseline.",
            "- Interpretation: the repaired pipeline is structurally sound, but the repaired metrics remain scientifically weak; "
            "the consolidated panel does not justify a claim that few-shot transfer beats the zero-shot baseline.",
            "- Caveat: the consolidated panel mixes the original seed-1337 target_overlap_n=2459 cohort with repaired target_overlap_n=223 cohorts, "
            "so across-seed dispersion is not a pure frozen-universe estimate.",
        ]
    ) + "\n"


def build_pairwise_strategy_summary(
    grouped_records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for strategy in SOURCE_USING_STRATEGIES:
        per_seed_rows: list[dict[str, Any]] = []
        for record in grouped_records:
            if record["strategy"] != strategy:
                continue
            comparison = record.get("vs_target_only_same_n")
            if not comparison:
                continue
            for entry in comparison["per_seed"]:
                per_seed_rows.append(
                    {
                        "n_target_labels": record["n_target_labels"],
                        **entry,
                    }
                )
        deltas = [float(entry["delta_r2"]) for entry in per_seed_rows]
        if not deltas:
            continue
        summary[strategy] = {
            "comparable_rows": int(len(per_seed_rows)),
            "wins": int(sum(delta > 0 for delta in deltas)),
            "losses_or_ties": int(sum(delta <= 0 for delta in deltas)),
            "mean_delta_r2": float(sum(deltas) / len(deltas)),
            "median_delta_r2": float(pd.Series(deltas).median()),
            "per_seed": per_seed_rows,
        }
    return summary


def build_best_source_strategy_per_n(
    grouped_records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    best_by_n: dict[str, dict[str, Any]] = {}
    available_n_values = sorted(
        {
            int(record["n_target_labels"])
            for record in grouped_records
            if record["strategy"] in SOURCE_USING_STRATEGIES
        }
    )
    for n_value in available_n_values:
        candidates = [
            record
            for record in grouped_records
            if record["strategy"] in SOURCE_USING_STRATEGIES
            and int(record["n_target_labels"]) == n_value
        ]
        if not candidates:
            continue
        best = max(candidates, key=lambda record: record["target_r2_mean"])
        best_by_n[str(n_value)] = {
            "strategy": best["strategy"],
            "n_target_labels": best["n_target_labels"],
            "target_r2_mean": best["target_r2_mean"],
            "target_r2_median": best["target_r2_median"],
            "delta_vs_exp002_mean": best["delta_vs_exp002_mean"],
        }
    return best_by_n


def extract_best_group(
    grouped_records: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> dict[str, Any] | None:
    candidates = [record for record in grouped_records if predicate(record)]
    if not candidates:
        return None
    best = max(candidates, key=lambda record: record["target_r2_mean"])
    return {
        "strategy": best["strategy"],
        "n_target_labels": best["n_target_labels"],
        "target_r2_mean": best["target_r2_mean"],
        "target_r2_median": best["target_r2_median"],
        "target_r2_std": best["target_r2_std"],
        "delta_vs_exp002_mean": best["delta_vs_exp002_mean"],
        "best_run_id": best["best_run_id"],
        "best_run_seed": best["best_run_seed"],
        "group_caveats": best["group_caveats"],
    }


def extract_best_single_run(combined_rows: pd.DataFrame) -> dict[str, Any] | None:
    if combined_rows.empty:
        return None
    best_index = pd.to_numeric(combined_rows["target_r2"], errors="raise").idxmax()
    row = combined_rows.loc[best_index]
    return {
        "run_id": str(row["run_id"]),
        "analysis_origin": str(row["analysis_origin"]),
        "strategy": str(row["strategy"]),
        "n_target_labels": int(row["n_target_labels"]),
        "seed": int(row["seed"]),
        "target_r2": float(row["target_r2"]),
    }


def flatten_grouped_records(grouped_records: list[dict[str, Any]]) -> pd.DataFrame:
    flattened: list[dict[str, Any]] = []
    for record in grouped_records:
        row = dict(record)
        comparison = row.pop("vs_target_only_same_n", None)
        row["seeds"] = json.dumps(row["seeds"])
        row["analysis_origins"] = json.dumps(row["analysis_origins"])
        row["requested_n_target_labels_unique"] = json.dumps(row["requested_n_target_labels_unique"])
        row["effective_n_target_labels_unique"] = json.dumps(row["effective_n_target_labels_unique"])
        row["actual_cal_n_unique"] = json.dumps(row["actual_cal_n_unique"])
        row["actual_eval_n_unique"] = json.dumps(row["actual_eval_n_unique"])
        row["source_overlap_n_unique"] = json.dumps(row["source_overlap_n_unique"])
        row["target_overlap_n_unique"] = json.dumps(row["target_overlap_n_unique"])
        row["min_target_eval_rows"] = json.dumps(row["min_target_eval_rows"])
        row["group_caveats"] = " | ".join(row["group_caveats"])
        if comparison is None:
            row["vs_target_only_common_seed_count"] = None
            row["vs_target_only_wins"] = None
            row["vs_target_only_losses_or_ties"] = None
            row["vs_target_only_mean_delta_r2"] = None
            row["vs_target_only_median_delta_r2"] = None
            row["vs_target_only_per_seed"] = ""
        else:
            row["vs_target_only_common_seed_count"] = comparison["common_seed_count"]
            row["vs_target_only_wins"] = comparison["wins"]
            row["vs_target_only_losses_or_ties"] = comparison["losses_or_ties"]
            row["vs_target_only_mean_delta_r2"] = comparison["mean_delta_r2"]
            row["vs_target_only_median_delta_r2"] = comparison["median_delta_r2"]
            row["vs_target_only_per_seed"] = json.dumps(comparison["per_seed"])
        flattened.append(row)
    return pd.DataFrame(flattened)


def extract_existing_repair_best_mean(
    repair_grouped_reference: dict[str, Any] | None,
) -> float | None:
    if not repair_grouped_reference:
        return None
    by_strategy_n = repair_grouped_reference.get("by_strategy_n", [])
    if not by_strategy_n:
        return None
    best = max(by_strategy_n, key=lambda record: float(record.get("r2_mean", float("-inf"))))
    return float(best["r2_mean"])


def sorted_unique_int(series: pd.Series) -> list[int]:
    values = [int(value) for value in series.dropna().tolist()]
    return sorted(dict.fromkeys(values))


def sorted_unique_str(series: pd.Series) -> list[str]:
    values = [str(value) for value in series.dropna().tolist()]
    return sorted(dict.fromkeys(values))


def population_std(series: pd.Series) -> float:
    values = [float(value) for value in series.dropna().tolist()]
    if len(values) <= 1:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return variance ** 0.5


def iqr(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float(values.quantile(0.75) - values.quantile(0.25))


def dataframe_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {key: to_jsonable(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, numbers.Real):
        return float(value)
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
