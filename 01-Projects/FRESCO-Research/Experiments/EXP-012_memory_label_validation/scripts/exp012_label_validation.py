#!/usr/bin/env python3
"""EXP-012: Memory label validation across clusters.

Diagnostic experiment to understand why EXP-011 showed catastrophic cross-site
transfer failures (R² = -21). Tests hypotheses about label definition mismatches:

1. Units: Are memory values in consistent units (KB/MB/bytes)?
2. Aggregation: For multi-node jobs, is peak_memused sum or max per node?
3. Scale: Do typical values match known node RAM sizes?
4. Distribution: Are there systematic offsets/scale factors between clusters?

Outputs validation metrics and diagnostics to guide recalibration strategies.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


CLUSTERS = ["S", "C", "NONE"]

# Known node RAM sizes (approximate) for sanity checks
NODE_RAM_GB = {
    "S": 32,    # Stampede: 32 GB per node (typical)
    "C": 128,   # Conte: 128 GB per node (typical)
    "NONE": 256 # Anvil: 256 GB per node (typical)
}


def load_sample_data(input_dir: str, threads: int = 8, sample_frac: float = 0.01) -> pd.DataFrame:
    """Load a sample of FRESCO data with memory metrics for validation.
    
    Args:
        input_dir: Path to FRESCO chunks directory
        threads: Number of DuckDB threads
        sample_frac: Fraction of data to sample (default 1%)
    
    Returns:
        DataFrame with job-level peak memory and metadata
    """
    # Use data depot for temp files
    temp_db_dir = "/depot/sbagchi/data/josh/FRESCO-Research/Experiments/EXP-012_memory_label_validation/temp"
    os.makedirs(temp_db_dir, exist_ok=True)
    
    con = duckdb.connect()
    con.execute(f"SET threads TO {threads}")
    con.execute("SET memory_limit = '48GB'")
    con.execute(f"SET temp_directory = '{temp_db_dir}'")

    sql = f"""
    WITH raw AS (
        SELECT
            jid,
            CAST(timelimit AS DOUBLE) AS timelimit_raw,
            CAST(ncores AS BIGINT) AS ncores,
            CAST(nhosts AS BIGINT) AS nhosts,
            start_time,
            end_time,
            CAST(value_memused AS DOUBLE) AS value_memused,
            filename,
            CASE
                WHEN filename LIKE '%_S.parquet' THEN 'S'
                WHEN filename LIKE '%_C.parquet' THEN 'C'
                ELSE 'NONE'
            END AS cluster
        FROM read_parquet('{input_dir}/**/*.parquet', filename=true)
        WHERE start_time IS NOT NULL 
          AND end_time IS NOT NULL
          AND RANDOM() < {sample_frac}
    ),
    mem_agg AS (
        SELECT
            cluster,
            jid,
            MAX(value_memused) AS peak_memused,
            AVG(value_memused) AS avg_memused,
            MIN(value_memused) AS min_memused,
            COUNT(CASE WHEN value_memused IS NOT NULL AND value_memused > 0 THEN 1 END) AS mem_sample_count
        FROM raw
        GROUP BY cluster, jid
    ),
    job_agg AS (
        SELECT
            cluster,
            jid,
            MAX(timelimit_raw) AS timelimit_raw,
            MAX(ncores) AS ncores,
            MAX(nhosts) AS nhosts,
            MIN(start_time) AS start_time,
            MAX(end_time) AS end_time
        FROM raw
        GROUP BY cluster, jid
    ),
    combined AS (
        SELECT
            j.jid,
            j.cluster,
            j.ncores,
            j.nhosts,
            CASE WHEN j.cluster = 'S' THEN j.timelimit_raw * 60.0 ELSE j.timelimit_raw END AS timelimit_sec,
            EXTRACT(YEAR FROM j.start_time) * 100 + EXTRACT(MONTH FROM j.start_time) AS yearmonth,
            EXTRACT(EPOCH FROM (j.end_time - j.start_time)) AS runtime_sec,
            m.peak_memused,
            m.avg_memused,
            m.min_memused,
            m.mem_sample_count
        FROM job_agg j
        LEFT JOIN mem_agg m ON j.cluster = m.cluster AND j.jid = m.jid
    )
    SELECT *
    FROM combined
    WHERE mem_sample_count > 0 
      AND peak_memused > 0
      AND runtime_sec > 0
      AND ncores > 0
      AND nhosts > 0
    """

    print(f"[load] Loading {sample_frac*100:.1f}% sample with memory metrics...")
    df = con.execute(sql).fetchdf()
    print(f"[load] Loaded: {len(df):,} jobs")
    
    con.close()
    return df


def validate_units(df: pd.DataFrame) -> pd.DataFrame:
    """Test hypothesis: Are memory units consistent across clusters?
    
    Strategy: Compare typical peak_memused values to known node RAM.
    If units differ, we'll see orders-of-magnitude differences.
    """
    results = []
    
    for cluster in CLUSTERS:
        cdf = df[df.cluster == cluster].copy()
        if len(cdf) == 0:
            continue
        
        # Basic statistics on peak memory
        peak_stats = {
            "cluster": cluster,
            "n_jobs": len(cdf),
            "peak_min": cdf.peak_memused.min(),
            "peak_p01": cdf.peak_memused.quantile(0.01),
            "peak_p10": cdf.peak_memused.quantile(0.10),
            "peak_p50": cdf.peak_memused.quantile(0.50),
            "peak_p90": cdf.peak_memused.quantile(0.90),
            "peak_p99": cdf.peak_memused.quantile(0.99),
            "peak_max": cdf.peak_memused.max(),
            "peak_mean": cdf.peak_memused.mean(),
            "peak_std": cdf.peak_memused.std(),
        }
        
        # Test possible unit interpretations
        node_ram_bytes = NODE_RAM_GB[cluster] * 1024**3
        
        # If values are in bytes, typical values should be < node_ram_bytes
        # If in KB, should be < node_ram_bytes / 1024
        # If in MB, should be < node_ram_bytes / 1024^2
        
        peak_stats["node_ram_gb"] = NODE_RAM_GB[cluster]
        peak_stats["likely_unit_bytes"] = int(peak_stats["peak_p90"] < node_ram_bytes)
        peak_stats["likely_unit_kb"] = int(peak_stats["peak_p90"] < node_ram_bytes / 1024)
        peak_stats["likely_unit_mb"] = int(peak_stats["peak_p90"] < node_ram_bytes / 1024**2)
        peak_stats["likely_unit_gb"] = int(peak_stats["peak_p90"] < node_ram_bytes / 1024**3)
        
        # Ratio of p90 to node RAM (in same units)
        for unit, divisor in [("bytes", 1), ("kb", 1024), ("mb", 1024**2), ("gb", 1024**3)]:
            peak_stats[f"p90_ratio_nodeRAM_{unit}"] = peak_stats["peak_p90"] / (node_ram_bytes / divisor)
        
        results.append(peak_stats)
    
    return pd.DataFrame(results)


def validate_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Test hypothesis: For multi-node jobs, does peak_memused scale with nhosts?
    
    Strategy: If peak is sum across nodes, correlation with nhosts should be strong.
    If peak is max per node, correlation should be weak/zero.
    """
    results = []
    
    for cluster in CLUSTERS:
        cdf = df[(df.cluster == cluster) & (df.nhosts > 1)].copy()
        if len(cdf) < 100:
            print(f"[agg] {cluster}: insufficient multi-node jobs ({len(cdf)}), skipping")
            continue
        
        # Compute correlation: log(peak_memused) vs log(nhosts)
        cdf["log_peak"] = np.log(cdf.peak_memused + 1)
        cdf["log_nhosts"] = np.log(cdf.nhosts + 1)
        
        corr = cdf[["log_peak", "log_nhosts"]].corr().iloc[0, 1]
        
        # Linear regression slope: if sum, slope ≈ 1; if max, slope ≈ 0
        from scipy.stats import linregress
        slope, intercept, r_value, p_value, stderr = linregress(cdf.log_nhosts, cdf.log_peak)
        
        results.append({
            "cluster": cluster,
            "n_multinode_jobs": len(cdf),
            "log_corr_peak_nhosts": corr,
            "linreg_slope": slope,
            "linreg_r2": r_value**2,
            "linreg_pvalue": p_value,
            "interpretation": "likely_sum" if slope > 0.5 else "likely_max_per_node",
        })
    
    return pd.DataFrame(results)


