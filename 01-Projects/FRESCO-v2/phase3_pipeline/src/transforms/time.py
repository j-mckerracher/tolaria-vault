"""Time field normalization for FRESCO v2.0."""

import pandas as pd
import logging
from datetime import timezone

logger = logging.getLogger(__name__)


def normalize_timestamps(df: pd.DataFrame, cluster: str) -> pd.DataFrame:
    """
    Normalize timestamps to UTC with microsecond precision.
    
    Timezone by cluster:
    - Stampede: US/Central
    - Conte: US/Eastern
    - Anvil: US/Eastern
    
    Args:
        df: DataFrame with timestamp columns
        cluster: Cluster identifier
    
    Returns:
        DataFrame with normalized timestamps
    """
    TIMEZONE_MAP = {
        'stampede': 'US/Central',
        'conte': 'US/Eastern',
        'anvil': 'US/Eastern'
    }
    
    source_tz = TIMEZONE_MAP.get(cluster, 'UTC')
    timestamp_cols = ['submit_time', 'start_time', 'end_time', 'eligible_time']
    
    for col in timestamp_cols:
        if col not in df.columns:
            continue
        
        # If already datetime, check timezone
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # Localize if naive, convert if aware
            if df[col].dt.tz is None:
                logger.info(f"Localizing {col} to {source_tz} then converting to UTC")
                df[col] = df[col].dt.tz_localize(source_tz).dt.tz_convert('UTC')
            elif str(df[col].dt.tz) != 'UTC':
                logger.info(f"Converting {col} from {df[col].dt.tz} to UTC")
                df[col] = df[col].dt.tz_convert('UTC')
        else:
            # Parse as datetime
            logger.info(f"Parsing {col} as datetime with {source_tz} timezone")
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[col] = df[col].dt.tz_localize(source_tz, ambiguous='infer').dt.tz_convert('UTC')
    
    logger.info(f"Normalized timestamps to UTC for {cluster}")
    return df


def normalize_timelimit(df: pd.DataFrame, cluster: str) -> pd.DataFrame:
    """
    Normalize timelimit to seconds.
    
    THE CRITICAL FIX: Stampede stores timelimit in MINUTES, others in SECONDS.
    
    Args:
        df: DataFrame with timelimit_sec column
        cluster: Cluster identifier
    
    Returns:
        DataFrame with timelimit in seconds
    """
    if 'timelimit_sec' not in df.columns:
        logger.warning("No timelimit_sec column found")
        return df
    
    # Check if conversion needed
    max_timelimit = df['timelimit_sec'].max()
    
    if cluster == 'stampede':
        # Stampede: minutes → seconds
        if max_timelimit < 10000:  # Likely in minutes (typical max ~4320 = 72 hours)
            logger.info(f"Converting Stampede timelimit: minutes → seconds (×60)")
            df['timelimit_sec'] = df['timelimit_sec'] * 60
            df['timelimit_unit_original'] = 'minutes'
        else:
            logger.warning(f"Stampede timelimit suspiciously large ({max_timelimit}), check conversion")
    else:
        # Conte, Anvil: already in seconds
        df['timelimit_unit_original'] = 'seconds'
        logger.info(f"{cluster} timelimit already in seconds")
    
    # Validate
    if df['timelimit_sec'].max() < 60:
        logger.error(f"All timelimits < 60 seconds for {cluster}, likely incorrect units!")
    
    logger.info(f"Timelimit stats for {cluster}:")
    logger.info(f"  Min: {df['timelimit_sec'].min()} sec")
    logger.info(f"  Max: {df['timelimit_sec'].max()} sec")
    logger.info(f"  Median: {df['timelimit_sec'].median()} sec")
    
    return df


def compute_derived_time_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived time fields.
    
    Derived fields:
    - runtime_sec: end - start
    - queue_time_sec: start - submit
    - runtime_fraction: runtime / timelimit
    - timed_out: runtime >= timelimit
    - submit_hour, submit_dow
    
    Args:
        df: DataFrame with timestamp columns
    
    Returns:
        DataFrame with derived columns
    """
    # Runtime
    if 'start_time' in df.columns and 'end_time' in df.columns:
        df['runtime_sec'] = (df['end_time'] - df['start_time']).dt.total_seconds().fillna(0).astype('int64')
    
    # Queue time
    if 'submit_time' in df.columns and 'start_time' in df.columns:
        df['queue_time_sec'] = (df['start_time'] - df['submit_time']).dt.total_seconds().fillna(0).astype('int64')
    
    # Runtime fraction
    if 'runtime_sec' in df.columns and 'timelimit_sec' in df.columns:
        df['runtime_fraction'] = (df['runtime_sec'] / df['timelimit_sec'].replace(0, 1)).clip(0, 10)
        df['timed_out'] = df['runtime_sec'] >= df['timelimit_sec']
        
        timeout_count = df['timed_out'].sum()
        if timeout_count > 0:
            logger.info(f"{timeout_count} jobs timed out ({timeout_count/len(df)*100:.2f}%)")
    
    # Submit time features
    if 'submit_time' in df.columns:
        df['submit_hour'] = df['submit_time'].dt.hour.astype('int8')
        df['submit_dow'] = df['submit_time'].dt.dayofweek.astype('int8')
    
    logger.info(f"Computed derived time fields for {len(df)} jobs")
    return df
