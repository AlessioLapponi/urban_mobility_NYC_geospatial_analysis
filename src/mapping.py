from pathlib import Path
import geopandas as gpd
import pandas as pd
import folium
import branca.colormap as bcm

from branca.element import MacroElement
from jinja2 import Template
from config import SUPPORTED_METRICS
from validate import validate_zone_columns

class SingleOverlayControl(MacroElement):
    def __init__(self, metric_layers: dict):
        super().__init__()
        self._name = "SingleOverlayControl"
        self.metric_layers = metric_layers

        layer_js_map = ",\n".join(
            f'"{label}": {layer.get_name()}'
            for label, layer in metric_layers.items()
        )

        self._template = Template(f"""
        {{% macro script(this, kwargs) %}}
        var metricLayers = {{
            {layer_js_map}
        }};

        {{this._parent.get_name()}}.on('overlayadd', function(e) {{
            for (var key in metricLayers) {{
                var layer = metricLayers[key];
                if (layer !== e.layer && {{this._parent.get_name()}}.hasLayer(layer)) {{
                    {{this._parent.get_name()}}.removeLayer(layer);
                }}
            }}
        }});
        {{% endmacro %}}
        """)


def add_single_overlay_control(base_map, metric_layers: dict):
    base_map.add_child(SingleOverlayControl(metric_layers))

def load_zones(shapefile_path: Path) -> gpd.GeoDataFrame:
    zones = gpd.read_file(shapefile_path)
    validate_zone_columns(zones)
    return zones


def load_daily_summary(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def merge_zones_with_summary(
    zones: gpd.GeoDataFrame,
    summary: pd.DataFrame
) -> gpd.GeoDataFrame:
    merged = zones.merge(summary, on="LocationID", how="left")

    numeric_columns = [
        "pickups_count",
        "dropoffs_count",
        "total_revenue",
        "avg_fare",
        "avg_trip_distance",
    ]

    for col in numeric_columns:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    return merged


def get_map_center(zones_gdf: gpd.GeoDataFrame) -> list[float]:
    zones_wgs84 = zones_gdf.to_crs(epsg=4326)
    centroid = zones_wgs84.geometry.union_all().centroid
    return [centroid.y, centroid.x]


def format_metric_series(values: pd.Series) -> tuple[float, float]:
    values = values.fillna(0)

    vmin = float(values.min())
    vmax = float(values.max())

    if vmin == vmax:
        vmax = vmin + 1.0

    return vmin, vmax

def build_colormap(values: pd.Series, metric: str, metric_label: str):
    values = values.fillna(0)
    vmax = float(values.max())

    if vmax == 0:
        vmax = 1.0

    # Special treatment for pickups:
    # denser gradient below 1000, while keeping a continuous legend in raw units
    if metric == "pickups":
        raw_breaks = [0, 10, 25, 50, 100, 250, 500, 1000, vmax]

        # keep only valid increasing breakpoints
        raw_breaks = sorted(set(b for b in raw_breaks if b <= vmax))
        if raw_breaks[-1] != vmax:
            raw_breaks.append(vmax)

        if len(raw_breaks) < 2:
            raw_breaks = [0, vmax]

        # choose as many colors as needed
        base_colors = [
            "#f7fbff",
            "#e3eef9",
            "#c6dbef",
            "#9ecae1",
            "#6baed6",
            "#4292c6",
            "#2171b5",
            "#08519c",
            "#08306b",
        ]
        colors = base_colors[:len(raw_breaks)]

        colormap = bcm.LinearColormap(
            colors=colors,
            index=raw_breaks,
            vmin=raw_breaks[0],
            vmax=raw_breaks[-1],
            caption=f"{metric_label} (enhanced contrast below 1000)",
        )

    else:
        # standard continuous scale for other metrics
        vmin = float(values.min())
        if vmin == vmax:
            vmax = vmin + 1.0

        colormap = bcm.LinearColormap(
            colors=["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
            vmin=vmin,
            vmax=vmax,
            caption=metric_label,
        )

    return colormap

from branca.element import Element

def add_custom_gradient_legend(base_map, metric: str, vmax: float, legend_title: str):
    if metric == "pickups":
        gradient_colors = [
            "#f7fbff",
            "#e3eef9",
            "#c6dbef",
            "#9ecae1",
            "#6baed6",
            "#4292c6",
            "#2171b5",
            "#08519c",
            "#08306b",
        ]

        tick_values = [0, 100, 1000, int(round(vmax))]
        tick_values = sorted(set(tick_values))

    else:
        gradient_colors = [
            "#f7fbff",
            "#c6dbef",
            "#6baed6",
            "#2171b5",
            "#08306b",
        ]

        tick_values = [0, int(round(vmax / 2)), int(round(vmax))]
        tick_values = sorted(set(tick_values))

    gradient_css = ", ".join(gradient_colors)

    labels_html = "".join(
        f'<span style="text-align:center;">{value:,}</span>'
        for value in tick_values
    )

    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 9999;
        background-color: white;
        padding: 10px 12px;
        border: 1px solid #999999;
        border-radius: 6px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.25);
        font-size: 12px;
    ">
        <div style="
            font-weight: bold;
            margin-bottom: 6px;
        ">{legend_title}</div>
        <div style="
            width: 240px;
            height: 14px;
            background: linear-gradient(to right, {gradient_css});
            border: 1px solid #999999;
            margin-bottom: 4px;
        "></div>
        <div style="
            width: 240px;
            display: flex;
            justify-content: space-between;
        ">
            {labels_html}
        </div>
    </div>
    """

    base_map.get_root().html.add_child(Element(legend_html))

def style_function_factory(metric_column: str, colormap):
    def style_function(feature):
        value = feature["properties"].get(metric_column, 0)

        if value is None:
            value = 0

        return {
            "fillColor": colormap(value),
            "color": "#444444",
            "weight": 0.6,
            "fillOpacity": 0.75,
        }

    return style_function


def highlight_function(feature):
    return {
        "weight": 2.0,
        "color": "black",
        "fillOpacity": 0.9,
    }


def create_daily_zone_map(
    zones_gdf: gpd.GeoDataFrame,
    metric: str,
    output_path: Path
) -> folium.Map:
    if metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported metrics: {list(SUPPORTED_METRICS.keys())}"
        )

    metric_column = SUPPORTED_METRICS[metric]["column"]
    metric_label = SUPPORTED_METRICS[metric]["label"]

    zones_wgs84 = zones_gdf.to_crs(epsg=4326)
    center = get_map_center(zones_gdf)

    base_map = folium.Map(
        location=center,
        zoom_start=10,
        tiles="CartoDB positron"
    )

    colormap = build_colormap(zones_wgs84[metric_column], metric, metric_label)

    tooltip = folium.GeoJsonTooltip(
        fields=[
            "zone",
            "borough",
            "pickups_count",
            "dropoffs_count",
            "total_revenue",
            "avg_fare",
            "avg_trip_distance",
        ],
        aliases=[
            "Zone:",
            "Borough:",
            "Pickups:",
            "Dropoffs:",
            "Total revenue:",
            "Average fare:",
            "Avg trip distance from pick up zone:",
        ],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: white;
            border: 1px solid #999999;
            border-radius: 4px;
            box-shadow: 3px;
        """,
    )

    geojson = folium.GeoJson(
        zones_wgs84,
        style_function=style_function_factory(metric_column, colormap),
        highlight_function=highlight_function,
        tooltip=tooltip,
        name=metric_label,
    )

    geojson.add_to(base_map)
    add_custom_gradient_legend(
    base_map=base_map,
    metric=metric,
    vmax=float(zones_wgs84[metric_column].max()),
    legend_title=metric_label
    )
    folium.LayerControl().add_to(base_map)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_map.save(output_path)

    return base_map

