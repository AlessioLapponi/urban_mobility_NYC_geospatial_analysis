from download import download_parquet_file, inspect_parquet_columns

dataset = "yellow"
year = 2024
month = 1

parquet_path = download_parquet_file(dataset, year, month)
inspect_parquet_columns(parquet_path)