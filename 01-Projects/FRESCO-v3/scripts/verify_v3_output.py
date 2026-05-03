#!/usr/bin/env python3
"""
Verify FRESCO v3 output file quality.
"""

import pandas as pd
import pyarrow.parquet as pq
import sys

output_file = '/depot/sbagchi/data/josh/FRESCO/chunks-v3/PROD-20260203-v3_v3.parquet'

print('=' * 80)
print('PARQUET FILE METADATA')
print('=' * 80)
parquet_file = pq.ParquetFile(output_file)
print(f'Number of row groups: {parquet_file.num_row_groups}')
print(f'Total rows: {parquet_file.metadata.num_rows:,}')
print(f'Schema fields: {len(parquet_file.schema)}')
print()

print('=' * 80)
print('CLUSTER DISTRIBUTION (streaming count)')
print('=' * 80)

# Stream through row groups to count clusters without loading all data
cluster_counts = {}
total_rows = 0

for i in range(parquet_file.num_row_groups):
    row_group = parquet_file.read_row_group(i, columns=['cluster'])
    df_group = row_group.to_pandas()
    counts = df_group['cluster'].value_counts().to_dict()
    for cluster, count in counts.items():
        cluster_counts[cluster] = cluster_counts.get(cluster, 0) + count
    total_rows += len(df_group)
    
    if (i + 1) % 100 == 0:
        print(f'Processed {i+1}/{parquet_file.num_row_groups} row groups...')

print()
print('Cluster distribution:')
for cluster, count in sorted(cluster_counts.items()):
    pct = (count / total_rows) * 100
    print(f'  {cluster}: {count:,} ({pct:.2f}%)')
print(f'Total: {total_rows:,}')
print()

print('=' * 80)
print('SAMPLE ROWS (first row group, first 10 rows)')
print('=' * 80)
df_sample = parquet_file.read_row_group(0).to_pandas().head(10)
cols_to_show = ['cluster', 'jid', 'time', 'ncores', 'timelimit_sec', 'memory_includes_cache']
print(df_sample[cols_to_show].to_string())
print()

print('=' * 80)
print('SCHEMA VERIFICATION')
print('=' * 80)
print('Expected timestamp[us] fields:')
time_fields = ['time', 'submit_time', 'start_time', 'end_time']
for field in time_fields:
    field_type = parquet_file.schema_arrow.field(field).type
    print(f'  {field}: {field_type}')
print()

print('✓ Verification complete')
