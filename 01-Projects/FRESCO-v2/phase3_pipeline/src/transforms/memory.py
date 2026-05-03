"""Memory metric normalization for FRESCO v2.0."""

import pandas as pd
import logging
import numpy as np

logger = logging.getLogger(__name__)


def normalize_memory_units(df: pd.DataFrame, cluster: str) -> pd.DataFrame:
    """
    Normalize memory values to GB based on source units.
    
    Memory units by cluster (from clusters.json):
    - Stampede: bytes
    - Conte: kilobytes
    - Anvil: gigabytes (already normalized!)
    
    Args:
        df: DataFrame with memory columns
        cluster: Cluster identifier
    
    Returns:
        DataFrame with normalized memory columns
    """
    if 'peak_memory_gb' not in df.columns or df['peak_memory_gb'].isna().all():
        logger.warning(f"No memory data found for {cluster}")
        return df
    
    # Anvil already in GB, no conversion needed
    if cluster == 'anvil':
        logger.info(f"Anvil memory already in GB, no conversion needed")
        return df
    
    # Apply unit conversion
    unit_multipliers = {
        'bytes': 1 / (1024**3),
        'kilobytes': 1 / (1024**2),
        'KB': 1 / (1024**2)
    }
    
    source_unit = df['memory_original_unit'].iloc[0] if 'memory_original_unit' in df.columns else None
    
    if cluster == 'stampede':
        # Stampede: bytes → GB
        multiplier = unit_multipliers['bytes']
        logger.info(f"Converting Stampede memory: bytes → GB (×{multiplier:.2e})")
    elif cluster == 'conte':
        # Conte: KB → GB
        multiplier = unit_multipliers['kilobytes']
        logger.info(f"Converting Conte memory: KB → GB (×{multiplier:.2e})")
    else:
        logger.warning(f"Unknown cluster {cluster}, no conversion applied")
        return df
    
    # Convert if not already done
    if df['peak_memory_gb'].max() > 1000:  # Suspiciously large, likely unconverted
        df['peak_memory_gb'] = df['peak_memory_gb'] * multiplier
        if 'mean_memory_gb' in df.columns:
            df['mean_memory_gb'] = df['mean_memory_gb'] * multiplier
        logger.info(f"Converted memory units for {len(df)} jobs")
    
    return df


def compute_memory_fractions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute normalized memory fractions.
    
    Key metric: peak_memory_fraction = peak_memory_gb / (node_memory_gb * nhosts)
    
    Args:
        df: DataFrame with memory and hardware context
    
    Returns:
        DataFrame with fraction columns added
    """
    if 'peak_memory_gb' not in df.columns or 'node_memory_gb' not in df.columns:
        logger.warning("Missing columns for memory fraction computation")
        return df
    
    # Total node memory available to job
    total_node_memory = df['node_memory_gb'] * df['nhosts']
    
    # Peak memory fraction
    df['peak_memory_fraction'] = (df['peak_memory_gb'] / total_node_memory.replace(0, np.nan)).clip(0, 2)
    
    # Memory efficiency (peak vs requested)
    if 'memory_requested_gb' in df.columns:
        df['memory_efficiency'] = (df['peak_memory_gb'] / df['memory_requested_gb'].replace(0, np.nan)).clip(0, 2)
    else:
        df['memory_efficiency'] = None
    
    # Log warnings for suspicious values
    high_fraction = df['peak_memory_fraction'] > 1.5
    if high_fraction.sum() > 0:
        logger.warning(f"{high_fraction.sum()} jobs with peak_memory_fraction > 1.5 (possible overcommit)")
    
    low_usage = df['peak_memory_fraction'] < 0.01
    if low_usage.sum() > 0:
        logger.info(f"{low_usage.sum()} jobs with peak_memory_fraction < 0.01 (low memory usage)")
    
    logger.info(f"Computed memory fractions for {len(df)} jobs")
    logger.info(f"  Mean peak_memory_fraction: {df['peak_memory_fraction'].mean():.3f}")
    logger.info(f"  Median peak_memory_fraction: {df['peak_memory_fraction'].median():.3f}")
    
    return df


def detect_oom_killed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect out-of-memory kills from exit codes and memory usage.
    
    OOM indicators:
    - Exit code in {137, 247, 9} (SIGKILL)
    - State contains 'OUT_OF_MEMORY'
    - High peak_memory_fraction (>0.95) with non-zero exit
    
    Args:
        df: DataFrame with exit codes and memory
    
    Returns:
        DataFrame with oom_killed column
    """
    OOM_EXIT_CODES = {137, 247, 9}
    
    # Initialize oom_killed column
    df['oom_killed'] = False
    
    # Check exit codes
    if 'exit_code' in df.columns:
        df.loc[df['exit_code'].isin(OOM_EXIT_CODES), 'oom_killed'] = True
    
    # Check state string
    if 'state' in df.columns:
        df.loc[df['state'].str.contains('OUT_OF_MEMORY', case=False, na=False), 'oom_killed'] = True
    
    # Heuristic: high memory usage + failure
    if 'peak_memory_fraction' in df.columns and 'failed' in df.columns:
        suspected_oom = (df['peak_memory_fraction'] > 0.95) & (df['failed'] == True)
        df.loc[suspected_oom, 'oom_killed'] = True
    
    oom_count = df['oom_killed'].sum()
    if oom_count > 0:
        logger.info(f"Detected {oom_count} OOM-killed jobs ({oom_count/len(df)*100:.2f}%)")
    
    return df
