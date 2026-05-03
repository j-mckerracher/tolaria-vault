#!/usr/bin/env python3
"""
FRESCO v2.0 Chunked Pilot Script

Extracts one month of data and writes in v1.0-compatible hourly chunks.
Output location: /depot/sbagchi/data/josh/FRESCO/chunks-v2.0/

Usage:
    python run_pilot_chunked.py --cluster anvil --year 2022 --month 8
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extractors.anvil import AnvilExtractor
from transforms import memory, time as time_transforms
from validation.schema import SchemaValidator
from output.chunked_writer import ChunkedWriter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pilot_chunked_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_pilot_chunked(
    cluster: str,
    year: int,
    month: int,
    source_data_dir: str,
    clusters_json_path: str,
    output_base_dir: str
):
    """
    Run pilot extraction with chunked output.
    
    Args:
        cluster: Cluster name ("anvil", "conte", or "stampede")
        year: Year to extract
        month: Month to extract
        source_data_dir: Base directory for source data
        clusters_json_path: Path to clusters.json
        output_base_dir: Base directory for chunked output
    """
    logger.info("=" * 80)
    logger.info("FRESCO v2.0 CHUNKED PILOT RUN")
    logger.info("=" * 80)
    logger.info(f"Cluster: {cluster}")
    logger.info(f"Period: {year:04d}-{month:02d}")
    logger.info(f"Output: {output_base_dir}")
    logger.info("")
    
    # =========================================================================
    # STAGE 1: EXTRACTION
    # =========================================================================
    logger.info("=" * 80)
    logger.info("STAGE 1: EXTRACTION")
    logger.info("=" * 80)
    
    if cluster == "anvil":
        extractor = AnvilExtractor(source_data_dir, clusters_json_path)
    else:
        raise NotImplementedError(f"Extractor for {cluster} not yet implemented")
    
    df = extractor.extract_month(year, month)
    logger.info(f"✓ Extracted {len(df):,} jobs")
    logger.info("")
    
    # =========================================================================
    # STAGE 2: TRANSFORMATION
    # =========================================================================
    logger.info("=" * 80)
    logger.info("STAGE 2: TRANSFORMATION")
    logger.info("=" * 80)
    
    # Memory normalization
    df = memory.normalize_memory_units(df, cluster)
    df = memory.compute_memory_fractions(df)
    logger.info("✓ Memory normalization complete")
    
    # Time normalization
    df = time_transforms.normalize_timelimit(df, cluster)
    df = time_transforms.compute_derived_time_fields(df)
    logger.info("✓ Time normalization complete")
    logger.info("")
    
    # =========================================================================
    # STAGE 3: VALIDATION
    # =========================================================================
    logger.info("=" * 80)
    logger.info("STAGE 3: VALIDATION")
    logger.info("=" * 80)
    
    validator = SchemaValidator()
    validation_passed, errors, warnings = validator.validate(df)
    
    if not validation_passed:
        logger.error("❌ Validation FAILED")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    if warnings:
        logger.warning(f"⚠ {len(warnings)} warnings")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    logger.info("✓ Validation PASSED")
    
    # Generate validation report
    validation_report = {
        "total_jobs": len(df),
        "clusters": {cluster: len(df)},
        "date_range": {
            "start": str(df["submit_time"].min()),
            "end": str(df["submit_time"].max())
        },
        "memory_coverage": (~df["peak_memory_gb"].isna()).sum() / len(df) * 100,
        "null_rates": {
            col: (df[col].isna().sum() / len(df) * 100)
            for col in df.columns
            if df[col].isna().any()
        },
        "validation_passed": True,
        "error_count": 0,
        "warning_count": len(warnings)
    }
    
    logger.info("")
    logger.info("VALIDATION REPORT:")
    logger.info(f"  Total jobs: {validation_report['total_jobs']:,}")
    logger.info(f"  Clusters: {validation_report['clusters']}")
    logger.info(f"  Date range: {validation_report['date_range']['start']} to {validation_report['date_range']['end']}")
    logger.info(f"  Memory coverage: {validation_report['memory_coverage']:.1f}%")
    logger.info(f"  Validation: PASSED ✓")
    logger.info("")
    
    # =========================================================================
    # STAGE 4: CHUNKED OUTPUT
    # =========================================================================
    logger.info("=" * 80)
    logger.info("STAGE 4: CHUNKED OUTPUT")
    logger.info("=" * 80)
    
    writer = ChunkedWriter(output_base_dir)
    chunk_stats = writer.write_chunks(df, append=False)  # First month, no append
    
    logger.info("")
    logger.info(f"✓ Wrote {chunk_stats['total_chunks']} hourly chunks")
    logger.info(f"  Total jobs: {chunk_stats['total_jobs']:,}")
    logger.info(f"  Output location: {output_base_dir}")
    logger.info("")
    
    # =========================================================================
    # SUMMARY STATISTICS
    # =========================================================================
    logger.info("=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    
    logger.info(f"Jobs extracted: {len(df):,}")
    logger.info(f"Date range: {df['submit_time'].min()} to {df['submit_time'].max()}")
    logger.info(f"Hourly chunks: {chunk_stats['total_chunks']}")
    
    if "partition" in df.columns:
        partition_counts = df["partition"].value_counts().to_dict()
        logger.info(f"Partitions: {partition_counts}")
    
    failed_count = df["failed"].sum() if "failed" in df.columns else 0
    logger.info(f"Failed jobs: {failed_count} ({failed_count/len(df)*100:.1f}%)")
    
    timed_out_count = df["timed_out"].sum() if "timed_out" in df.columns else 0
    logger.info(f"Timed out: {timed_out_count} ({timed_out_count/len(df)*100:.1f}%)")
    
    oom_count = df["oom_killed"].sum() if "oom_killed" in df.columns else 0
    logger.info(f"OOM killed: {oom_count} ({oom_count/len(df)*100:.1f}%)")
    
    logger.info("")
    logger.info("Memory usage:")
    if "peak_memory_fraction" in df.columns:
        mem_frac = df["peak_memory_fraction"].dropna()
        if len(mem_frac) > 0:
            logger.info(f"  Mean peak_memory_fraction: {mem_frac.mean():.3f}")
            logger.info(f"  Median peak_memory_fraction: {mem_frac.median():.3f}")
            logger.info(f"  95th percentile: {mem_frac.quantile(0.95):.3f}")
    
    logger.info("")
    logger.info("CPU efficiency:")
    if "cpu_efficiency" in df.columns:
        cpu_eff = df["cpu_efficiency"].dropna()
        if len(cpu_eff) > 0:
            logger.info(f"  Mean: {cpu_eff.mean():.1f}%")
            logger.info(f"  Median: {cpu_eff.median():.1f}%")
    
    logger.info("")
    logger.info("Chunk distribution:")
    for chunk_info in chunk_stats["chunks_written"][:5]:  # Show first 5
        logger.info(f"  {chunk_info['path']}: {chunk_info['jobs']:,} jobs, {chunk_info['size_mb']:.2f} MB")
    if len(chunk_stats["chunks_written"]) > 5:
        logger.info(f"  ... and {len(chunk_stats['chunks_written']) - 5} more chunks")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("PILOT RUN COMPLETE ✓")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Next steps:")
    logger.info(f"  1. Inspect chunks: {output_base_dir}")
    logger.info(f"  2. Compare to v1.0: /depot/sbagchi/data/josh/FRESCO/chunks/{year:04d}/{month:02d}/")
    logger.info(f"  3. If satisfactory, proceed to full production run")


def main():
    parser = argparse.ArgumentParser(description="FRESCO v2.0 Chunked Pilot Extraction")
    parser.add_argument("--cluster", required=True, choices=["anvil", "conte", "stampede"],
                        help="Cluster to extract")
    parser.add_argument("--year", type=int, required=True, help="Year to extract")
    parser.add_argument("--month", type=int, required=True, help="Month to extract")
    parser.add_argument("--source-data-dir", 
                        default="/depot/sbagchi/www/fresco/repository",
                        help="Source data directory")
    parser.add_argument("--clusters-json",
                        default="../config/clusters.json",
                        help="Path to clusters.json")
    parser.add_argument("--output-dir",
                        default="/depot/sbagchi/data/josh/FRESCO/chunks-v2.0",
                        help="Output directory for chunked data")
    
    args = parser.parse_args()
    
    try:
        run_pilot_chunked(
            cluster=args.cluster,
            year=args.year,
            month=args.month,
            source_data_dir=args.source_data_dir,
            clusters_json_path=args.clusters_json,
            output_base_dir=args.output_dir
        )
    except Exception as e:
        logger.exception("Fatal error in pilot run")
        sys.exit(1)


if __name__ == "__main__":
    main()
