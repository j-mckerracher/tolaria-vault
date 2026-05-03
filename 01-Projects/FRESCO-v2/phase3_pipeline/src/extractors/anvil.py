"""Anvil cluster extractor for FRESCO v2.0."""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from .base import BaseExtractor

logger = logging.getLogger(__name__)


class AnvilExtractor(BaseExtractor):
    """Extractor for Anvil cluster data (2022-2023)."""
    
    @property
    def cluster_name(self) -> str:
        return "anvil"
    
    def extract_month(self, year: int, month: int) -> pd.DataFrame:
        """
        Extract Anvil data for a specific month.
        
        Anvil format:
        - JobAccounting/job_accounting_MMMYYYY_anon.csv (job-level)
        - JobResourceUsage/job_ts_metrics_MMMYYYY_anon.csv (time-series)
        - Join on "Job Id"
        
        Args:
            year: Year (2022-2023)
            month: Month (1-12)
        
        Returns:
            DataFrame in v2.0 intermediate format
        """
        month_name = pd.to_datetime(f"{year}-{month:02d}-01").strftime('%b').lower()
        
        # File paths (under Anvil/ subdirectory)
        anvil_path = self.source_path / "Anvil"
        accounting_file = anvil_path / "JobAccounting" / f"job_accounting_{month_name}{year}_anon.csv"
        metrics_file = anvil_path / "JobResourceUsage" / f"job_ts_metrics_{month_name}{year}_anon.csv"
        
        logger.info(f"Extracting Anvil {year}-{month:02d}")
        logger.info(f"Accounting: {accounting_file}")
        logger.info(f"Metrics: {metrics_file}")
        
        # Read accounting data
        if not accounting_file.exists():
            logger.warning(f"Accounting file not found: {accounting_file}")
            return pd.DataFrame()
        
        accounting_df = pd.read_csv(accounting_file)
        logger.info(f"Read {len(accounting_df)} jobs from accounting")
        
        # Read metrics data
        if not metrics_file.exists():
            logger.warning(f"Metrics file not found: {metrics_file}")
            metrics_df = pd.DataFrame()
        else:
            metrics_df = pd.read_csv(metrics_file)
            logger.info(f"Read {len(metrics_df)} metric samples")
        
        # Transform accounting data to v2.0 schema
        df = self._transform_accounting(accounting_df)
        
        # Aggregate time-series metrics to job-level
        if not metrics_df.empty:
            job_metrics = self._aggregate_metrics(metrics_df)
            df = df.merge(job_metrics, left_on='jid', right_index=True, how='left')
        
        # Add cluster metadata
        df = self.add_cluster_metadata(df)
        
        # Add hardware context
        hardware_context = df.apply(self.get_hardware_context, axis=1, result_type='expand')
        df = pd.concat([df, hardware_context], axis=1)
        
        logger.info(f"Extracted {len(df)} jobs for Anvil {year}-{month:02d}")
        return df
    
    def _transform_accounting(self, accounting_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform Anvil accounting data to v2.0 intermediate schema.
        
        Anvil accounting columns:
        - Account, Job Id, Shared, Cores, Gpus, Nodes, Cpu Time, Node Time,
          Requested Nodes, Requested Wall Time, Queue, Wait Time, Wall Time,
          Eligible Time, End Time, Start Time, Submit Time, User, Exit Status,
          Hosts, Job Name
        """
        df = pd.DataFrame()
        
        # Job identity
        df['jid'] = accounting_df['Job Id']
        df['jid_global'] = 'anvil_' + accounting_df['Job Id'].astype(str)
        df['job_name'] = accounting_df['Job Name']
        df['array_job_id'] = None  # Extract from Job Id if format indicates array
        df['array_task_id'] = None
        
        # Time fields (already UTC in Anvil data)
        df['submit_time'] = pd.to_datetime(accounting_df['Submit Time'])
        df['start_time'] = pd.to_datetime(accounting_df['Start Time'])
        df['end_time'] = pd.to_datetime(accounting_df['End Time'])
        df['eligible_time'] = pd.to_datetime(accounting_df['Eligible Time'])
        
        # Timelimit (Anvil: already in seconds)
        df['timelimit_sec'] = pd.to_numeric(accounting_df['Requested Wall Time'], errors='coerce').fillna(0).astype('int64')
        df['timelimit_original'] = accounting_df['Requested Wall Time'].astype(str)
        df['timelimit_unit_original'] = 'seconds'
        
        # Derived time fields
        df['runtime_sec'] = (df['end_time'] - df['start_time']).dt.total_seconds().fillna(0).astype('int64')
        df['queue_time_sec'] = (df['start_time'] - df['submit_time']).dt.total_seconds().fillna(0).astype('int64')
        df['submit_hour'] = df['submit_time'].dt.hour.astype('int8')
        df['submit_dow'] = df['submit_time'].dt.dayofweek.astype('int8')
        df['runtime_fraction'] = (df['runtime_sec'] / df['timelimit_sec'].replace(0, 1)).clip(0, 10)
        df['timed_out'] = df['runtime_sec'] >= df['timelimit_sec']
        
        # Resource allocation
        df['nhosts'] = accounting_df['Nodes'].astype('int32')
        df['ncores'] = accounting_df['Cores'].astype('int32')
        df['gpus_allocated'] = accounting_df['Gpus'].astype('int32')
        df['memory_requested_gb'] = None  # Not in Anvil accounting
        df['account'] = accounting_df['Account']
        df['partition'] = accounting_df['Queue']
        df['qos'] = None
        df['reservation'] = None
        
        # CPU metrics (from accounting)
        df['cpu_time_sec'] = pd.to_numeric(accounting_df['Cpu Time'], errors='coerce')
        df['cpu_efficiency'] = (df['cpu_time_sec'] / (df['runtime_sec'] * df['ncores']).replace(0, 1) * 100).clip(0, 105)
        
        # Job status
        df['exit_code'] = 0  # Parse from Exit Status
        df['state'] = accounting_df['Exit Status']
        df['failed'] = accounting_df['Exit Status'] != 'COMPLETED'
        df['node_fail'] = False  # Parse from state if available
        
        # User/accounting
        df['username_hash'] = accounting_df['User']
        
        # Hosts
        df['hosts'] = accounting_df['Hosts']
        
        return df
    
    def _aggregate_metrics(self, metrics_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate Anvil time-series metrics to job-level.
        
        Metrics columns:
        - Job Id, Host, Event, Value, Units, Timestamp
        
        Events include: cpuuser, memused, gpuutil, io_read, io_write, etc.
        """
        # Pivot so each event type becomes a column
        aggregated = []
        
        for job_id, group in metrics_df.groupby('Job Id'):
            job_metrics = {'Job Id': job_id}
            
            for event_type in group['Event'].unique():
                event_data = group[group['Event'] == event_type]
                values = pd.to_numeric(event_data['Value'], errors='coerce')
                
                if event_type == 'cpuuser':
                    job_metrics['value_cpuuser'] = values.mean()
                elif event_type == 'memused':
                    # Anvil memory already in GB
                    job_metrics['peak_memory_gb'] = values.max()
                    job_metrics['mean_memory_gb'] = values.mean()
                    job_metrics['memory_original_value'] = values.max()
                elif event_type == 'gpuutil':
                    job_metrics['gpu_utilization_mean'] = values.mean()
                    job_metrics['value_gpu'] = values.mean()
                elif event_type == 'gpumem':
                    job_metrics['gpu_memory_used_gb'] = values.max()
                elif event_type == 'io_read':
                    job_metrics['io_read_gb'] = values.sum() / 1024  # MB to GB
                elif event_type == 'io_write':
                    job_metrics['io_write_gb'] = values.sum() / 1024
            
            aggregated.append(job_metrics)
        
        result = pd.DataFrame(aggregated).set_index('Job Id')
        logger.info(f"Aggregated metrics for {len(result)} jobs")
        return result
