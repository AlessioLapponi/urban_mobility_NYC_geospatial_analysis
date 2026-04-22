from pathlib import Path

from preprocess import run_preprocessing

parquet_path = Path("data/raw/yellow_tripdata_2024-01.parquet")

outputs = run_preprocessing(
    parquet_path=parquet_path,
    dataset="yellow",
    year=2024,
    month=1,
    day=15,
)

print(outputs)