from pathlib import Path
from urllib.request import urlretrieve
import pandas as pd

from config import SUPPORTED_DATASETS


def build_tlc_url(dataset: str, year: int, month: int) -> str:
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset: {dataset}")

    prefix = SUPPORTED_DATASETS[dataset]["file_prefix"]
    return f"https://d37ci6vzurychx.cloudfront.net/trip-data/{prefix}_{year}-{month:02d}.parquet"


def build_local_parquet_path(dataset: str, year: int, month: int, raw_dir: str = "data/raw") -> Path:
    raw_path = Path(raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    return raw_path / f"{dataset}_tripdata_{year}-{month:02d}.parquet"


def download_parquet_file(dataset: str, year: int, month: int, raw_dir: str = "data/raw") -> Path:
    url = build_tlc_url(dataset, year, month)
    output_path = build_local_parquet_path(dataset, year, month, raw_dir=raw_dir)

    if output_path.exists():
        print(f"File already exists: {output_path}")
        return output_path

    print(f"Downloading from: {url}")
    urlretrieve(url, output_path)
    print(f"Saved to: {output_path}")

    return output_path


def inspect_parquet_columns(parquet_path: Path, n_rows: int = 5):
    try:
        df = pd.read_parquet(parquet_path)
    except ImportError as e:
        raise ImportError(
            "Parquet support is missing. Install 'pyarrow' or 'fastparquet' in the current environment."
        ) from e

    print("Columns:")
    print(df.columns.tolist())
    print("\nPreview:")
    print(df.head(n_rows))
    print(df.shape)