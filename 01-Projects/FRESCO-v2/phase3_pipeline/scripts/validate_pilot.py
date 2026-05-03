#!/usr/bin/env python3
"""
FRESCO v2.0 Phase 4: Cross-Cluster Validation

Compare v2.0 pilot output against expected patterns from EXP-011/012/013 research.
Validates that the transformation pipeline correctly addresses v1.0 issues.

Usage:
    python scripts/validate_pilot.py --input pilot_output/ --clusters-json config/clusters.json
"""

import argparse
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Validate FRESCO v2.0 pilot output')
    parser.add_argument('--input', type=str, required=True,
                       help='Path to pilot output directory')
    parser.add_argument('--clusters-json', type=str, default='config/clusters.json',
                       help='Path to clusters.json')
    return parser.parse_args()


def load_pilot_data(input_dir: Path):
    """Load pilot parquet output."""
    parquet_files = list(input_dir.glob('*.parquet'))
    
    if not parquet_files:
        logger.error(f"No parquet files found in {input_dir}")
        return None
    
    logger.info(f"Loading {len(parquet_files)} parquet file(s)")
    
    dfs = []
    for pq_file in parquet_files:
        logger.info(f"  Reading {pq_file.name}")
        df = pd.read_parquet(pq_file)
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(combined)} total jobs")
    
    return combined


