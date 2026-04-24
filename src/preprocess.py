from pathlib import Path
import pandas as pd

from config import SUPPORTED_DATASETS
from validate import validate_dataset_name, validate_trip_columns


def load_required_trip_data(parquet_path: Path, dataset: str) -> pd.DataFrame:
    validate_dataset_name(dataset)

    cfg = SUPPORTED_DATASETS[dataset]
    required_columns = [
        cfg["pickup_datetime"],
        cfg["dropoff_datetime"],
        cfg["pickup_zone"],
        cfg["dropoff_zone"],
        cfg["trip_distance"],
        cfg["fare_amount"],
        cfg["total_amount"],
    ]

    df = pd.read_parquet(parquet_path, columns=required_columns)
    validate_trip_columns(df, dataset)

    return df


def filter_day(df: pd.DataFrame, dataset: str, year: int, month: int, day: int) -> pd.DataFrame:
    cfg = SUPPORTED_DATASETS[dataset]
    pickup_col = cfg["pickup_datetime"]

    df = df.copy()
    df[pickup_col] = pd.to_datetime(df[pickup_col], errors="coerce")
    df = df.dropna(subset=[pickup_col])

    target_date = pd.Timestamp(year=year, month=month, day=day).date()
    return df[df[pickup_col].dt.date == target_date].copy()


def add_time_columns(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    cfg = SUPPORTED_DATASETS[dataset]
    pickup_col = cfg["pickup_datetime"]

    df = df.copy()
    df["pickup_hour"] = df[pickup_col].dt.hour
    df["pickup_date"] = df[pickup_col].dt.date
    return df


def build_daily_zone_summary(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    cfg = SUPPORTED_DATASETS[dataset]
    pu_col = cfg["pickup_zone"]
    do_col = cfg["dropoff_zone"]
    fare_col = cfg["fare_amount"]
    total_col = cfg["total_amount"]
    distance_col = cfg["trip_distance"]

    pickups = (
        df.groupby(pu_col)
        .agg(
            pickups_count=(pu_col, "size"),
            total_revenue=(total_col, "sum"),
            avg_fare=(fare_col, "mean"),
            avg_trip_distance=(distance_col, "mean"),
        )
        .reset_index()
        .rename(columns={pu_col: "LocationID"})
    )

    dropoffs = (
        df.groupby(do_col)
        .size()
        .reset_index(name="dropoffs_count")
        .rename(columns={do_col: "LocationID"})
    )

    summary = pickups.merge(dropoffs, on="LocationID", how="left")
    summary["dropoffs_count"] = summary["dropoffs_count"].fillna(0).astype(int)

    return summary


def build_hourly_zone_summary(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    cfg = SUPPORTED_DATASETS[dataset]
    pu_col = cfg["pickup_zone"]
    fare_col = cfg["fare_amount"]
    total_col = cfg["total_amount"]
    distance_col = cfg["trip_distance"]

    summary = (
        df.groupby([pu_col, "pickup_hour"])
        .agg(
            pickups_count=(pu_col, "size"),
            total_revenue=(total_col, "sum"),
            avg_fare=(fare_col, "mean"),
            avg_trip_distance=(distance_col, "mean"),
        )
        .reset_index()
        .rename(columns={pu_col: "LocationID"})
    )

    return summary


def build_od_summary(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    cfg = SUPPORTED_DATASETS[dataset]
    pu_col = cfg["pickup_zone"]
    do_col = cfg["dropoff_zone"]
    total_col = cfg["total_amount"]
    distance_col = cfg["trip_distance"]

    od = (
        df.groupby([pu_col, do_col])
        .agg(
            trips_count=(pu_col, "size"),
            total_revenue=(total_col, "sum"),
            avg_trip_distance=(distance_col, "mean"),
        )
        .reset_index()
        .rename(columns={pu_col: "PU_LocationID", do_col: "DO_LocationID"})
        .sort_values("trips_count", ascending=False)
    )

    return od


def save_processed_outputs(
    daily_summary: pd.DataFrame,
    hourly_summary: pd.DataFrame,
    od_summary: pd.DataFrame,
    dataset: str,
    year: int,
    month: int,
    day: int,
    processed_dir: str = "data/processed",
) -> dict[str, Path]:
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    suffix = f"{dataset}_{year}-{month:02d}-{day:02d}"

    daily_path = processed_path / f"daily_zone_summary_{suffix}.csv"
    hourly_path = processed_path / f"hourly_zone_summary_{suffix}.csv"
    od_path = processed_path / f"od_summary_{suffix}.csv"

    daily_summary.to_csv(daily_path, index=False)
    hourly_summary.to_csv(hourly_path, index=False)
    od_summary.to_csv(od_path, index=False)

    return {
        "daily": daily_path,
        "hourly": hourly_path,
        "od": od_path,
    }


def run_preprocessing(parquet_path: Path, dataset: str, year: int, month: int, day: int) -> dict[str, Path]:
    df = load_required_trip_data(parquet_path, dataset)
    df = filter_day(df, dataset, year, month, day)
    df = add_time_columns(df, dataset)

    daily_summary = build_daily_zone_summary(df, dataset)
    hourly_summary = build_hourly_zone_summary(df, dataset)
    od_summary = build_od_summary(df, dataset)

    return save_processed_outputs(
        daily_summary=daily_summary,
        hourly_summary=hourly_summary,
        od_summary=od_summary,
        dataset=dataset,
        year=year,
        month=month,
        day=day,
    )