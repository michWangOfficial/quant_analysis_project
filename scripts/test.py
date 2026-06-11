from pathlib import Path
import pandas as pd

base_path = Path('.') / 'clean_data' / 'daily' / '20260528'
for parquet_file in sorted(base_path.glob('*.parquet')):
    df = pd.read_parquet(parquet_file)
    print(f'File: {parquet_file.name}')
    print(df.columns.tolist())