def validate_schema_compliance(df: pd.DataFrame) -> dict:
    """Validate that output matches v2.0 schema."""
    logger.info("\n" + "="*80)
    logger.info("VALIDATION 1: Schema Compliance")
    logger.info("="*80)
    
    results = {'passed': True, 'errors': [], 'warnings': []}
    
    # Required columns from v2.0 spec
    required_cols = [
        'jid', 'jid_global', 'cluster',
        'submit_time', 'start_time', 'end_time',
        'timelimit_sec', 'runtime_sec', 'queue_time_sec',
        'nhosts', 'ncores',
        'node_memory_gb', 'node_cores',
        'memory_includes_cache', 'memory_collection_method',
        'exit_code', 'state'
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        results['passed'] = False
        results['errors'].append(f"Missing required columns: {missing}")
        logger.error(f"✗ Missing columns: {missing}")
    else:
        logger.info(f"✓ All {len(required_cols)} required columns present")
    
    # Check for nulls in required columns
    for col in required_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                pct = null_count / len(df) * 100
                if pct > 1:  # More than 1% nulls is an error
                    results['passed'] = False
                    results['errors'].append(f"{col} has {null_count} nulls ({pct:.1f}%)")
                    logger.error(f"✗ {col}: {null_count} nulls ({pct:.1f}%)")
                else:
                    results['warnings'].append(f"{col} has {null_count} nulls ({pct:.2f}%)")
                    logger.warning(f"⚠ {col}: {null_count} nulls ({pct:.2f}%)")
    
    # Check total column count (should be ~65)
    if len(df.columns) < 50:
        results['warnings'].append(f"Only {len(df.columns)} columns (expected ~65)")
        logger.warning(f"⚠ Only {len(df.columns)} columns (expected ~65)")
    else:
        logger.info(f"✓ Schema has {len(df.columns)} columns")
    
    return results


def validate_critical_fixes(df: pd.DataFrame, clusters_json_path: Path) -> dict:
    """Validate that v1.0 critical issues are fixed."""
    logger.info("\n" + "="*80)
    logger.info("VALIDATION 2: Critical Fixes from EXP-011/012/013")
    logger.info("="*80)
    
    results = {'passed': True, 'errors': [], 'warnings': []}
    
    # Load cluster metadata
    with open(clusters_json_path) as f:
        clusters_data = json.load(f)
    
    # Fix #1: Explicit cluster column
    logger.info("\nFix #1: Explicit cluster identifier")
    if 'cluster' in df.columns:
        clusters = df['cluster'].unique()
        logger.info(f"✓ Explicit cluster column present: {clusters}")
        
        invalid = df[~df['cluster'].isin(['stampede', 'conte', 'anvil'])]
        if len(invalid) > 0:
            results['passed'] = False
            results['errors'].append(f"Invalid cluster values: {invalid['cluster'].unique()}")
            logger.error(f"✗ Invalid cluster values found")
    else:
        results['passed'] = False
        results['errors'].append("Missing cluster column")
        logger.error("✗ No cluster column")
    
    # Fix #2: Timelimit in seconds
    logger.info("\nFix #2: Timelimit normalized to seconds")
    if 'timelimit_sec' in df.columns:
        min_tl = df['timelimit_sec'].min()
        max_tl = df['timelimit_sec'].max()
        median_tl = df['timelimit_sec'].median()
        
        logger.info(f"  Min: {min_tl} sec")
        logger.info(f"  Median: {median_tl} sec ({median_tl/3600:.1f} hours)")
        logger.info(f"  Max: {max_tl} sec ({max_tl/3600:.1f} hours)")
        
        if max_tl < 3600:  # Less than 1 hour max is suspicious
            results['passed'] = False
            results['errors'].append(f"Timelimit suspiciously small (max={max_tl} sec)")
            logger.error("✗ Timelimit values suspiciously small (may still be in minutes)")
        else:
            logger.info("✓ Timelimit values in reasonable range (likely seconds)")
    
    # Fix #3: Hardware context populated
    logger.info("\nFix #3: Hardware context from clusters.json")
    if 'node_memory_gb' in df.columns:
        null_hw = df['node_memory_gb'].isna().sum()
        if null_hw > 0:
            results['passed'] = False
            results['errors'].append(f"node_memory_gb has {null_hw} nulls")
            logger.error(f"✗ node_memory_gb missing for {null_hw} jobs")
        else:
            logger.info("✓ node_memory_gb populated for all jobs")
            logger.info(f"  Values: {df['node_memory_gb'].unique()}")
    
    # Fix #4: Memory metadata present
    logger.info("\nFix #4: Memory collection methodology documented")
    metadata_cols = ['memory_includes_cache', 'memory_collection_method', 
                     'memory_aggregation', 'memory_sampling_interval_sec']
    
    for col in metadata_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count == 0:
                if df[col].dtype == 'object':
                    logger.info(f"✓ {col}: {df[col].unique()}")
                else:
                    logger.info(f"✓ {col}: populated")
            else:
                results['errors'].append(f"{col} has {null_count} nulls")
                logger.error(f"✗ {col} missing for {null_count} jobs")
        else:
            results['passed'] = False
            results['errors'].append(f"Missing column: {col}")
            logger.error(f"✗ Missing column: {col}")
    
    # Fix #5: UTC timestamps
    logger.info("\nFix #5: Timestamps in UTC")
    time_cols = ['submit_time', 'start_time', 'end_time']
    for col in time_cols:
        if col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                if df[col].dt.tz is not None:
                    logger.info(f"✓ {col} is timezone-aware: {df[col].dt.tz}")
                else:
                    results['warnings'].append(f"{col} is timezone-naive")
                    logger.warning(f"⚠ {col} is timezone-naive (should be UTC)")
    
    # Fix #6: Memory fractions computed
    logger.info("\nFix #6: Memory fractions for cross-cluster comparison")
    if 'peak_memory_fraction' in df.columns:
        has_fraction = df['peak_memory_fraction'].notna().sum()
        logger.info(f"✓ peak_memory_fraction computed for {has_fraction}/{len(df)} jobs")
        
        mean_frac = df['peak_memory_fraction'].mean()
        median_frac = df['peak_memory_fraction'].median()
        p95_frac = df['peak_memory_fraction'].quantile(0.95)
        
        logger.info(f"  Mean: {mean_frac:.3f}")
        logger.info(f"  Median: {median_frac:.3f}")
        logger.info(f"  95th percentile: {p95_frac:.3f}")
        
        # Check for suspicious values
        over_1 = (df['peak_memory_fraction'] > 1.0).sum()
        if over_1 > len(df) * 0.1:  # More than 10% over capacity
            results['warnings'].append(f"{over_1} jobs with peak_memory_fraction > 1.0")
            logger.warning(f"⚠ {over_1} jobs exceed node capacity (>1.0)")
    
    return results


def validate_data_quality(df: pd.DataFrame) -> dict:
    """Validate data quality and distributions."""
    logger.info("\n" + "="*80)
    logger.info("VALIDATION 3: Data Quality")
    logger.info("="*80)
    
    results = {'passed': True, 'errors': [], 'warnings': []}
    
    # Coverage statistics
    logger.info("\nCoverage Statistics:")
    if 'peak_memory_gb' in df.columns:
        mem_coverage = df['peak_memory_gb'].notna().sum() / len(df) * 100
        logger.info(f"  Memory metrics: {mem_coverage:.1f}%")
        
        if mem_coverage < 95:
            results['warnings'].append(f"Memory coverage only {mem_coverage:.1f}%")
            logger.warning(f"⚠ Low memory coverage")
        else:
            logger.info(f"  ✓ Excellent memory coverage")
    
    if 'cpu_efficiency' in df.columns:
        cpu_coverage = df['cpu_efficiency'].notna().sum() / len(df) * 100
        logger.info(f"  CPU metrics: {cpu_coverage:.1f}%")
    
    # Time consistency
    logger.info("\nTime Consistency:")
    if all(col in df.columns for col in ['submit_time', 'start_time', 'end_time']):
        bad_order = (df['submit_time'] > df['start_time']) | (df['start_time'] > df['end_time'])
        if bad_order.sum() > 0:
            results['errors'].append(f"{bad_order.sum()} jobs with inconsistent time ordering")
            logger.error(f"✗ {bad_order.sum()} jobs have submit > start > end violations")
        else:
            logger.info("✓ All jobs have consistent time ordering (submit ≤ start ≤ end)")
    
    # Value ranges
    logger.info("\nValue Range Checks:")
    
    if 'cpu_efficiency' in df.columns:
        over_100 = (df['cpu_efficiency'] > 105).sum()
        if over_100 > 0:
            results['warnings'].append(f"{over_100} jobs with cpu_efficiency > 105%")
            logger.warning(f"⚠ {over_100} jobs with CPU efficiency > 105%")
        
        very_low = (df['cpu_efficiency'] < 5).sum()
        logger.info(f"  {very_low} jobs with CPU efficiency < 5% (likely idle)")
    
    # Failure rates
    logger.info("\nJob Outcomes:")
    if 'failed' in df.columns:
        fail_rate = df['failed'].sum() / len(df) * 100
        logger.info(f"  Failed: {df['failed'].sum()} ({fail_rate:.1f}%)")
    
    if 'timed_out' in df.columns:
        timeout_rate = df['timed_out'].sum() / len(df) * 100
        logger.info(f"  Timed out: {df['timed_out'].sum()} ({timeout_rate:.1f}%)")
    
    if 'oom_killed' in df.columns:
        oom_rate = df['oom_killed'].sum() / len(df) * 100
        logger.info(f"  OOM killed: {df['oom_killed'].sum()} ({oom_rate:.1f}%)")
    
    return results


def generate_summary_report(df: pd.DataFrame, all_results: dict) -> dict:
    """Generate comprehensive validation summary."""
    logger.info("\n" + "="*80)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*80)
    
    # Overall pass/fail
    all_passed = all(r['passed'] for r in all_results.values())
    total_errors = sum(len(r['errors']) for r in all_results.values())
    total_warnings = sum(len(r['warnings']) for r in all_results.values())
    
    logger.info(f"\nOverall Result: {'PASSED ✓' if all_passed else 'FAILED ✗'}")
    logger.info(f"  Errors: {total_errors}")
    logger.info(f"  Warnings: {total_warnings}")
    
    if total_errors > 0:
        logger.info("\nErrors:")
        for validation_name, result in all_results.items():
            for error in result['errors']:
                logger.error(f"  [{validation_name}] {error}")
    
    if total_warnings > 0:
        logger.info("\nWarnings:")
        for validation_name, result in all_results.items():
            for warning in result['warnings']:
                logger.warning(f"  [{validation_name}] {warning}")
    
    # Summary stats
    logger.info("\n" + "="*80)
    logger.info("DATASET STATISTICS")
    logger.info("="*80)
    
    logger.info(f"\nTotal jobs: {len(df):,}")
    logger.info(f"Columns: {len(df.columns)}")
    
    if 'cluster' in df.columns:
        logger.info(f"\nClusters:")
        for cluster, count in df['cluster'].value_counts().items():
            logger.info(f"  {cluster}: {count:,}")
    
    if 'submit_time' in df.columns:
        logger.info(f"\nDate range:")
        logger.info(f"  Start: {df['submit_time'].min()}")
        logger.info(f"  End: {df['submit_time'].max()}")
    
    if 'partition' in df.columns:
        logger.info(f"\nPartitions:")
        for partition, count in df['partition'].value_counts().head(5).items():
            logger.info(f"  {partition}: {count:,}")
    
    # Create summary dict
    summary = {
        'validation_passed': all_passed,
        'total_errors': total_errors,
        'total_warnings': total_warnings,
        'total_jobs': len(df),
        'columns': len(df.columns),
        'clusters': df['cluster'].value_counts().to_dict() if 'cluster' in df.columns else {},
        'date_range': {
            'start': str(df['submit_time'].min()) if 'submit_time' in df.columns else None,
            'end': str(df['submit_time'].max()) if 'submit_time' in df.columns else None
        },
        'memory_coverage': float(df['peak_memory_gb'].notna().sum() / len(df) * 100) if 'peak_memory_gb' in df.columns else 0,
        'validation_details': all_results
    }
    
    return summary


