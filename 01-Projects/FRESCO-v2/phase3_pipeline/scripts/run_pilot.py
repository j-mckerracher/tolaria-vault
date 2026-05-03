#!/usr/bin/env python3
"""
FRESCO v2.0 Pilot Run Script

Run extraction and transformation for a single month (March 2015)
to validate the pipeline before full production.

Usage:
    python scripts/run_pilot.py --month 2015-03 --output pilot_output/
"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from extractors.anvil import AnvilExtractor
from transforms import memory, time as time_transforms
from validation.schema import SchemaValidator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pilot_run.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run FRESCO v2.0 pilot extraction')
    parser.add_argument('--month', type=str, default='2022-08',
                       help='Month to extract (YYYY-MM), default: 2022-08 (Anvil)')
    parser.add_argument('--cluster', type=str, default='anvil',
                       choices=['anvil', 'conte', 'stampede'],
                       help='Cluster to extract')
    parser.add_argument('--source', type=str,
                       default='/depot/sbagchi/www/fresco/repository/',
                       help='Path to source repository')
    parser.add_argument('--output', type=str, default='pilot_output/',
                       help='Output directory')
    parser.add_argument('--clusters-json', type=str,
                       default='config/clusters.json',
                       help='Path to clusters.json')
    return parser.parse_args()


def run_pilot(args):
    """Run pilot extraction and transformation."""
    
    logger.info("="*80)
    logger.info("FRESCO v2.0 PILOT RUN")
    logger.info("="*80)
    logger.info(f"Month: {args.month}")
    logger.info(f"Cluster: {args.cluster}")
    logger.info(f"Source: {args.source}")
    logger.info(f"Output: {args.output}")
    logger.info("="*80)
    
    # Parse month
    year, month = map(int, args.month.split('-'))
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize extractor
    logger.info(f"\n{'='*80}\nSTAGE 1: EXTRACTION\n{'='*80}")
    
    if args.cluster == 'anvil':
        source_path = Path(args.source) / 'Anvil'
        extractor = AnvilExtractor(source_path, Path(args.clusters_json))
    else:
        logger.error(f"Extractor for {args.cluster} not yet implemented in this pilot")
        logger.info("NOTE: Full implementation includes Conte and Stampede extractors")
        logger.info("      This pilot demonstrates the pipeline with Anvil")
        return 1
    
    # Extract data
    try:
        df = extractor.extract_month(year, month)
        logger.info(f"✓ Extracted {len(df)} jobs")
    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}", exc_info=True)
        return 1
    
    if df.empty:
        logger.error("No data extracted, aborting")
        return 1
    
    # Stage 2: Transformation
    logger.info(f"\n{'='*80}\nSTAGE 2: TRANSFORMATION\n{'='*80}")
    
    try:
        # Normalize timestamps
        logger.info("Normalizing timestamps to UTC...")
        df = time_transforms.normalize_timestamps(df, args.cluster)
        
        # Normalize timelimit
        logger.info("Normalizing timelimit to seconds...")
        df = time_transforms.normalize_timelimit(df, args.cluster)
        
        # Compute derived time fields
        logger.info("Computing derived time fields...")
        df = time_transforms.compute_derived_time_fields(df)
        
        # Normalize memory
        logger.info("Normalizing memory units...")
        df = memory.normalize_memory_units(df, args.cluster)
        
        # Compute memory fractions
        logger.info("Computing memory fractions...")
        df = memory.compute_memory_fractions(df)
        
        # Detect OOM kills
        logger.info("Detecting OOM-killed jobs...")
        df = memory.detect_oom_killed(df)
        
        logger.info("✓ Transformation complete")
    except Exception as e:
        logger.error(f"✗ Transformation failed: {e}", exc_info=True)
        return 1
    
    # Stage 3: Validation
    logger.info(f"\n{'='*80}\nSTAGE 3: VALIDATION\n{'='*80}")
    
    validator = SchemaValidator()
    is_valid, errors, warnings = validator.validate(df)
    
    # Print errors and warnings
    if errors:
        logger.error("ERRORS:")
        for error in errors:
            logger.error(f"  - {error}")
    
    if warnings:
        logger.warning("WARNINGS:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    # Generate report
    report = validator.generate_report(df)
    
    logger.info("\nVALIDATION REPORT:")
    logger.info(f"  Total jobs: {report['total_jobs']}")
    logger.info(f"  Clusters: {report['clusters']}")
    logger.info(f"  Date range: {report['date_range']['start']} to {report['date_range']['end']}")
    logger.info(f"  Memory coverage: {report['memory_coverage']:.1f}%")
    logger.info(f"  Validation: {'PASSED ✓' if report['validation_passed'] else 'FAILED ✗'}")
    
    if not is_valid:
        logger.error("Validation failed, not writing output")
        return 1
    
    # Stage 4: Write output
    logger.info(f"\n{'='*80}\nSTAGE 4: OUTPUT\n{'='*80}")
    
    try:
        # Write parquet
        output_file = output_dir / f"{args.cluster}_{args.month.replace('-', '')}.parquet"
        df.to_parquet(output_file, engine='pyarrow', compression='snappy', index=False)
        logger.info(f"✓ Wrote {len(df)} jobs to {output_file}")
        logger.info(f"  File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Write validation report
        report_file = output_dir / f"validation_report_{args.cluster}_{args.month.replace('-', '')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"✓ Wrote validation report to {report_file}")
        
        # Write sample CSV for inspection
        sample_file = output_dir / f"sample_{args.cluster}_{args.month.replace('-', '')}.csv"
        df.head(100).to_csv(sample_file, index=False)
        logger.info(f"✓ Wrote sample (100 rows) to {sample_file}")
        
    except Exception as e:
        logger.error(f"✗ Output write failed: {e}", exc_info=True)
        return 1
    
    # Summary statistics
    logger.info(f"\n{'='*80}\nSUMMARY STATISTICS\n{'='*80}")
    logger.info(f"Jobs extracted: {len(df)}")
    logger.info(f"Date range: {df['submit_time'].min()} to {df['submit_time'].max()}")
    logger.info(f"Partitions: {df['partition'].value_counts().to_dict()}")
    logger.info(f"Failed jobs: {df['failed'].sum()} ({df['failed'].sum()/len(df)*100:.1f}%)")
    logger.info(f"Timed out: {df['timed_out'].sum()} ({df['timed_out'].sum()/len(df)*100:.1f}%)")
    logger.info(f"OOM killed: {df['oom_killed'].sum()} ({df['oom_killed'].sum()/len(df)*100:.1f}%)")
    
    if 'peak_memory_fraction' in df.columns:
        logger.info(f"\nMemory usage:")
        logger.info(f"  Mean peak_memory_fraction: {df['peak_memory_fraction'].mean():.3f}")
        logger.info(f"  Median peak_memory_fraction: {df['peak_memory_fraction'].median():.3f}")
        logger.info(f"  95th percentile: {df['peak_memory_fraction'].quantile(0.95):.3f}")
    
    if 'cpu_efficiency' in df.columns:
        logger.info(f"\nCPU efficiency:")
        logger.info(f"  Mean: {df['cpu_efficiency'].mean():.1f}%")
        logger.info(f"  Median: {df['cpu_efficiency'].median():.1f}%")
    
    logger.info(f"\n{'='*80}")
    logger.info("PILOT RUN COMPLETE ✓")
    logger.info("="*80)
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Inspect output: {output_file}")
    logger.info(f"  2. Review validation report: {report_file}")
    logger.info(f"  3. Check sample: {sample_file}")
    logger.info(f"  4. If satisfactory, proceed to full production run")
    
    return 0


if __name__ == '__main__':
    args = parse_args()
    sys.exit(run_pilot(args))