def create_metric_layer(
    zones_gdf: gpd.GeoDataFrame,
    metric: str,
    show: bool = False
) -> folium.FeatureGroup:
    if metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported metrics: {list(SUPPORTED_METRICS.keys())}"
        )

    metric_column = SUPPORTED_METRICS[metric]["column"]
    metric_label = SUPPORTED_METRICS[metric]["label"]

    zones_wgs84 = zones_gdf.to_crs(epsg=4326)
    colormap = build_colormap(zones_wgs84[metric_column], metric, metric_label)

    tooltip = folium.GeoJsonTooltip(
        fields=[
            "zone",
            "borough",
            "pickups_count",
            "dropoffs_count",
            "total_revenue",
            "avg_fare",
            "avg_trip_distance",
        ],
        aliases=[
            "Zone:",
            "Borough:",
            "Pickups:",
            "Dropoffs:",
            "Total revenue:",
            "Average fare:",
            "Average trip distance:",
        ],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: white;
            border: 1px solid #999999;
            border-radius: 4px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        """,
    )

    layer = folium.FeatureGroup(name=metric_label, show=show)

    geojson = folium.GeoJson(
        zones_wgs84,
        style_function=style_function_factory(metric_column, colormap),
        highlight_function=highlight_function,
        tooltip=tooltip,
        name=metric_label,
    )

    geojson.add_to(layer)
    return layer


def create_multi_metric_daily_map(
    zones_gdf: gpd.GeoDataFrame,
    output_path: Path,
    default_metric: str = "pickups"
) -> folium.Map:
    if default_metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported default metric '{default_metric}'. Supported metrics: {list(SUPPORTED_METRICS.keys())}"
        )

    center = get_map_center(zones_gdf)

    base_map = folium.Map(
        location=center,
        zoom_start=10,
        tiles=None
    )

    folium.TileLayer(
        tiles="CartoDB positron",
        name="CartoDB Positron",
        control=False
    ).add_to(base_map)

    metric_layers = {}

    for metric in SUPPORTED_METRICS:
        layer = create_metric_layer(
            zones_gdf=zones_gdf,
            metric=metric,
            show=(metric == default_metric)
        )
        layer.add_to(base_map)
        metric_layers[SUPPORTED_METRICS[metric]["label"]] = layer

    #add_single_overlay_control(base_map, metric_layers)

    folium.LayerControl(collapsed=False).add_to(base_map)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_map.save(output_path)

    return base_map