def main():
    args = parse_args()
    
    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return 1
    
    logger.info("="*80)
    logger.info("FRESCO v2.0 PHASE 4: VALIDATION")
    logger.info("="*80)
    logger.info(f"Input: {input_dir}")
    logger.info(f"Clusters metadata: {args.clusters_json}")
    
    # Load data
    df = load_pilot_data(input_dir)
    if df is None:
        return 1
    
    # Run validations
    all_results = {}
    
    all_results['schema'] = validate_schema_compliance(df)
    all_results['fixes'] = validate_critical_fixes(df, Path(args.clusters_json))
    all_results['quality'] = validate_data_quality(df)
    
    # Generate summary
    summary = generate_summary_report(df, all_results)
    
    # Write summary to file
    summary_file = input_dir / 'phase4_validation_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"\n✓ Validation summary written to {summary_file}")
    
    # Exit code
    if summary['validation_passed']:
        logger.info("\n" + "="*80)
        logger.info("✓ PHASE 4 VALIDATION PASSED")
        logger.info("="*80)
        logger.info("\nReady to proceed to Phase 5: Production Run")
        return 0
    else:
        logger.error("\n" + "="*80)
        logger.error("✗ PHASE 4 VALIDATION FAILED")
        logger.error("="*80)
        logger.error(f"\nFound {summary['total_errors']} errors that must be fixed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
