"""Stampede cluster extractor for FRESCO v2.0."""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from multiprocessing import Pool
import os
from .base import BaseExtractor

logger = logging.getLogger(__name__)

_WORKER_JOB_IDS = None
_WORKER_TACC_STATS_PATH = None
_WORKER_MONTH_START = None
_WORKER_MONTH_END = None
_TIMESTAMP_CHUNK_SIZE = 200_000


def _init_worker(tacc_stats_path: Path, job_ids: set, month_start: datetime, month_end: datetime) -> None:
    """Initialize worker globals to avoid large payload per task."""
    global _WORKER_JOB_IDS, _WORKER_TACC_STATS_PATH, _WORKER_MONTH_START, _WORKER_MONTH_END
    _WORKER_JOB_IDS = job_ids
    _WORKER_TACC_STATS_PATH = Path(tacc_stats_path)
    _WORKER_MONTH_START = month_start
    _WORKER_MONTH_END = month_end


def _node_has_month_data(mem_file: Path, month_start: datetime, month_end: datetime) -> bool:
    """Scan timestamps in chunks and early-exit once month data is detected."""
    try:
        for chunk in pd.read_csv(mem_file, usecols=['timestamp'], chunksize=_TIMESTAMP_CHUNK_SIZE):
            timestamps = pd.to_datetime(chunk['timestamp'], errors='coerce')
            if timestamps.isna().all():
                continue
            if ((timestamps >= month_start) & (timestamps < month_end)).any():
                return True
        return False
    except Exception:
        return False


