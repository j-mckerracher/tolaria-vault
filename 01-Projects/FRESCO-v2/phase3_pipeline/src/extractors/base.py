"""Base extractor class for FRESCO v2.0 transformation pipeline."""

import pandas as pd
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, List
import json

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for cluster-specific data extractors."""
    
    def __init__(self, source_path: Path, clusters_json_path: Path):
        """
        Initialize extractor.
        
        Args:
            source_path: Path to source data repository
            clusters_json_path: Path to clusters.json metadata
        """
        self.source_path = Path(source_path)
        self.clusters_json_path = Path(clusters_json_path)
        
        # Load cluster metadata
        with open(clusters_json_path) as f:
            clusters_data = json.load(f)
            self.cluster_metadata = clusters_data['clusters'][self.cluster_name]
        
        logger.info(f"Initialized {self.cluster_name} extractor")
        logger.info(f"Source path: {self.source_path}")
    
    @property
    @abstractmethod
    def cluster_name(self) -> str:
        """Return cluster identifier ('stampede', 'conte', or 'anvil')."""
        pass
    
    @abstractmethod
    def extract_month(self, year: int, month: int) -> pd.DataFrame:
        """
        Extract and normalize data for a specific month.
        
        Args:
            year: Year (e.g., 2015)
            month: Month (1-12)
        
        Returns:
            DataFrame in v2.0 intermediate format (pre-validation)
        """
        pass
    
    def add_cluster_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add cluster-level metadata columns from clusters.json.
        
        Args:
            df: DataFrame with job data
        
        Returns:
            DataFrame with metadata columns added
        """
        # Memory collection metadata
        mem_config = self.cluster_metadata['memory_collection']
        df['memory_includes_cache'] = mem_config['includes_cache']
        df['memory_collection_method'] = mem_config['method']
        df['memory_aggregation'] = mem_config['aggregation']
        df['memory_sampling_interval_sec'] = mem_config['sampling_interval_sec']
        df['memory_original_unit'] = mem_config['unit_in_source']
        
        # Cluster identifier
        df['cluster'] = self.cluster_name
        
        logger.info(f"Added cluster metadata for {len(df)} jobs")
        return df
    
    def get_hardware_context(self, row: pd.Series) -> Dict:
        """
        Get hardware specifications for a job based on partition and date.
        
        Args:
            row: Job row with 'partition' and 'submit_time' fields
        
        Returns:
            Dictionary with hardware specifications
        """
        partition = row['partition']
        submit_date = pd.to_datetime(row['submit_time']).date()
        
        # Find applicable hardware generation
        for gen in self.cluster_metadata['hardware_generations']:
            start = pd.to_datetime(gen['start_date']).date()
            end = pd.to_datetime(gen['end_date']).date()
            
            if start <= submit_date <= end:
                if partition in gen['partitions']:
                    partition_spec = gen['partitions'][partition]
                    
                    return {
                        'node_memory_gb': partition_spec['node_memory_gb'],
                        'node_cores': partition_spec['node_cores'],
                        'node_type': partition_spec['node_type'],
                        'node_architecture': 'x86_64',  # All current clusters
                        'node_cpu_model': partition_spec.get('cpu_model'),
                        'gpu_count_per_node': partition_spec.get('gpu_count_per_node', 0),
                        'gpu_memory_gb_per_device': partition_spec.get('gpu_memory_gb_per_device'),
                        'gpu_model': partition_spec.get('gpu_model'),
                        'hardware_generation': gen['generation_id'],
                        'interconnect': partition_spec.get('interconnect')
                    }
                else:
                    logger.warning(f"Unknown partition '{partition}' for {self.cluster_name} on {submit_date}")
                    # Return defaults
                    return self._get_default_hardware()
        
        logger.warning(f"No hardware generation found for {self.cluster_name} on {submit_date}")
        return self._get_default_hardware()
    
    def _get_default_hardware(self) -> Dict:
        """Return default hardware specs when partition lookup fails."""
        # Use first partition from first generation as default
        first_gen = self.cluster_metadata['hardware_generations'][0]
        first_partition = list(first_gen['partitions'].values())[0]
        
        return {
            'node_memory_gb': first_partition['node_memory_gb'],
            'node_cores': first_partition['node_cores'],
            'node_type': first_partition['node_type'],
            'node_architecture': 'x86_64',
            'node_cpu_model': first_partition.get('cpu_model'),
            'gpu_count_per_node': first_partition.get('gpu_count_per_node', 0),
            'gpu_memory_gb_per_device': first_partition.get('gpu_memory_gb_per_device'),
            'gpu_model': first_partition.get('gpu_model'),
            'hardware_generation': first_gen['generation_id'],
            'interconnect': first_partition.get('interconnect')
        }
    
    def validate_source_files(self, year: int, month: int) -> bool:
        """
        Check if source files exist for the given month.
        
        Args:
            year: Year
            month: Month
        
        Returns:
            True if files exist, False otherwise
        """
        # Override in subclasses to check specific files
        return True
