from pathlib import Path

from mapping import (
    load_zones,
    load_daily_summary,
    merge_zones_with_summary,
    create_multi_metric_daily_map,
)

zones_path = Path("data/reference/taxi_zones/taxi_zones.shp")
daily_summary_path = Path("data/processed/daily_zone_summary_yellow_2024-01-15.csv")
output_map_path = Path("outputs/maps/daily_multi_metric_map_yellow_2024-01-15.html")

zones = load_zones(zones_path)
summary = load_daily_summary(daily_summary_path)
merged = merge_zones_with_summary(zones, summary)

create_multi_metric_daily_map(
    zones_gdf=merged,
    output_path=output_map_path,
    default_metric="pickups",
)

print(f"Map saved to: {output_map_path}")