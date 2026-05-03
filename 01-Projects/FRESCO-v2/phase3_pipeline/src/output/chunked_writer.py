"""
Chunked writer module for FRESCO v2.0.

Writes output in hourly chunks:
    /depot/sbagchi/data/josh/FRESCO/chunks-v2.0/YYYY/MM/DD/HH.parquet

Unlike v1.0, NO cluster suffixes are used because:
- v2.0 has explicit 'cluster' column in data
- v2.0 has 'jid_global' with cluster prefix (no ID collisions)
- All clusters combined in same hourly files (truly unified dataset)
"""

import logging
from pathlib import Path
from typing import Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


class ChunkedWriter:
    """Writes FRESCO v2.0 data in hourly chunks (unified across clusters)."""
    
    def __init__(self, base_output_dir: str):
        """
        Initialize chunked writer.
        
        Args:
            base_output_dir: Base directory for output (e.g., /depot/.../chunks-v2.0)
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized ChunkedWriter with base_output_dir: {self.base_output_dir}")
    
    def write_chunks(self, df: pd.DataFrame, append: bool = True) -> Dict[str, int]:
        """
        Write DataFrame in hourly chunks based on submit_time.
        
        All clusters go into the same hourly files (no suffixes).
        The 'cluster' column in the data distinguishes them.
        
        Args:
            df: DataFrame with submit_time and cluster columns
            append: If True, append to existing files; if False, overwrite
        
        Returns:
            Dictionary with chunk statistics
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to write_chunks")
            return {"total_chunks": 0, "total_jobs": 0}
        
        # Validate cluster column exists
        if "cluster" not in df.columns:
            raise ValueError("DataFrame must have 'cluster' column")
        
        # Ensure submit_time is datetime
        if not pd.api.types.is_datetime64_any_dtype(df["submit_time"]):
            df["submit_time"] = pd.to_datetime(df["submit_time"], utc=True)
        
        # Extract year, month, day, hour from submit_time
        df = df.copy()  # Avoid SettingWithCopyWarning
        df["_year"] = df["submit_time"].dt.year
        df["_month"] = df["submit_time"].dt.month
        df["_day"] = df["submit_time"].dt.day
        df["_hour"] = df["submit_time"].dt.hour
        
        # Group by submit_time hour
        grouped = df.groupby(["_year", "_month", "_day", "_hour"])
        
        stats = {
            "total_chunks": 0,
            "total_jobs": 0,
            "chunks_written": []
        }
        
        for (year, month, day, hour), group_df in grouped:
            # Drop temporary columns
            output_df = group_df.drop(columns=["_year", "_month", "_day", "_hour"])
            
            # Build output path: YYYY/MM/DD/HH.parquet (no suffix)
            year_dir = self.base_output_dir / f"{year:04d}"
            month_dir = year_dir / f"{month:02d}"
            day_dir = month_dir / f"{day:02d}"
            day_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{hour:02d}.parquet"
            output_path = day_dir / filename
            
            # If append mode and file exists, merge with existing data
            if append and output_path.exists():
                existing_df = pd.read_parquet(output_path)
                output_df = pd.concat([existing_df, output_df], ignore_index=True)
                logger.debug(f"Appending to existing chunk: {output_path}")
            
            # Write chunk
            output_df.to_parquet(
                output_path,
                engine="pyarrow",
                compression="snappy",
                index=False
            )
            
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            
            stats["total_chunks"] += 1
            stats["total_jobs"] += len(output_df)
            stats["chunks_written"].append({
                "path": str(output_path),
                "jobs": len(output_df),
                "size_mb": file_size_mb
            })
            
            # Log cluster breakdown if multiple clusters in chunk
            cluster_counts = output_df["cluster"].value_counts().to_dict() if "cluster" in output_df.columns else {}
            cluster_str = ", ".join([f"{k}={v}" for k, v in cluster_counts.items()]) if cluster_counts else ""
            
            logger.info(
                f"✓ Wrote chunk: {year:04d}/{month:02d}/{day:02d}/{filename} "
                f"({len(output_df):,} jobs, {file_size_mb:.2f} MB) [{cluster_str}]"
            )
        
        logger.info(
            f"Chunked write complete: {stats['total_chunks']} chunks, "
            f"{stats['total_jobs']:,} jobs"
        )
        
        return stats
