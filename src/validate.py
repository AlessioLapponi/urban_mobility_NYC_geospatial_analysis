from .config import SUPPORTED_DATASETS, REQUIRED_ZONE_COLUMNS


def get_required_trip_columns(dataset: str) -> list[str]:
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset: {dataset}")

    cfg = SUPPORTED_DATASETS[dataset]
    return [
        cfg["pickup_datetime"],
        cfg["dropoff_datetime"],
        cfg["pickup_zone"],
        cfg["dropoff_zone"],
        cfg["trip_distance"],
        cfg["fare_amount"],
        cfg["total_amount"],
    ]


def validate_trip_columns(df, dataset: str) -> None:
    required_columns = get_required_trip_columns(dataset)
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(
            f"Missing required columns for dataset '{dataset}': {missing_columns}"
        )


def validate_zone_columns(zones_df) -> None:
    missing_columns = [col for col in REQUIRED_ZONE_COLUMNS if col not in zones_df.columns]

    if missing_columns:
        raise ValueError(
            f"Missing required zone columns: {missing_columns}"
        )


def validate_dataset_name(dataset: str) -> None:
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(
            f"Unsupported dataset '{dataset}'. Supported datasets: {list(SUPPORTED_DATASETS.keys())}"
        )