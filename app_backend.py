from pathlib import Path

from src.config import SUPPORTED_DATASETS
from src.download import download_parquet_file
from src.preprocess import (
    run_preprocessing,
    build_daily_zone_summary,
    build_hourly_zone_summary,
    #save_processed_outputs,
)
from src.mapping import (
    load_zones,
    load_daily_summary,
    load_hourly_summary,
    merge_zones_with_summary,
    create_multi_metric_daily_map,
    create_single_html_animated_metric_map,
)

from src.dashboard import (
    load_daily_summary as load_daily_dashboard_summary,
    load_hourly_summary as load_hourly_dashboard_summary,
    load_od_summary,
    load_zone_reference,
    build_dashboard_payload,
)

ZONES_PATH = Path("data/reference/taxi_zones/taxi_zones.shp")


def run_analysis(selection):
    dataset = selection.dataset
    year = selection.year
    month = selection.month
    day = selection.day
    selected_maps = selection.selected_maps

    date_str = f"{year}-{month:02d}-{day:02d}"

    zones_path = Path("data/reference/taxi_zones/taxi_zones.shp")
    output_dir = Path("outputs/maps")
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = download_parquet_file(dataset, year, month)

    processed_paths = run_preprocessing(
        parquet_path=parquet_path,
        dataset=dataset,
        year=year,
        month=month,
        day=day,
    )

    zones = load_zones(zones_path)

    outputs = {}

    if "daily_static" in selected_maps:
        daily_summary = load_daily_summary(processed_paths["daily"])
        merged = merge_zones_with_summary(zones, daily_summary)

        daily_map_path = output_dir / f"daily_multi_metric_map_{dataset}_{date_str}.html"
        create_multi_metric_daily_map(
            zones_gdf=merged,
            output_path=daily_map_path,
            default_metric="pickups",
        )
        outputs["daily_static"] = str(daily_map_path)

    if "animated_hourly" in selected_maps:
        hourly_summary = load_hourly_summary(processed_paths["hourly"])

        animated_map_path = output_dir / f"animated_hourly_multi_metric_{dataset}_{date_str}.html"
        create_single_html_animated_metric_map(
            zones=zones,
            hourly_summary=hourly_summary,
            output_path=animated_map_path,
            day_string=date_str,
            default_metric="pickups",
        )
        outputs["animated_hourly"] = str(animated_map_path)

    return {
        "maps": outputs,
        "processed_paths": processed_paths,
    }

def prepare_python_dashboard_payload(processed_paths: dict):
    daily_summary = load_daily_dashboard_summary(processed_paths["daily"])
    hourly_summary = load_hourly_dashboard_summary(processed_paths["hourly"])
    od_summary = load_od_summary(processed_paths["od"])
    zones_ref = load_zone_reference("data/reference/taxi_zones/taxi_zones.shp")

    payload = build_dashboard_payload(
        daily_summary=daily_summary,
        hourly_summary=hourly_summary,
        od_summary=od_summary,
        zones_ref=zones_ref,
    )
    return payload