#!/usr/bin/env python3
"""
FRESCO v2.0 Conte Pilot Script

Extracts one month of Conte data (2015-03) and writes to chunks-v2.0.

Usage:
    python run_pilot_conte.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extractors.conte import ConteExtractor
from transforms import memory, time as time_transforms
from validation.schema import SchemaValidator
from output.chunked_writer import ChunkedWriter
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pilot_conte_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("FRESCO v2.0 CONTE PILOT RUN")
    logger.info("=" * 80)
    logger.info("Cluster: conte")
    logger.info("Period: 2015-03 (Conte/Stampede overlap month)")
    logger.info("Output: /depot/sbagchi/data/josh/FRESCO/chunks-v2.0")
    logger.info("")
    
    # Configuration
    cluster = "conte"
    year = 2015
    month = 3
    source_data_dir = "/depot/sbagchi/www/fresco/repository"
    clusters_json_path = "../config/clusters.json"
    output_base_dir = "/depot/sbagchi/data/josh/FRESCO/chunks-v2.0"
    
    # =========================================================================
    # STAGE 1: EXTRACTION
    # =========================================================================
    logger.info("=" * 80)
    logger.info("STAGE 1: EXTRACTION")
    logger.info("=" * 80)
    
    extractor = ConteExtractor(source_data_dir, clusters_json_path)
    df = extractor.extract_month(year, month)
    
    if df.empty:
        logger.error("No data extracted!")
        sys.exit(1)
    
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
    logger.info("")
    
    # =========================================================================
    # STAGE 4: CHUNKED OUTPUT
    # =========================================================================
    logger.info("=" * 80)
    logger.info("STAGE 4: CHUNKED OUTPUT")
    logger.info("=" * 80)
    
    writer = ChunkedWriter(output_base_dir)
    chunk_stats = writer.write_chunks(df, append=True)  # Append to existing Anvil data
    
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
    
    logger.info("")
    logger.info("Memory usage:")
    if "peak_memory_fraction" in df.columns:
        mem_frac = df["peak_memory_fraction"].dropna()
        if len(mem_frac) > 0:
            logger.info(f"  Mean peak_memory_fraction: {mem_frac.mean():.3f}")
            logger.info(f"  Median peak_memory_fraction: {mem_frac.median():.3f}")
            logger.info(f"  95th percentile: {mem_frac.quantile(0.95):.3f}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("CONTE PILOT RUN COMPLETE ✓")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Next steps:")
    logger.info(f"  1. Compare to Anvil data in same month")
    logger.info(f"  2. Measure cross-cluster offsets (Conte vs Anvil)")
    logger.info(f"  3. Run Stampede pilot for 2015-03")
    logger.info(f"  4. Three-way comparison (Conte + Stampede + Anvil if any)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error in Conte pilot run")
        sys.exit(1)
