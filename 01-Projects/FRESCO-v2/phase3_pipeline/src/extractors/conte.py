"""Conte cluster extractor for FRESCO v2.0."""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from .base import BaseExtractor

logger = logging.getLogger(__name__)


class ConteExtractor(BaseExtractor):
    """Extractor for Conte cluster data (2015-2017)."""
    
    @property
    def cluster_name(self) -> str:
        return "conte"
    
    def extract_month(self, year: int, month: int) -> pd.DataFrame:
        """
        Extract Conte data for a specific month.
        
        Conte format:
        - AccountingStatistics/YYYY-MM.csv (PBS/Torque accounting)
        - TACC_Stats/YYYY-MM/mem.csv (memory time-series)
        - TACC_Stats/YYYY-MM/cpu.csv (CPU metrics)
        - Join on "jobID"
        
        Args:
            year: Year (2015-2017)
            month: Month (1-12)
        
        Returns:
            DataFrame in v2.0 intermediate format
        """
        logger.info(f"Extracting Conte {year:04d}-{month:02d}")
        
        # File paths (under Conte/ subdirectory)
        conte_path = self.source_path / "Conte"
        accounting_file = conte_path / "AccountingStatistics" / f"{year:04d}-{month:02d}.csv"
        mem_file = conte_path / "TACC_Stats" / f"{year:04d}-{month:02d}" / "mem.csv"
        cpu_file = conte_path / "TACC_Stats" / f"{year:04d}-{month:02d}" / "cpu.csv"
        
        logger.info(f"Accounting: {accounting_file}")
        logger.info(f"Memory: {mem_file}")
        
        # Check files exist
        if not accounting_file.exists():
            logger.warning(f"Accounting file not found: {accounting_file}")
            return pd.DataFrame()
        
        # =========================================================================
        # STAGE 1: Read Accounting Data
        # =========================================================================
        logger.info("Reading accounting data...")
        acc_df = pd.read_csv(accounting_file)
        
        # Filter to job completion events only (jobevent='E' for End)
        acc_df = acc_df[acc_df['jobevent'] == 'E'].copy()
        logger.info(f"Found {len(acc_df):,} completed jobs")
        
        if acc_df.empty:
            logger.warning(f"No completed jobs in {year:04d}-{month:02d}")
            return pd.DataFrame()
        
        # =========================================================================
        # STAGE 2: Parse Job Attributes
        # =========================================================================
        logger.info("Parsing job attributes...")
        
        # Rename columns
        job_df = pd.DataFrame({
            'jid': acc_df['jobID'],
            'job_name': acc_df['jobname'],
            'username': acc_df['user'],
            'account': acc_df['account'],
            'partition': acc_df['queue'],
            'exit_code': acc_df['Exit_status'],
        })
        
        # Parse timestamps (MM/DD/YYYY HH:MM:SS)
        submit_time = pd.to_datetime(acc_df['qtime'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
        submit_time = submit_time.fillna(
            pd.to_datetime(acc_df['ctime'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
        )
        submit_time = submit_time.fillna(
            pd.to_datetime(acc_df['timestamp'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
        )
        job_df['submit_time'] = submit_time
        job_df['start_time'] = pd.to_datetime(acc_df['start'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
        job_df['end_time'] = pd.to_datetime(acc_df['end'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
        
        # Parse walltime (format: "HH:MM:SS" or "DD-HH:MM:SS")
        job_df['timelimit_original'] = acc_df['Resource_List.walltime']
        job_df['timelimit_sec'] = acc_df['Resource_List.walltime'].apply(self._parse_walltime_to_seconds)
        job_df['timelimit_unit_original'] = 'seconds'  # Already in seconds
        
        # Parse node/core counts
        job_df['nhosts'] = acc_df['Resource_List.nodect'].fillna(1).astype(int)
        job_df['ncores'] = acc_df['Resource_List.ncpus'].fillna(1).astype(int)
        
        # Parse exit status
        job_df['state'] = self._map_exit_status(acc_df['Exit_status'])
        job_df['failed'] = job_df['state'].isin(['FAILED', 'TIMEOUT', 'NODE_FAIL', 'CANCELLED'])
        
        # Parse hosts from exec_host (format: "node1/0+node1/1+node2/0...")
        job_df['hosts'] = acc_df['exec_host'].apply(self._parse_exec_host)
        
        # =========================================================================
        # STAGE 3: Join Memory Metrics (if available)
        # =========================================================================
        if mem_file.exists():
            logger.info("Reading memory metrics...")
            mem_df = pd.read_csv(mem_file)
            
            # Aggregate memory per job: MAX/MEAN(MemUsed) across all timestamps and nodes
            mem_agg = mem_df.groupby('jobID').agg({
                'MemUsed': ['max', 'mean'],  # Bytes (verified from inspection)
                'MemTotal': 'first'  # Node memory capacity (bytes)
            }).reset_index()
            
            # Rename for merge
            mem_agg.columns = ['jid', 'memory_original_value', 'memory_mean_value', 'node_memory_from_metrics']
            
            # Join with job data
            job_df = job_df.merge(mem_agg, on='jid', how='left')
            
            # Memory metadata
            job_df['memory_original_unit'] = 'bytes'  # Verified from inspection
            job_df['memory_includes_cache'] = False  # Conte uses RSS only
            job_df['memory_collection_method'] = 'tacc_stats_monthly'
            job_df['memory_aggregation'] = 'max_per_node'
            job_df['memory_sampling_interval_sec'] = 300
            
            # Normalize to GB for downstream transforms
            job_df['peak_memory_gb'] = job_df['memory_original_value'] / (1024**3)
            job_df['mean_memory_gb'] = job_df['memory_mean_value'] / (1024**3)
            
            logger.info(f"Memory coverage: {(~job_df['memory_original_value'].isna()).sum() / len(job_df) * 100:.1f}%")
        else:
            logger.warning(f"Memory file not found: {mem_file}")
            job_df['memory_original_value'] = None
            job_df['memory_original_unit'] = None
            job_df['memory_includes_cache'] = False
            job_df['memory_collection_method'] = None
            job_df['memory_aggregation'] = None
            job_df['memory_sampling_interval_sec'] = None
            job_df['peak_memory_gb'] = None
            job_df['mean_memory_gb'] = None
        
        # =========================================================================
        # STAGE 4: Join CPU Metrics (if available)
        # =========================================================================
        if cpu_file.exists():
            logger.info("Reading CPU metrics...")
            cpu_df = pd.read_csv(cpu_file)
            
            # Aggregate CPU per job
            # CPU columns vary, try common ones
            cpu_cols = [col for col in cpu_df.columns if 'user' in col.lower()]
            if cpu_cols:
                cpu_df['cpu_usage'] = cpu_df[cpu_cols].sum(axis=1)
                cpu_agg = cpu_df.groupby('jobID')['cpu_usage'].mean().reset_index()
                cpu_agg.columns = ['jid', 'value_cpuuser']
                job_df = job_df.merge(cpu_agg, on='jid', how='left')
            else:
                logger.warning("No CPU user columns found in cpu.csv")
                job_df['value_cpuuser'] = None
        else:
            logger.warning(f"CPU file not found: {cpu_file}")
            job_df['value_cpuuser'] = None
        
        # =========================================================================
        # STAGE 5: Join Hardware Context
        # =========================================================================
        logger.info("Joining hardware context...")
        
        # Get hardware specs for each job based on partition and date
        for idx, row in job_df.iterrows():
            hw_context = self.get_hardware_context(row)
            
            if hw_context:
                job_df.at[idx, 'node_memory_gb'] = hw_context['node_memory_gb']
                job_df.at[idx, 'node_cores'] = hw_context['node_cores']
                job_df.at[idx, 'node_type'] = hw_context['node_type']
                job_df.at[idx, 'node_architecture'] = hw_context.get('cpu_model', '')
                job_df.at[idx, 'node_cpu_model'] = hw_context.get('cpu_model', '')
                job_df.at[idx, 'hardware_generation'] = hw_context.get('generation_id', '')
                job_df.at[idx, 'interconnect'] = hw_context.get('interconnect', '')
                job_df.at[idx, 'gpu_count_per_node'] = hw_context.get('gpu_count_per_node', 0)
                job_df.at[idx, 'gpu_memory_gb_per_device'] = hw_context.get('gpu_memory_gb_per_device', None)
                job_df.at[idx, 'gpu_model'] = hw_context.get('gpu_model', None)
        
        # =========================================================================
        # STAGE 6: Add Cluster Identifier and Global ID
        # =========================================================================
        job_df['cluster'] = 'conte'
        job_df['jid_global'] = 'conte_' + job_df['jid'].astype(str)
        
        # =========================================================================
        # STAGE 7: Parse Outages (Optional Enhancement)
        # =========================================================================
        # TODO: Parse Conte_outages.txt and flag system_issue
        job_df['system_issue'] = False  # Placeholder
        
        logger.info(f"Extracted {len(job_df):,} jobs for Conte {year:04d}-{month:02d}")
        
        return job_df
    
    def _parse_walltime_to_seconds(self, walltime_str) -> int:
        """
        Parse PBS walltime format to seconds.
        
        Formats:
        - "HH:MM:SS" → seconds
        - "DD-HH:MM:SS" → seconds
        - "MM:SS" → seconds
        - "1800.0" → numeric seconds (float string)
        - 1800 → numeric seconds (int/float)
        
        Args:
            walltime_str: Walltime string or numeric value
        
        Returns:
            Seconds as integer
        """
        if pd.isna(walltime_str):
            return 0
        
        try:
            # Handle numeric values (int, float, or numeric string like "1800.0")
            if isinstance(walltime_str, (int, float)):
                return int(walltime_str)
            
            walltime_str = str(walltime_str).strip()
            
            # Check if it's a pure numeric string (possibly with decimal)
            try:
                return int(float(walltime_str))
            except ValueError:
                pass  # Not a pure number, continue with time format parsing
            
            # Check for DD-HH:MM:SS format
            if '-' in walltime_str:
                days_part, time_part = walltime_str.split('-')
                days = int(days_part)
                h, m, s = map(int, time_part.split(':'))
                return days * 86400 + h * 3600 + m * 60 + s
            
            # Check for HH:MM:SS or MM:SS format
            parts = list(map(int, walltime_str.split(':')))
            if len(parts) == 3:
                h, m, s = parts
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = parts
                return m * 60 + s
            else:
                return 0
        except Exception as e:
            logger.warning(f"Could not parse walltime: {walltime_str} - {e}")
            return 0
    
    def _map_exit_status_single(self, exit_status) -> str:
        """Map a single PBS exit status to SLURM-style state."""
        if pd.isna(exit_status):
            return 'UNKNOWN'
        
        # Handle numeric exit codes (common for PBS/Torque)
        try:
            code = int(float(exit_status))
            if code == 0:
                return 'COMPLETED'
            return 'FAILED'
        except (TypeError, ValueError):
            pass
        
        exit_str = str(exit_status).upper()
        
        if exit_str in ['0', 'COMPLETED']:
            return 'COMPLETED'
        if 'TIMEOUT' in exit_str or 'TIMELIMIT' in exit_str:
            return 'TIMEOUT'
        if 'NODE' in exit_str or 'HARDWARE' in exit_str:
            return 'NODE_FAIL'
        if 'CANCEL' in exit_str:
            return 'CANCELLED'
        return 'FAILED'
    
    def _map_exit_status(self, exit_status_series: pd.Series) -> pd.Series:
        """
        Map PBS exit status Series to SLURM-style state (vectorized).
        
        Args:
            exit_status_series: Series of PBS exit status codes/strings
        
        Returns:
            Series of state strings
        """
        return exit_status_series.apply(self._map_exit_status_single)
    
    def _parse_exec_host(self, exec_host_str) -> str:
        """
        Parse PBS exec_host string to extract node list.
        
        Format: "node1/0+node1/1+node2/0+node2/1"
        Extracts: "{node1,node2}"
        
        Args:
            exec_host_str: PBS exec_host string
        
        Returns:
            Comma-separated node list
        """
        if pd.isna(exec_host_str):
            return ''
        
        try:
            # Split by '+' and extract node names
            parts = exec_host_str.split('+')
            nodes = set()
            for part in parts:
                if '/' in part:
                    node = part.split('/')[0]
                    nodes.add(node)
                else:
                    nodes.add(part)
            
            return ','.join(sorted(nodes))
        except Exception as e:
            logger.warning(f"Could not parse exec_host: {exec_host_str} - {e}")
            return ''
