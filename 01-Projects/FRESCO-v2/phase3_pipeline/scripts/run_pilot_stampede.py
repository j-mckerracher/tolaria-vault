#!/usr/bin/env python3
"""
Stampede Pilot: Extract 2015-03 for cross-cluster validation with Conte.

This pilot tests:
1. Stampede accounting parsing (timelimit ×60 conversion!)
2. Node-partitioned TACC_Stats aggregation
3. Memory in KB → GB conversion
4. Same month as Conte pilot (enables cross-validation)

Output: Chunked parquet files in /depot/sbagchi/data/josh/FRESCO/chunks-v2.0/
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.stampede import StampedeExtractor
from src.transformers.normalizer import Normalizer
from src.output.chunked_writer import ChunkedWriter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/stampede_pilot_{datetime.now():%Y%m%d_%H%M%S}.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Run Stampede pilot for 2015-03."""
    
    # Configuration
    SOURCE_PATH = Path("/depot/sbagchi/www/fresco/repository")
    CLUSTERS_JSON = Path(__file__).parent.parent / "phase2_outputs" / "clusters.json"
    OUTPUT_PATH = Path("/depot/sbagchi/data/josh/FRESCO/chunks-v2.0")
    PILOT_YEAR = 2015
    PILOT_MONTH = 3  # March 2015 - same as Conte pilot
    
    logger.info("=" * 60)
    logger.info("STAMPEDE PILOT: Extracting 2015-03")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    # Step 1: Extract
    logger.info("\n[STEP 1] EXTRACTION")
    extractor = StampedeExtractor(SOURCE_PATH, CLUSTERS_JSON)
    raw_df = extractor.extract_month(PILOT_YEAR, PILOT_MONTH)
    
    if raw_df.empty:
        logger.error("No data extracted!")
        return 1
    
    logger.info(f"Extracted {len(raw_df):,} jobs")
    
    # Validate timelimit conversion (CRITICAL)
    logger.info("\n[VALIDATION] Timelimit Conversion Check")
    logger.info(f"  timelimit_unit_original: {raw_df['timelimit_unit_original'].unique()}")
    sample = raw_df[raw_df['timelimit_original'].notna()].head(3)
    for _, row in sample.iterrows():
        logger.info(f"  Original: {row['timelimit_original']} minutes → {row['timelimit_sec']} seconds")
    
    # Step 2: Normalize
    logger.info("\n[STEP 2] NORMALIZATION")
    normalizer = Normalizer()
    normalized_df = normalizer.transform(raw_df)
    
    logger.info(f"Normalized {len(normalized_df):,} jobs")
    
    # Validate memory normalization (CRITICAL)
    logger.info("\n[VALIDATION] Memory Normalization Check")
    mem_coverage = (~normalized_df['peak_memory_gb'].isna()).sum() / len(normalized_df) * 100
    logger.info(f"  Memory coverage: {mem_coverage:.1f}%")
    
    if mem_coverage > 0:
        mem_sample = normalized_df[normalized_df['peak_memory_gb'].notna()].head(3)
        for _, row in mem_sample.iterrows():
            logger.info(f"  Job {row['jid']}: {row.get('memory_original_value', 'N/A')} KB → {row['peak_memory_gb']:.2f} GB")
            logger.info(f"    Fraction: {row.get('peak_memory_fraction', 'N/A')}")
    
    # Step 3: Write chunks
    logger.info("\n[STEP 3] WRITE CHUNKS")
    writer = ChunkedWriter(OUTPUT_PATH)
    chunks_written = writer.write_chunks(normalized_df, append=True)
    
    logger.info(f"Wrote {len(chunks_written)} chunks")
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("\n" + "=" * 60)
    logger.info("STAMPEDE PILOT COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Jobs: {len(normalized_df):,}")
    logger.info(f"Chunks: {len(chunks_written)}")
    logger.info(f"Time: {elapsed:.1f} seconds")
    logger.info(f"Output: {OUTPUT_PATH}/2015/03/")
    
    # Validate critical columns
    logger.info("\n[FINAL VALIDATION] Critical Columns")
    for col in ['cluster', 'jid_global', 'timelimit_sec', 'node_memory_gb', 'peak_memory_fraction']:
        coverage = (~normalized_df[col].isna()).sum() / len(normalized_df) * 100
        logger.info(f"  {col}: {coverage:.1f}%")
    
    return 0


if __name__ == '__main__':
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    sys.exit(main())
