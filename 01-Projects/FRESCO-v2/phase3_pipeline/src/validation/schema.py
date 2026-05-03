"""Schema validation for FRESCO v2.0."""

import pandas as pd
import logging
import numpy as np
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validator for v2.0 schema compliance."""
    
    # Required columns (must be present and non-null for all rows)
    REQUIRED_COLUMNS = [
        'jid', 'jid_global', 'cluster',
        'submit_time', 'start_time', 'end_time',
        'nhosts', 'ncores',
        'node_memory_gb', 'node_cores',
        'exit_code', 'state',
        'memory_includes_cache', 'memory_collection_method'
    ]
    
    # Value ranges for validation
    VALUE_RANGES = {
        'peak_memory_fraction': (0, 2.0),
        'cpu_efficiency': (0, 105.0),
        'runtime_fraction': (0, 10.0),
        'submit_hour': (0, 23),
        'submit_dow': (0, 6),
        'node_memory_gb': (1, 2048),
        'node_cores': (1, 256),
        'nhosts': (1, 10000),
        'ncores': (1, 1000000)
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
        """
        Validate DataFrame against v2.0 schema.
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        logger.info(f"Validating {len(df)} rows")
        
        # Check required columns
        self._check_required_columns(df)
        
        # Check value ranges
        self._check_value_ranges(df)
        
        # Check time consistency
        self._check_time_consistency(df)
        
        # Check data types
        self._check_data_types(df)
        
        # Check cluster identifier
        self._check_cluster(df)
        
        is_valid = len(self.errors) == 0
        
        if is_valid:
            logger.info("✓ Validation PASSED")
        else:
            logger.error(f"✗ Validation FAILED with {len(self.errors)} errors")
        
        if self.warnings:
            logger.warning(f"⚠ {len(self.warnings)} warnings")
        
        return is_valid, self.errors, self.warnings
    
    def _check_required_columns(self, df: pd.DataFrame):
        """Check all required columns are present."""
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            self.errors.append(f"Missing required columns: {missing}")
        
        # Check for nulls in required columns
        for col in self.REQUIRED_COLUMNS:
            if col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    self.errors.append(f"Column '{col}' has {null_count} null values")
    
    def _check_value_ranges(self, df: pd.DataFrame):
        """Check values are within expected ranges."""
        for col, (min_val, max_val) in self.VALUE_RANGES.items():
            if col not in df.columns:
                continue
            
            out_of_range = df[col].notna() & ((df[col] < min_val) | (df[col] > max_val))
            if out_of_range.sum() > 0:
                self.warnings.append(
                    f"Column '{col}' has {out_of_range.sum()} values outside "
                    f"expected range [{min_val}, {max_val}]"
                )
    
    def _check_time_consistency(self, df: pd.DataFrame):
        """Check time fields are consistent."""
        # submit <= start <= end
        if all(col in df.columns for col in ['submit_time', 'start_time', 'end_time']):
            bad_order = (df['submit_time'] > df['start_time']) | (df['start_time'] > df['end_time'])
            if bad_order.sum() > 0:
                self.errors.append(f"{bad_order.sum()} jobs have inconsistent time ordering")
        
        # runtime = end - start
        if all(col in df.columns for col in ['runtime_sec', 'start_time', 'end_time']):
            computed_runtime = (df['end_time'] - df['start_time']).dt.total_seconds()
            mismatch = (df['runtime_sec'] - computed_runtime).abs() > 1
            if mismatch.sum() > 0:
                self.warnings.append(f"{mismatch.sum()} jobs have runtime_sec mismatch")
    
    def _check_data_types(self, df: pd.DataFrame):
        """Check data types are correct."""
        type_checks = {
            'jid': 'object',
            'jid_global': 'object',
            'cluster': 'object',
            'nhosts': 'int32',
            'ncores': 'int32',
            'node_memory_gb': 'float64',
            'node_cores': 'int32'
        }
        
        for col, expected_type in type_checks.items():
            if col in df.columns:
                if df[col].dtype != expected_type:
                    self.warnings.append(f"Column '{col}' has type {df[col].dtype}, expected {expected_type}")
    
    def _check_cluster(self, df: pd.DataFrame):
        """Check cluster identifier is valid."""
        if 'cluster' in df.columns:
            valid_clusters = {'stampede', 'conte', 'anvil'}
            invalid = ~df['cluster'].isin(valid_clusters)
            if invalid.sum() > 0:
                self.errors.append(
                    f"{invalid.sum()} rows have invalid cluster: "
                    f"{df.loc[invalid, 'cluster'].unique()}"
                )
    
    def generate_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate validation report with statistics.
        
        Args:
            df: DataFrame to report on
        
        Returns:
            Dictionary with validation statistics
        """
        report = {
            'total_jobs': len(df),
            'clusters': df['cluster'].value_counts().to_dict() if 'cluster' in df.columns else {},
            'date_range': {
                'start': df['submit_time'].min() if 'submit_time' in df.columns else None,
                'end': df['submit_time'].max() if 'submit_time' in df.columns else None
            },
            'memory_coverage': (df['peak_memory_gb'].notna().sum() / len(df) * 100) if 'peak_memory_gb' in df.columns else 0,
            'null_rates': {col: df[col].isna().sum() / len(df) * 100 for col in df.columns if df[col].isna().sum() > 0},
            'validation_passed': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
        
        return report