def _read_node_file_filtered(node_dir: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Read and aggregate a single node's mem.csv for target jobs/month."""
    mem_file = _WORKER_TACC_STATS_PATH / node_dir / "mem.csv"
    if not mem_file.exists():
        return None, None

    try:
        if not _node_has_month_data(mem_file, _WORKER_MONTH_START, _WORKER_MONTH_END):
            return None, None

        node_mem = pd.read_csv(mem_file, usecols=['jobID', 'timestamp', 'MemUsed', 'MemTotal'])
        node_mem['timestamp'] = pd.to_datetime(node_mem['timestamp'], errors='coerce')

        node_mem = node_mem[
            (node_mem['timestamp'] >= _WORKER_MONTH_START) &
            (node_mem['timestamp'] < _WORKER_MONTH_END) &
            (node_mem['jobID'].isin(_WORKER_JOB_IDS))
        ]

        if node_mem.empty:
            return None, None

        # Aggregate per-node max memory for each job
        node_agg = node_mem.groupby('jobID').agg({
            'MemUsed': 'max',
            'MemTotal': 'first'
        }).reset_index()

        node_agg.columns = ['jid', 'node_max_mem', 'node_mem_total']
        return node_agg, None
    except Exception as e:
        return None, f"{node_dir}: {e}"


class StampedeExtractor(BaseExtractor):
    """
    Extractor for Stampede cluster data (2013-2018).
    
    Stampede is the most complex cluster because:
    1. Single 1.1GB accounting file (8.7M jobs total)
    2. Node-partitioned TACC_Stats (6,172 NODE* directories)
    3. Timelimit in MINUTES (requires ×60 conversion!)
    4. Memory in KB (requires ÷1024÷1024 to GB)
    5. Multi-node jobs spread across multiple NODE* directories
    
    Optimization: Parallel reads with month filtering to avoid scanning all data.
    """
    
    def __init__(self, source_path: Path, clusters_json_path: Path):
        super().__init__(source_path, clusters_json_path)
        self._accounting_df: Optional[pd.DataFrame] = None
        self._node_index: Optional[Dict[str, List[str]]] = None
    
    @property
    def cluster_name(self) -> str:
        return "stampede"
    
    def _load_accounting(self) -> pd.DataFrame:
        """Load and cache the full accounting file."""
        if self._accounting_df is not None:
            return self._accounting_df
        
        logger.info("Loading Stampede accounting file (8.7M rows, may take a minute)...")
        accounting_file = self.source_path / "Stampede" / "AccountingStatistics" / "stampede_accounting.csv"
        
        if not accounting_file.exists():
            raise FileNotFoundError(f"Stampede accounting file not found: {accounting_file}")
        
        self._accounting_df = pd.read_csv(accounting_file, low_memory=False)
        
        # Parse timestamps once
        self._accounting_df['start_parsed'] = pd.to_datetime(
            self._accounting_df['start'], format='%m/%d/%Y %H:%M:%S', errors='coerce'
        )
        self._accounting_df['end_parsed'] = pd.to_datetime(
            self._accounting_df['end'], format='%m/%d/%Y %H:%M:%S', errors='coerce'
        )
        self._accounting_df['submit_parsed'] = pd.to_datetime(
            self._accounting_df['submit'], format='%m/%d/%Y %H:%M:%S', errors='coerce'
        )
        
        logger.info(f"Loaded {len(self._accounting_df):,} total Stampede jobs")
        return self._accounting_df
    
    def extract_month(self, year: int, month: int) -> pd.DataFrame:
        """
        Extract Stampede data for a specific month.
        
        Stampede format:
        - AccountingStatistics/stampede_accounting.csv (single file, filter by month)
        - TACC_Stats/NODE*/mem.csv (node-partitioned memory metrics)
        
        Args:
            year: Year (2013-2018)
            month: Month (1-12)
        
        Returns:
            DataFrame in v2.0 intermediate format
        """
        logger.info(f"Extracting Stampede {year:04d}-{month:02d}")
        
        # Load full accounting (cached after first call)
        acc_df = self._load_accounting()
        
        # Filter to target month
        target_start = datetime(year, month, 1)
        if month == 12:
            target_end = datetime(year + 1, 1, 1)
        else:
            target_end = datetime(year, month + 1, 1)
        
        month_df = acc_df[
            (acc_df['start_parsed'] >= target_start) &
            (acc_df['start_parsed'] < target_end)
        ].copy()
        
        logger.info(f"Found {len(month_df):,} jobs in {year:04d}-{month:02d}")
        
        if month_df.empty:
            return pd.DataFrame()
        
        # =========================================================================
        # STAGE 1: Parse Job Attributes
        # =========================================================================
        logger.info("Parsing job attributes...")
        
        job_df = pd.DataFrame({
            'jid': month_df['jobID'],
            'job_name': month_df['jobname'],
            'username': month_df['user'],
            'account': month_df['account'],
            'partition': month_df['queue'],
            'exit_code_raw': month_df['exit_status'],
            'nhosts': month_df['nnodes'].fillna(1).astype(int),
            'ncores': month_df['ncpus'].fillna(1).astype(int),
        })
        
        # Timestamps
        job_df['submit_time'] = month_df['submit_parsed'].values
        job_df['start_time'] = month_df['start_parsed'].values
        job_df['end_time'] = month_df['end_parsed'].values
        
        # CRITICAL: Timelimit in MINUTES → convert to seconds
        job_df['timelimit_original'] = month_df['walltime']
        job_df['timelimit_unit_original'] = 'minutes'  # Stampede uses minutes!
        job_df['timelimit_sec'] = month_df['walltime'].fillna(0).astype(int) * 60  # ×60!
        
        # Parse exit status
        job_df['state'] = month_df['exit_status'].apply(self._map_exit_status)
        job_df['exit_code'] = job_df['exit_code_raw'].apply(self._parse_exit_code)
        job_df['failed'] = job_df['state'].isin(['FAILED', 'TIMEOUT', 'NODE_FAIL', 'CANCELLED'])
        
        # =========================================================================
        # STAGE 2: Load Memory Metrics from Node Directories
        # =========================================================================
        logger.info("Loading memory metrics from node directories...")
        
        # Get job IDs in this month
        job_ids = set(month_df['jobID'].unique())
        
        # Load memory data from all nodes (optimized: parallel + month-filtered)
        mem_agg = self._aggregate_node_memory(job_ids, year, month)
        
        if not mem_agg.empty:
            job_df = job_df.merge(mem_agg, on='jid', how='left')
            
            # Memory metadata for Stampede
            job_df['memory_original_unit'] = 'kilobytes'  # KB in source
            job_df['memory_includes_cache'] = True  # Stampede includes cache
            job_df['memory_collection_method'] = 'tacc_stats_node'
            job_df['memory_aggregation'] = 'max_per_node_sum_across_nodes'
            job_df['memory_sampling_interval_sec'] = 600  # 10 min intervals
            
            coverage = (~job_df['memory_original_value'].isna()).sum() / len(job_df) * 100
            logger.info(f"Memory coverage: {coverage:.1f}%")
        else:
            logger.warning("No memory data loaded")
            job_df['memory_original_value'] = None
            job_df['memory_original_unit'] = 'kilobytes'
            job_df['memory_includes_cache'] = True
            job_df['memory_collection_method'] = 'tacc_stats_node'
            job_df['memory_aggregation'] = 'max_per_node_sum_across_nodes'
            job_df['memory_sampling_interval_sec'] = 600
        
        # =========================================================================
        # STAGE 3: Load CPU Metrics (Optional - same node directories)
        # =========================================================================
        # CPU data is also in node directories but less critical than memory
        # For pilot, skip CPU and add later if needed
        job_df['value_cpuuser'] = None
        
        # =========================================================================
        # STAGE 4: Join Hardware Context
        # =========================================================================
        logger.info("Joining hardware context...")
        
        # Stampede has simpler hardware (mostly Sandy Bridge)
        # Vectorized approach for speed
        hw_defaults = {
            'node_memory_gb': 32.0,  # Standard Stampede node
            'node_cores': 16,
            'node_type': 'sandy_bridge',
            'node_architecture': 'Sandy Bridge (E5-2680)',
            'node_cpu_model': 'Intel Xeon E5-2680',
            'hardware_generation': 'stampede_1',
            'interconnect': 'Mellanox FDR InfiniBand',
            'gpu_count_per_node': 0,
            'gpu_memory_gb_per_device': None,
            'gpu_model': None,
        }
        
        for col, val in hw_defaults.items():
            job_df[col] = val
        
        # Override for largemem queue
        largemem_mask = job_df['partition'].str.contains('large', case=False, na=False)
        if largemem_mask.any():
            job_df.loc[largemem_mask, 'node_memory_gb'] = 256.0
            job_df.loc[largemem_mask, 'node_cores'] = 32
            job_df.loc[largemem_mask, 'node_type'] = 'westmere_largemem'
        
        # =========================================================================
        # STAGE 5: Add Cluster Identifier and Global ID
        # =========================================================================
        job_df['cluster'] = 'stampede'
        job_df['jid_global'] = 'stampede_' + job_df['jid'].astype(str)
        
        # Placeholder columns
        job_df['system_issue'] = False
        job_df['hosts'] = ''
        
        logger.info(f"Extracted {len(job_df):,} jobs for Stampede {year:04d}-{month:02d}")
        
        return job_df
    
    def _aggregate_node_memory(self, job_ids: set, year: int, month: int) -> pd.DataFrame:
        """
        Load and aggregate memory data from all node directories.
        
        This is the most expensive operation for Stampede.
        Strategy: Parallel reads + month filtering + per-node aggregation.
        
        Args:
            job_ids: Set of job IDs to extract
            year: Target year
            month: Target month
        
        Returns:
            DataFrame with columns: jid, memory_original_value, node_memory_from_metrics
        """
        tacc_stats_path = self.source_path / "Stampede" / "TACC_Stats"
        
        if not tacc_stats_path.exists():
            logger.warning(f"TACC_Stats directory not found: {tacc_stats_path}")
            return pd.DataFrame()
        
        # Get list of NODE* directories
        node_dirs = sorted([d for d in os.listdir(tacc_stats_path) if d.startswith('NODE')])
        logger.info(f"Found {len(node_dirs)} node directories")

        # Month boundaries
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)

        worker_count = int(os.environ.get('SLURM_CPUS_PER_TASK', 8))
        worker_count = max(1, worker_count)
        logger.info(f"Reading node files in parallel ({worker_count} workers)")

        job_ids = set(job_ids)
        with Pool(
            processes=worker_count,
            initializer=_init_worker,
            initargs=(tacc_stats_path, job_ids, month_start, month_end)
        ) as pool:
            results = pool.map(_read_node_file_filtered, node_dirs)

        all_mem_data = []
        errors = []
        for data, error in results:
            if error:
                errors.append(error)
            if data is not None and not data.empty:
                all_mem_data.append(data)

        if errors:
            for err in errors[:5]:
                logger.warning(f"Node read error: {err}")
            if len(errors) > 5:
                logger.warning(f"{len(errors) - 5} additional node read errors suppressed")

        if not all_mem_data:
            return pd.DataFrame()

        combined = pd.concat(all_mem_data, ignore_index=True)
        logger.info(f"Combined {len(combined):,} per-node aggregates from {len(all_mem_data)} nodes")

        # Aggregate: SUM(per-node max) per job, max node memory for reference
        mem_agg = combined.groupby('jid').agg({
            'node_max_mem': 'sum',
            'node_mem_total': 'max'
        }).reset_index()

        mem_agg.columns = ['jid', 'memory_original_value', 'node_memory_from_metrics']

        return mem_agg
    
    def _map_exit_status(self, exit_status) -> str:
        """Map Stampede exit status to standardized state."""
        if pd.isna(exit_status):
            return 'UNKNOWN'
        
        exit_str = str(exit_status).upper()
        
        if exit_str == 'COMPLETED' or exit_str == '0':
            return 'COMPLETED'
        elif 'TIMEOUT' in exit_str:
            return 'TIMEOUT'
        elif 'NODE' in exit_str or 'HARDWARE' in exit_str:
            return 'NODE_FAIL'
        elif 'CANCEL' in exit_str:
            return 'CANCELLED'
        else:
            return 'FAILED'
    
    def _parse_exit_code(self, exit_status) -> int:
        """Parse exit code from status string."""
        if pd.isna(exit_status):
            return -1
        
        exit_str = str(exit_status).upper()
        
        if exit_str == 'COMPLETED':
            return 0
        elif exit_str == 'TIMEOUT':
            return 124  # Standard timeout exit code
        elif 'CANCEL' in exit_str:
            return 130  # SIGINT
        else:
            # Try to parse as integer
            try:
                return int(exit_status)
            except ValueError:
                return 1  # Generic failure
