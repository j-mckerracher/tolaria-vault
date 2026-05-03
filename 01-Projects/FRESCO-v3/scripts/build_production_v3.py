#!/usr/bin/env python3
"""
FRESCO v3 Production Data Build Script

Processes raw FRESCO shards from /depot/sbagchi/data/josh/FRESCO/chunks/
and outputs to chunks-v3/ with:
- Schema normalization
- Provenance metadata
- Dtype stability
- Full manifests and validation

Usage:
    python build_production_v3.py --config config/production_v3.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import hashlib

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path):
    """Load production configuration."""
    with open(config_path, 'r') as f:
        return json.load(f)


def get_git_commit():
    """Get current git commit hash."""
    import subprocess
    try:
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=Path(__file__).parent.parent,
            text=True
        ).strip()
        return commit
    except Exception as e:
        logger.warning(f"Could not get git commit: {e}")
        return "unknown"


def normalize_schema(df, cluster):
    """
    Apply v3 schema normalization.
    
    Args:
        df: Input dataframe
        cluster: Cluster name (anvil, conte, stampede)
    
    Returns:
        Normalized dataframe with canonical v3 schema
    """
    logger.info(f"Normalizing schema for {cluster}...")
    
    # Ensure cluster column
    df['cluster'] = cluster
    
    # Normalize jid to string
    if 'jid' in df.columns:
        df['jid'] = df['jid'].astype(str)
    
    # Create jid_global (cluster_jid)
    if 'jid' in df.columns:
        df['jid_global'] = df['cluster'] + '_' + df['jid']
    
    # Normalize timelimit to seconds
    if 'timelimit' in df.columns:
        df['timelimit_original'] = df['timelimit'].copy()
        df['timelimit_unit_original'] = 'varies'  # Cluster-specific
        
        # Normalize based on cluster
        if cluster == 'stampede':
            # Stampede timelimit is in minutes
            df['timelimit_sec'] = df['timelimit'] * 60.0
        elif cluster == 'conte':
            # Conte timelimit is in seconds
            df['timelimit_sec'] = df['timelimit'].astype(float)
        else:
            # Anvil (assume seconds)
            df['timelimit_sec'] = df['timelimit'].astype(float)
    
    # Ensure float64 dtypes for numeric columns
    numeric_cols = [
        'peak_memory_gb', 'node_memory_gb', 'peak_memory_fraction',
        'runtime_sec', 'queue_time_sec', 'runtime_fraction',
        'timelimit_sec', 'timelimit_original'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
    
    # Ensure int64 dtypes for integer columns
    int_cols = ['nhosts', 'ncores', 'node_cores', 'gpu_count_per_node']
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    
    logger.info(f"✓ Schema normalized ({len(df)} rows, {len(df.columns)} columns)")
    return df


def add_provenance_metadata(df, cluster):
    """
    Add provenance metadata fields.
    
    Args:
        df: Input dataframe
        cluster: Cluster name
    
    Returns:
        Dataframe with provenance columns
    """
    logger.info("Adding provenance metadata...")
    
    # Memory measurement semantics (cluster-specific)
    if cluster == 'anvil':
        df['memory_includes_cache'] = True
        df['memory_collection_method'] = 'cgroup_memory.max_usage_in_bytes'
        df['memory_aggregation'] = 'max_per_job'
    elif cluster == 'conte':
        df['memory_includes_cache'] = False
        df['memory_collection_method'] = 'tacc_stats_MemUsed'
        df['memory_aggregation'] = 'max_per_job'
    elif cluster == 'stampede':
        df['memory_includes_cache'] = False
        df['memory_collection_method'] = 'tacc_stats_MemUsed'
        df['memory_aggregation'] = 'max_per_job'
    
    df['memory_sampling_interval_sec'] = 300.0  # 5 minutes
    
    logger.info("✓ Provenance metadata added")
    return df


def enforce_batch_schema(df):
    """
    Enforce consistent dtypes across batches to avoid Parquet schema mismatches.
    """
    time_cols = ['time', 'submit_time', 'start_time', 'end_time']
    float_cols = [
        'timelimit', 'timelimit_sec', 'timelimit_original',
        'runtime_sec', 'queue_time_sec', 'runtime_fraction',
        'peak_memory_gb', 'node_memory_gb', 'peak_memory_fraction',
        'value_cpuuser', 'value_gpu', 'value_memused',
        'value_memused_minus_diskcache', 'value_nfs', 'value_block',
        'memory_sampling_interval_sec', 'memory_original_value'
    ]
    int_cols = ['nhosts', 'ncores', 'node_cores', 'gpu_count_per_node']
    bool_cols = ['memory_includes_cache']

    for col in time_cols:
        if col in df.columns:
            series = pd.to_datetime(df[col], errors='coerce', utc=True)
            if pd.api.types.is_datetime64tz_dtype(series.dtype):
                series = series.dt.tz_localize(None)
            df[col] = series.astype('datetime64[us]')

    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')

    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype('boolean')

    for col in df.columns:
        if col in time_cols or col in float_cols or col in int_cols or col in bool_cols:
            continue
        df[col] = df[col].astype('string')

    return df


def align_table_to_schema(table, schema, batch_label):
    """
    Align a PyArrow table to a fixed schema (cast types, add missing columns, drop extras).
    """
    table_cols = set(table.column_names)
    schema_cols = [field.name for field in schema]
    schema_set = set(schema_cols)
    extra_cols = sorted(table_cols - schema_set)
    missing_cols = sorted(schema_set - table_cols)

    if extra_cols:
        logger.warning(f"{batch_label}: dropping extra columns not in schema: {extra_cols}")
    if missing_cols:
        logger.warning(f"{batch_label}: adding missing columns as nulls: {missing_cols}")

    arrays = []
    for field in schema:
        if field.name in table.column_names:
            arr = table[field.name]
            if not arr.type.equals(field.type):
                try:
                    logger.warning(
                        f"{batch_label}: casting column '{field.name}' "
                        f"from {arr.type} to {field.type}"
                    )
                    arr = arr.cast(field.type, safe=False)
                except Exception as e:
                    logger.error(
                        f"{batch_label}: failed casting column '{field.name}' "
                        f"from {arr.type} to {field.type}: {e}"
                    )
                    raise
        else:
            arr = pa.nulls(table.num_rows, type=field.type)
        arrays.append(arr)

    return pa.Table.from_arrays(arrays, schema=schema)


def validate_output(df):
    """
    Run validation checks on output data.
    
    Args:
        df: Output dataframe
    
    Returns:
        Dict with validation results
    """
    logger.info("Running validation checks...")
    
    validation = {
        'row_count': len(df),
        'column_count': len(df.columns),
        'has_cluster': 'cluster' in df.columns,
        'has_jid': 'jid' in df.columns,
        'clusters_present': df['cluster'].unique().tolist() if 'cluster' in df.columns else [],
        'dtype_check': {},
        'missingness': {}
    }
    
    # Check dtypes
    for col in df.columns:
        validation['dtype_check'][col] = str(df[col].dtype)
    
    # Check missingness
    for col in df.columns:
        validation['missingness'][col] = float(df[col].isna().mean())
    
    logger.info(f"✓ Validation complete: {len(df)} rows, {len(df.columns)} columns")
    return validation


def write_manifest(manifest_path, manifest_type, entries):
    """Write manifest file."""
    with open(manifest_path, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')
    logger.info(f"✓ Wrote {manifest_type} manifest: {len(entries)} entries")


def run_production_build(config_path):
    """
    Run production v3 data build.
    
    Args:
        config_path: Path to production config JSON
    """
    logger.info("=" * 80)
    logger.info("FRESCO v3 PRODUCTION DATA BUILD")
    logger.info("=" * 80)
    logger.info(f"Config: {config_path}")
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info("")
    
    # Load config
    config = load_config(config_path)
    input_dir = Path(config['input_dir'])
    output_dir = Path(config['output_dir'])
    run_id = config.get('run_id', f"PROD-{datetime.now().strftime('%Y%m%d')}")
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'manifests').mkdir(exist_ok=True)
    (output_dir / 'validation').mkdir(exist_ok=True)
    (output_dir / 'logs').mkdir(exist_ok=True)
    
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Input: {input_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info("")
    
    # Get git commit
    git_commit = get_git_commit()
    logger.info(f"Git commit: {git_commit}")
    logger.info("")
    
    # Track manifests
    input_manifest = []
    output_manifest = []
    
    # =========================================================================
    # PROCESS INPUT SHARDS
    # =========================================================================
    logger.info("=" * 80)
    logger.info("PROCESSING INPUT SHARDS")
    logger.info("=" * 80)
    
    # Find all input parquet files
    input_files = sorted(input_dir.glob('**/*.parquet'))
    logger.info(f"Found {len(input_files)} input shards")
    
    if len(input_files) == 0:
        logger.error("No input files found!")
        sys.exit(1)
    
    # Process each shard and write incrementally (streaming)
    logger.info("Processing shards (streaming)...")
    
    output_file = output_dir / f'{run_id}_v3.parquet'
    writer = None
    total_rows = 0
    sample_size = int(config.get('validation_sample_size', 100000))
    sample_per_file = int(config.get('validation_sample_per_file', 100))
    sample_df = None
    missing_counts = {}
    dtype_observed = {}
    clusters_seen = set()
    
    logger.info(
        f"Validation sample size: {sample_size} (per file: {sample_per_file})"
    )
    
    for idx, input_file in enumerate(input_files):
        if idx % 1000 == 0:
            logger.info(f"Progress: {idx}/{len(input_files)} files processed...")
        
        # Read shard
        try:
            df = pd.read_parquet(input_file)
        except Exception as e:
            logger.warning(f"Failed to read {input_file}: {e}")
            continue
        
        # Record input manifest
        input_manifest.append({
            'path': str(input_file),
            'size_bytes': input_file.stat().st_size,
            'row_count': len(df),
            'processed_at': datetime.now().isoformat()
        })
        
        # Detect cluster (from path or data or filename suffix)
        if 'cluster' in df.columns:
            cluster = df['cluster'].iloc[0]
        else:
            # Infer from filename suffix (_S, _C, _A) or path or year range
            filename = input_file.name
            file_path_str = str(input_file)
            
            if filename.endswith('_S.parquet') or '_S/' in file_path_str:
                cluster = 'stampede'
            elif filename.endswith('_C.parquet') or '_C/' in file_path_str:
                cluster = 'conte'
            elif filename.endswith('_A.parquet') or '_A/' in file_path_str:
                cluster = 'anvil'
            elif 'anvil' in file_path_str.lower():
                cluster = 'anvil'
            elif 'conte' in file_path_str.lower():
                cluster = 'conte'
            elif 'stampede' in file_path_str.lower():
                cluster = 'stampede'
            else:
                # Anvil files have no suffix; infer from year range (2022+)
                # Extract year from path pattern: .../chunks/YYYY/MM/DD/HH.parquet
                import re
                year_match = re.search(r'/chunks/(\d{4})/', file_path_str)
                if year_match:
                    year = int(year_match.group(1))
                    if year >= 2022:
                        cluster = 'anvil'
                        logger.debug(f"Inferred Anvil from year {year} for {filename}")
                    else:
                        logger.warning(f"Cannot detect cluster for {input_file} (year {year}), skipping")
                        continue
                else:
                    logger.warning(f"Cannot detect cluster for {input_file}, skipping")
                    continue
        
        # Apply transformations
        df = normalize_schema(df, cluster)
        df = add_provenance_metadata(df, cluster)
        df = enforce_batch_schema(df)
        clusters_seen.add(cluster)
        
        # Update validation sample (bounded)
        if sample_size > 0 and len(df) > 0:
            take = min(sample_per_file, len(df))
            if take > 0:
                sample_new = df.sample(n=take, random_state=(idx % 2**32))
                if sample_df is None:
                    sample_df = sample_new
                else:
                    sample_df = pd.concat([sample_df, sample_new], ignore_index=True)
                    if len(sample_df) > sample_size:
                        sample_df = sample_df.sample(
                            n=sample_size,
                            random_state=42
                        )
        
        # Convert to Arrow and align to writer schema
        table = pa.Table.from_pandas(df, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(output_file, table.schema)
        else:
            table = align_table_to_schema(table, writer.schema, f"file_{idx}")
        
        # Accumulate missingness and dtype observations from aligned table
        for field in table.schema:
            missing_counts[field.name] = (
                missing_counts.get(field.name, 0) + table.column(field.name).null_count
            )
            dtype_observed.setdefault(field.name, set()).add(str(field.type))
        
        if idx % 1000 == 0:
            logger.info(
                f"file_{idx}: rows={table.num_rows}, columns={table.num_columns}"
            )
        
        writer.write_table(table)
        total_rows += table.num_rows
        del df
        del table
    
    # Close writer
    if writer is not None:
        writer.close()
    
    logger.info(f"✓ Processed {len(input_files)} files, {total_rows:,} total rows")
    logger.info("")
    
    # =========================================================================
    # VALIDATION (Streaming sample-based)
    # =========================================================================
    logger.info("=" * 80)
    logger.info("VALIDATION")
    logger.info("=" * 80)
    
    if sample_df is None or len(sample_df) == 0:
        logger.warning("No validation sample collected; skipping validation stats.")
        validation_results = {
            'row_count': 0,
            'column_count': 0,
            'has_cluster': False,
            'has_jid': False,
            'clusters_present': [],
            'dtype_check': {},
            'missingness': {}
        }
        validation_results['total_rows'] = total_rows
        validation_results['sample_size'] = 0
    else:
        validation_results = validate_output(sample_df)
        validation_results['total_rows'] = total_rows
        validation_results['sample_size'] = len(sample_df)
        validation_results['dtype_observed'] = {
            k: sorted(list(v)) for k, v in dtype_observed.items()
        }
        validation_results['missingness_global'] = {
            k: (missing_counts.get(k, 0) / total_rows) if total_rows > 0 else None
            for k in dtype_observed.keys()
        }
    
    # Write validation report
    validation_path = output_dir / 'validation' / 'schema_report.json'
    with open(validation_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    logger.info(f"✓ Wrote validation report: {validation_path}")
    logger.info("")
    
    # Record output manifest
    output_manifest.append({
        'path': str(output_file),
        'size_bytes': output_file.stat().st_size,
        'row_count': total_rows,
        'written_at': datetime.now().isoformat()
    })
    logger.info("")
    
    # =========================================================================
    # WRITE MANIFESTS
    # =========================================================================
    logger.info("=" * 80)
    logger.info("WRITING MANIFESTS")
    logger.info("=" * 80)
    
    write_manifest(
        output_dir / 'manifests' / 'input_manifest.jsonl',
        'input',
        input_manifest
    )
    
    write_manifest(
        output_dir / 'manifests' / 'output_manifest.jsonl',
        'output',
        output_manifest
    )
    
    # Write run metadata
    run_metadata = {
        'run_id': run_id,
        'config': config,
        'git_commit': git_commit,
        'started_at': datetime.now().isoformat(),
        'input_file_count': len(input_manifest),
        'output_file_count': len(output_manifest),
        'total_rows': total_rows,
        'clusters': list(sample_df['cluster'].unique()) if 'cluster' in sample_df.columns else []
    }
    
    metadata_path = output_dir / 'manifests' / 'run_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(run_metadata, f, indent=2)
    logger.info(f"✓ Wrote run metadata: {metadata_path}")
    logger.info("")
    
    # =========================================================================
    # COMPLETE
    # =========================================================================
    logger.info("=" * 80)
    logger.info("PRODUCTION BUILD COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Total rows: {total_rows:,}")
    logger.info(f"Clusters: {', '.join(run_metadata['clusters'])}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Completed: {datetime.now().isoformat()}")
    logger.info("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FRESCO v3 Production Data Build"
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Path to production config JSON'
    )
    
    args = parser.parse_args()
    
    try:
        run_production_build(args.config)
    except Exception as e:
        logger.exception("Production build failed")
        sys.exit(1)
