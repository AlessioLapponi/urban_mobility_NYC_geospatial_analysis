from pathlib import Path

from mapping import (
    load_zones,
    load_hourly_summary,
    create_single_html_animated_metric_map,
)

zones_path = Path("data/reference/taxi_zones/taxi_zones.shp")
hourly_summary_path = Path("data/processed/hourly_zone_summary_yellow_2024-01-15.csv")
output_map_path = Path("outputs/maps/single_html_animated_pickups_revenue_yellow_2024-01-15.html")

zones = load_zones(zones_path)
hourly_summary = load_hourly_summary(hourly_summary_path)

create_single_html_animated_metric_map(
    zones=zones,
    hourly_summary=hourly_summary,
    output_path=output_map_path,
    day_string="2024-01-15",
    default_metric="pickups",
)

print(f"Map saved to: {output_map_path}")