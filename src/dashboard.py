from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

import numpy as np

from .config import SUPPORTED_DATASETS

def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    result = numerator / denominator
    result = result.replace([np.inf, -np.inf], np.nan)
    return result

# =========================
# Load helpers
# =========================

def _drop_invalid_metric_rows(df: pd.DataFrame, metric_col: str) -> pd.DataFrame:
    return df[df[metric_col].notna()].copy()

def load_daily_summary(csv_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)

def _clean_zone_table(df: pd.DataFrame) -> pd.DataFrame:
    zone_cols = [col for col in ["zone", "borough", "pickup_zone", "pickup_borough", "dropoff_zone", "dropoff_borough"] if col in df.columns]
    if zone_cols:
        df = df.dropna(subset=zone_cols, how="any").copy()
    return df

def load_hourly_summary(csv_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def load_od_summary(csv_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def load_zone_reference(shapefile_path: str | Path) -> pd.DataFrame:
    """
    Load only the zone metadata needed for dashboard tables.
    If geopandas is available, it reads the shapefile and drops geometry.
    """
    import geopandas as gpd

    zones = gpd.read_file(shapefile_path)
    keep_cols = [col for col in ["LocationID", "zone", "borough"] if col in zones.columns]
    return pd.DataFrame(zones[keep_cols]).copy()


# =========================
# KPI functions
# =========================
def compute_total_pickups(daily_summary: pd.DataFrame) -> int:
    return int(daily_summary["pickups_count"].sum())


def compute_total_dropoffs(daily_summary: pd.DataFrame) -> int:
    return int(daily_summary["dropoffs_count"].sum())


def compute_total_revenue(daily_summary: pd.DataFrame) -> float:
    return float(daily_summary["total_revenue"].sum())


def compute_average_fare(daily_summary: pd.DataFrame) -> float:
    weighted_sum = (daily_summary["avg_fare"] * daily_summary["pickups_count"]).sum()
    total_pickups = daily_summary["pickups_count"].sum()

    if total_pickups == 0:
        return 0.0

    return float(weighted_sum / total_pickups)


def compute_average_trip_distance(daily_summary: pd.DataFrame) -> float:
    weighted_sum = (daily_summary["avg_trip_distance"] * daily_summary["pickups_count"]).sum()
    total_pickups = daily_summary["pickups_count"].sum()

    if total_pickups == 0:
        return 0.0

    return float(weighted_sum / total_pickups)


def compute_busiest_pickup_zone(daily_summary: pd.DataFrame, zones_ref: pd.DataFrame) -> str:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")
    if merged.empty:
        return "N/A"

    top_row = merged.sort_values("pickups_count", ascending=False).iloc[0]
    zone = top_row.get("zone", "Unknown zone")
    borough = top_row.get("borough", "Unknown borough")
    return f"{zone} ({borough})"


def compute_busiest_dropoff_zone(daily_summary: pd.DataFrame, zones_ref: pd.DataFrame) -> str:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")
    if merged.empty:
        return "N/A"

    top_row = merged.sort_values("dropoffs_count", ascending=False).iloc[0]
    zone = top_row.get("zone", "Unknown zone")
    borough = top_row.get("borough", "Unknown borough")
    return f"{zone} ({borough})"


# =========================
# Chart / table builders
# These return clean dataframes, ready for:
# - Python charts
# - Streamlit tables
# - Power BI export later
# =========================
def build_pickups_by_hour(hourly_summary: pd.DataFrame) -> pd.DataFrame:
    result = (
        hourly_summary.groupby("pickup_hour", as_index=False)["pickups_count"]
        .sum()
        .sort_values("pickup_hour")
    )
    return result


def build_revenue_by_hour(hourly_summary: pd.DataFrame) -> pd.DataFrame:
    result = (
        hourly_summary.groupby("pickup_hour", as_index=False)["total_revenue"]
        .sum()
        .sort_values("pickup_hour")
    )
    return result


def build_top_pickup_zones(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")
    merged = _clean_zone_table(merged)

    result = (
        merged[["zone", "borough", "pickups_count"]]
        .sort_values("pickups_count", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return result


def build_top_dropoff_zones(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")
    merged = _clean_zone_table(merged)

    result = (
        merged[["zone", "borough", "dropoffs_count"]]
        .sort_values("dropoffs_count", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return result


def build_top_od_routes(
    od_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    pu_ref = zones_ref.rename(
        columns={
            "LocationID": "PU_LocationID",
            "zone": "pickup_zone",
            "borough": "pickup_borough",
        }
    )
    do_ref = zones_ref.rename(
        columns={
            "LocationID": "DO_LocationID",
            "zone": "dropoff_zone",
            "borough": "dropoff_borough",
        }
    )

    merged = od_summary.merge(pu_ref, on="PU_LocationID", how="left").merge(
        do_ref, on="DO_LocationID", how="left"
    )
    merged = _clean_zone_table(merged)

    result = (
        merged[
            [
                "trips_count",
                "pickup_zone",
                "pickup_borough",
                "dropoff_zone",
                "dropoff_borough",
                "total_revenue",
                "avg_trip_distance",
            ]
        ]
        .sort_values("trips_count", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    return result


def build_borough_summary(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
) -> pd.DataFrame:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")

    result = (
        merged.groupby("borough", as_index=False)
        .agg(
            total_pickups=("pickups_count", "sum"),
            total_dropoffs=("dropoffs_count", "sum"),
            total_revenue=("total_revenue", "sum"),
        )
        .sort_values("total_pickups", ascending=False)
        .reset_index(drop=True)
    )
    return result

def build_borough_bar_chart_data(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
) -> pd.DataFrame:
    return build_borough_summary(daily_summary, zones_ref)

def build_average_fare_by_pickup_zone(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")
    merged = _clean_zone_table(merged)

    result = (
        merged[["zone", "borough", "avg_fare", "pickups_count"]]
        .sort_values("avg_fare", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return result


def build_average_trip_distance_by_pickup_zone(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")
    merged = _clean_zone_table(merged)

    result = (
        merged[["zone", "borough", "avg_trip_distance", "pickups_count"]]
        .sort_values("avg_trip_distance", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return result

def build_borough_bar_chart_data(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
) -> pd.DataFrame:
    return build_borough_summary(daily_summary, zones_ref)

# ==========================
# Derived analysis functions
# ==========================
def build_revenue_per_distance_by_pickup_zone(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")
    merged = _clean_zone_table(merged)

    merged["revenue_per_distance"] = _safe_divide(
        merged["total_revenue"],
        merged["avg_trip_distance"] * merged["pickups_count"]
    )

    merged = _drop_invalid_metric_rows(merged, "revenue_per_distance")

    result = (
        merged[["zone", "borough", "pickups_count", "total_revenue", "avg_trip_distance", "revenue_per_distance"]]
        .sort_values("revenue_per_distance", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return result

def build_average_fare_per_distance_by_hour(
    trip_df: pd.DataFrame,
    dataset: str,
    min_pickups: int = 10,
    min_distance: float = 0.25,
    max_fare_per_distance: float = 100.0,
) -> pd.DataFrame:
    cfg = SUPPORTED_DATASETS[dataset]
    pickup_datetime_col = cfg["pickup_datetime"]
    fare_col = cfg["fare_amount"]
    distance_col = cfg["trip_distance"]

    df = trip_df.copy()
    df[pickup_datetime_col] = pd.to_datetime(df[pickup_datetime_col], errors="coerce")
    df = df.dropna(subset=[pickup_datetime_col]).copy()

    df = df[df[fare_col] > 0].copy()
    df = df[df[distance_col] >= min_distance].copy()

    df["pickup_hour"] = df[pickup_datetime_col].dt.hour
    df["fare_per_distance"] = _safe_divide(df[fare_col], df[distance_col])
    df = _drop_invalid_metric_rows(df, "fare_per_distance")
    df = df[df["fare_per_distance"] <= max_fare_per_distance].copy()

    result = (
        df.groupby("pickup_hour", as_index=False)
        .agg(
            pickups_count=("pickup_hour", "size"),
            fare_per_distance=("fare_per_distance", "mean"),
        )
        .sort_values("pickup_hour")
        .reset_index(drop=True)
    )

    result = result[result["pickups_count"] >= min_pickups].copy()

    return result

def build_borough_share_summary(
    daily_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
) -> pd.DataFrame:
    merged = daily_summary.merge(zones_ref, on="LocationID", how="left")
    merged = _clean_zone_table(merged)

    result = (
        merged.groupby("borough", as_index=False)
        .agg(
            total_pickups=("pickups_count", "sum"),
            total_revenue=("total_revenue", "sum"),
        )
        .reset_index(drop=True)
    )

    total_pickups = result["total_pickups"].sum()
    total_revenue = result["total_revenue"].sum()

    result["pickup_share"] = _safe_divide(result["total_pickups"], pd.Series(total_pickups, index=result.index))
    result["revenue_share"] = _safe_divide(result["total_revenue"], pd.Series(total_revenue, index=result.index))
    result["revenue_share_vs_pickup_share"] = _safe_divide(result["revenue_share"], result["pickup_share"])

    result = _drop_invalid_metric_rows(result, "revenue_share_vs_pickup_share")
    result = result.sort_values("total_pickups", ascending=False).reset_index(drop=True)

    return result

def build_average_fare_per_distance_by_borough(
    trip_df: pd.DataFrame,
    dataset: str,
    zones_ref: pd.DataFrame,
    min_trips: int = 10,
    min_distance: float = 0.25,
    max_fare_per_distance: float = 20.0,
) -> pd.DataFrame:
    cfg = SUPPORTED_DATASETS[dataset]
    pu_col = cfg["pickup_zone"]
    fare_col = cfg["fare_amount"]
    distance_col = cfg["trip_distance"]

    df = trip_df.copy()
    df = df[df[pu_col].notna()].copy()
    df = df[df[fare_col] > 0].copy()
    df = df[df[distance_col] >= min_distance].copy()

    df["fare_per_distance"] = _safe_divide(df[fare_col], df[distance_col])
    df = _drop_invalid_metric_rows(df, "fare_per_distance")
    df = df[df["fare_per_distance"] <= max_fare_per_distance].copy()

    merged = df.merge(
        zones_ref.rename(columns={"LocationID": pu_col}),
        on=pu_col,
        how="left",
    )
    merged = _clean_zone_table(merged)

    borough_result = (
        merged.groupby("borough", as_index=False)
        .agg(
            total_pickups=(pu_col, "size"),
            avg_fare_per_distance=("fare_per_distance", "mean"),
        )
        .sort_values("avg_fare_per_distance", ascending=False)
        .reset_index(drop=True)
    )

    borough_result = borough_result[borough_result["total_pickups"] >= min_trips].copy()

    return borough_result

def build_average_fare_per_distance_by_pickup_zone(
    trip_df: pd.DataFrame,
    dataset: str,
    zones_ref: pd.DataFrame,
    top_n: int = 10,
    min_pickups: int = 10,
    min_distance: float = 0.25,
    max_fare_per_distance: float = 100.0,
) -> pd.DataFrame:
    cfg = SUPPORTED_DATASETS[dataset]
    pu_col = cfg["pickup_zone"]
    fare_col = cfg["fare_amount"]
    distance_col = cfg["trip_distance"]

    df = trip_df.copy()
    df = df[df[pu_col].notna()].copy()
    df = df[df[fare_col] > 0].copy()
    df = df[df[distance_col] >= min_distance].copy()

    df["fare_per_distance"] = _safe_divide(df[fare_col], df[distance_col])
    df = _drop_invalid_metric_rows(df, "fare_per_distance")
    df = df[df["fare_per_distance"] <= max_fare_per_distance].copy()

    grouped = (
        df.groupby(pu_col)
        .agg(
            pickups_count=(pu_col, "size"),
            avg_fare=(fare_col, "mean"),
            avg_trip_distance=(distance_col, "mean"),
            fare_per_distance=("fare_per_distance", "mean"),
        )
        .reset_index()
        .rename(columns={pu_col: "LocationID"})
    )

    grouped = grouped[grouped["pickups_count"] >= min_pickups].copy()

    merged = grouped.merge(zones_ref, on="LocationID", how="left")
    merged = _clean_zone_table(merged)

    result = (
        merged[
            ["zone", "borough", "pickups_count", "avg_fare", "avg_trip_distance", "fare_per_distance"]
        ]
        .sort_values("fare_per_distance", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    return result

# =========================
# Dashboard payload builder
# A single place to compute all daily dashboard elements
# =========================
def build_dashboard_payload(
    trip_df: pd.DataFrame,
    dataset: str,
    daily_summary: pd.DataFrame,
    hourly_summary: pd.DataFrame,
    od_summary: pd.DataFrame,
    zones_ref: pd.DataFrame,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "kpis": {
            "total_pickups": compute_total_pickups(daily_summary),
            "total_dropoffs": compute_total_dropoffs(daily_summary),
            "total_revenue": compute_total_revenue(daily_summary),
            "average_fare": compute_average_fare(daily_summary),
            "average_trip_distance": compute_average_trip_distance(daily_summary),
            "busiest_pickup_zone": compute_busiest_pickup_zone(daily_summary, zones_ref),
            "busiest_dropoff_zone": compute_busiest_dropoff_zone(daily_summary, zones_ref),
        },
        "tables": {
            "pickups_by_hour": build_pickups_by_hour(hourly_summary),
            "revenue_by_hour": build_revenue_by_hour(hourly_summary),
            "top_pickup_zones": build_top_pickup_zones(daily_summary, zones_ref),
            "top_dropoff_zones": build_top_dropoff_zones(daily_summary, zones_ref),
            "top_od_routes": build_top_od_routes(od_summary, zones_ref),
            "borough_summary": build_borough_summary(daily_summary, zones_ref),
            "borough_bar_chart": build_borough_bar_chart_data(daily_summary, zones_ref),
            "average_fare_by_pickup_zone": build_average_fare_by_pickup_zone(daily_summary, zones_ref),
            "average_trip_distance_by_pickup_zone": build_average_trip_distance_by_pickup_zone(daily_summary, zones_ref),
            "average_fare_per_distance_by_pickup_zone": build_average_fare_per_distance_by_pickup_zone(trip_df, dataset, zones_ref),
            "average_fare_per_distance_by_hour": build_average_fare_per_distance_by_hour(trip_df, dataset),
            "borough_share_summary": build_borough_share_summary(daily_summary, zones_ref),
            "average_fare_per_distance_by_borough": build_average_fare_per_distance_by_borough(trip_df, dataset, zones_ref),
        },
    }

    return payload