def validate_distributions(df: pd.DataFrame) -> pd.DataFrame:
    """Compute distributional statistics for cross-cluster comparison.
    
    Returns statistics on log(peak_memused) to enable calibration diagnostics.
    """
    results = []
    
    for cluster in CLUSTERS:
        cdf = df[df.cluster == cluster].copy()
        if len(cdf) == 0:
            continue
        
        cdf["log_peak"] = np.log(cdf.peak_memused)
        
        results.append({
            "cluster": cluster,
            "n_jobs": len(cdf),
            "log_peak_mean": cdf.log_peak.mean(),
            "log_peak_std": cdf.log_peak.std(),
            "log_peak_min": cdf.log_peak.min(),
            "log_peak_p25": cdf.log_peak.quantile(0.25),
            "log_peak_p50": cdf.log_peak.quantile(0.50),
            "log_peak_p75": cdf.log_peak.quantile(0.75),
            "log_peak_max": cdf.log_peak.max(),
        })
    
    return pd.DataFrame(results)


def compute_pairwise_offsets(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean log-scale offset between cluster pairs.
    
    If there's a systematic unit/scale difference, we'll see constant offsets.
    """
    results = []
    
    log_means = {}
    for cluster in CLUSTERS:
        cdf = df[df.cluster == cluster]
        if len(cdf) > 0:
            log_means[cluster] = np.log(cdf.peak_memused).mean()
    
    for c1 in CLUSTERS:
        for c2 in CLUSTERS:
            if c1 >= c2:
                continue
            if c1 not in log_means or c2 not in log_means:
                continue
            
            offset = log_means[c2] - log_means[c1]
            scale_factor = np.exp(offset)
            
            results.append({
                "cluster_1": c1,
                "cluster_2": c2,
                "log_offset_c2_minus_c1": offset,
                "scale_factor_c2_over_c1": scale_factor,
                "interpretation": f"{c2} values are {scale_factor:.2f}× {c1} values (on average)",
            })
    
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description="EXP-012: Memory label validation")
    parser.add_argument("--input-dir", required=True, help="Path to FRESCO chunks directory")
    parser.add_argument("--out-dir", required=True, help="Output directory for results")
    parser.add_argument("--threads", type=int, default=8, help="DuckDB threads")
    parser.add_argument("--sample-frac", type=float, default=0.01, help="Fraction of data to sample")
    
    args = parser.parse_args()
    
    print(f"[EXP-012] Memory Label Validation")
    print(f"[config] Input: {args.input_dir}")
    print(f"[config] Output: {args.out_dir}")
    print(f"[config] Threads: {args.threads}")
    print(f"[config] Sample fraction: {args.sample_frac*100:.1f}%")
    
    # Load sample data
    df = load_sample_data(args.input_dir, threads=args.threads, sample_frac=args.sample_frac)
    
    print("\n" + "="*80)
    print("VALIDATION 1: Units")
    print("="*80)
    units_df = validate_units(df)
    print(units_df.to_string(index=False))
    units_df.to_csv(f"{args.out_dir}/exp012_units_validation.csv", index=False)
    
    print("\n" + "="*80)
    print("VALIDATION 2: Aggregation (multi-node jobs)")
    print("="*80)
    agg_df = validate_aggregation(df)
    print(agg_df.to_string(index=False))
    agg_df.to_csv(f"{args.out_dir}/exp012_aggregation_validation.csv", index=False)
    
    print("\n" + "="*80)
    print("VALIDATION 3: Distributions (log scale)")
    print("="*80)
    dist_df = validate_distributions(df)
    print(dist_df.to_string(index=False))
    dist_df.to_csv(f"{args.out_dir}/exp012_distributions.csv", index=False)
    
    print("\n" + "="*80)
    print("VALIDATION 4: Pairwise Offsets")
    print("="*80)
    offset_df = compute_pairwise_offsets(df)
    print(offset_df.to_string(index=False))
    offset_df.to_csv(f"{args.out_dir}/exp012_pairwise_offsets.csv", index=False)
    
    print(f"\n[save] Results written to {args.out_dir}")
    print("EXP-012 complete")


if __name__ == "__main__":
    main()
