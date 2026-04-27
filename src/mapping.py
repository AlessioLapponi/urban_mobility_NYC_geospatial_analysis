from pathlib import Path
import geopandas as gpd
import pandas as pd
import folium
import branca.colormap as bcm

from folium.plugins import TimestampedGeoJson
from branca.element import MacroElement
from jinja2 import Template
from .config import SUPPORTED_METRICS, METRIC_HIGHLIGHT_COLORS
from .validate import validate_zone_columns

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

class HourSelectorControl(MacroElement):
    def __init__(self, hour_layers: dict, default_hour_label: str):
        super().__init__()
        self._name = "HourSelectorControl"

        layer_map_entries = []
        radio_entries = []

        for label, layer in hour_layers.items():
            layer_map_entries.append(f'"{label}": {layer.get_name()}')
            checked = "checked" if label == default_hour_label else ""
            radio_entries.append(
                f'''
                <label style="display:block; margin-bottom:3px; cursor:pointer;">
                    <input type="radio" name="hour_selector" value="{label}" {checked}>
                    {label}
                </label>
                '''
            )

        layer_map_js = ",\n".join(layer_map_entries)
        radio_html = "\n".join(radio_entries)

        template_str = f"""
        {{% macro html(this, kwargs) %}}
        <div id="hour-selector-control" style="
            position: fixed;
            top: 30px;
            right: 30px;
            z-index: 9999;
            background-color: white;
            padding: 10px 12px;
            border: 1px solid #999999;
            border-radius: 6px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.25);
            font-size: 13px;
            max-height: 520px;
            overflow-y: auto;
            min-width: 110px;
        ">
            <div style="font-weight: bold; margin-bottom: 8px;">Displayed hour</div>
            {radio_html}
        </div>
        {{% endmacro %}}

        {{% macro script(this, kwargs) %}}
        var hourLayers = {{
            {layer_map_js}
        }};

        function switchHourLayer(selectedLabel) {{
            var map = {{{{this._parent.get_name()}}}};

            for (var label in hourLayers) {{
                var layer = hourLayers[label];
                if (map.hasLayer(layer)) {{
                    map.removeLayer(layer);
                }}
            }}

            if (hourLayers[selectedLabel]) {{
                map.addLayer(hourLayers[selectedLabel]);
            }}
        }}

        var radioButtons = document.querySelectorAll('input[name="hour_selector"]');
        radioButtons.forEach(function(radio) {{
            radio.addEventListener('change', function() {{
                switchHourLayer(this.value);
            }});
        }});
        {{% endmacro %}}
        """

        self._template = Template(template_str)

class AnimatedMetricSelector(MacroElement):
    def __init__(self, metric_layers: dict, default_metric: str):
        super().__init__()
        self._name = "AnimatedMetricSelector"

        buttons = []
        layer_entries = []

        metric_keys = list(metric_layers.keys())

        for metric_key, layer in metric_layers.items():
            label = SUPPORTED_METRICS[metric_key]["label"]
            checked = "checked" if metric_key == default_metric else ""
            buttons.append(
                f'''
                <label style="display:block; margin-bottom:4px; cursor:pointer;">
                    <input type="radio" name="animated_metric_selector" value="{metric_key}" {checked}>
                    {label}
                </label>
                '''
            )
            layer_entries.append(f'"{metric_key}": {layer.get_name()}')

        buttons_html = "\n".join(buttons)
        layer_map_js = ",\n".join(layer_entries)
        metric_keys_js = "[" + ", ".join(f'"{k}"' for k in metric_keys) + "]"

        template_str = f"""
        {{% macro html(this, kwargs) %}}
        <div style="
            position: fixed;
            top: 30px;
            right: 30px;
            z-index: 9999;
            background-color: white;
            padding: 10px 12px;
            border: 1px solid #999999;
            border-radius: 6px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.25);
            font-size: 13px;
            min-width: 220px;
        ">
            <div style="font-weight: bold; margin-bottom: 8px;">Displayed metric</div>
            {buttons_html}
        </div>
        {{% endmacro %}}

        {{% macro script(this, kwargs) %}}
        var animatedMetricLayers = {{
            {layer_map_js}
        }};

        var animatedMetricOrder = {metric_keys_js};

        function getTimeControlContainers() {{
            var nodes = document.querySelectorAll('.leaflet-control-timecontrol');
            var containers = [];
            var seen = new Set();

            nodes.forEach(function(node) {{
                var container = node.closest('.leaflet-bar') || node.parentElement || node;
                if (container && !seen.has(container)) {{
                    seen.add(container);
                    containers.push(container);
                }}
            }});

            return containers;
        }}

        function updateVisibleTimeControl(selectedMetric) {{
            var controls = getTimeControlContainers().reverse();
            var selectedIndex = animatedMetricOrder.indexOf(selectedMetric);

            controls.forEach(function(control, idx) {{
                if (idx === selectedIndex) {{
                    control.style.display = '';
                    control.style.visibility = 'visible';
                }} else {{
                    control.style.display = 'none';
                    control.style.visibility = 'hidden';
                }}
            }});
        }}

        function switchAnimatedMetric(selectedMetric) {{
            var map = {{{{this._parent.get_name()}}}};

            for (var key in animatedMetricLayers) {{
                var layer = animatedMetricLayers[key];
                if (map.hasLayer(layer)) {{
                    map.removeLayer(layer);
                }}
            }}

            if (animatedMetricLayers[selectedMetric]) {{
                map.addLayer(animatedMetricLayers[selectedMetric]);
            }}

            setTimeout(function() {{
                updateVisibleTimeControl(selectedMetric);
            }}, 100);
        }}

        var radioButtons = document.querySelectorAll('input[name="animated_metric_selector"]');
        radioButtons.forEach(function(radio) {{
            radio.addEventListener('change', function() {{
                switchAnimatedMetric(this.value);
            }});
        }});

        setTimeout(function() {{
            updateVisibleTimeControl("{default_metric}");
        }}, 200);
        {{% endmacro %}}
        """

        self._template = Template(template_str)

class AnimatedMetricInitializer(MacroElement):
    def __init__(self, metric_layers: dict, default_metric: str):
        super().__init__()
        self._name = "AnimatedMetricInitializer"

        layer_entries = ",\n".join(
            f'"{metric_key}": {layer.get_name()}'
            for metric_key, layer in metric_layers.items()
        )

        template_str = f"""
        {{% macro script(this, kwargs) %}}
        var animatedMetricLayersInit = {{
            {layer_entries}
        }};

        var map = {{{{this._parent.get_name()}}}};

        for (var key in animatedMetricLayersInit) {{
            if (key !== "{default_metric}") {{
                var layer = animatedMetricLayersInit[key];
                if (map.hasLayer(layer)) {{
                    map.removeLayer(layer);
                }}
            }}
        }}
        {{% endmacro %}}
        """

        self._template = Template(template_str)

def load_hourly_summary(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)

def add_single_overlay_control(base_map, metric_layers: dict):
    base_map.add_child(SingleOverlayControl(metric_layers))

def load_zones(shapefile_path: Path) -> gpd.GeoDataFrame:
    zones = gpd.read_file(shapefile_path)
    validate_zone_columns(zones)
    return zones

def merge_zones_with_hourly_summary(
    zones: gpd.GeoDataFrame,
    hourly_summary: pd.DataFrame,
    hour: int
) -> gpd.GeoDataFrame:
    hour_df = hourly_summary[hourly_summary["pickup_hour"] == hour].copy()

    merged = zones.merge(hour_df, on="LocationID", how="left")

    numeric_columns = [
        "pickups_count",
        "total_revenue",
        "avg_fare",
        "avg_trip_distance",
    ]

    for col in numeric_columns:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    merged["pickup_hour"] = hour
    return merged

def create_hour_layer(
    zones_gdf: gpd.GeoDataFrame,
    metric: str,
    hour: int,
    show: bool = False
) -> folium.FeatureGroup:
    if metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported metrics: {list(SUPPORTED_METRICS.keys())}"
        )

    metric_column = SUPPORTED_METRICS[metric]["column"]
    metric_label = SUPPORTED_METRICS[metric]["label"]
    highlight_color = METRIC_HIGHLIGHT_COLORS.get(metric, "#000000")

    zones_wgs84 = zones_gdf.to_crs(epsg=4326)
    colormap = build_colormap(zones_wgs84[metric_column], metric, metric_label)

    tooltip = folium.GeoJsonTooltip(
        fields=[
            "zone",
            "borough",
            "pickup_hour",
            "pickups_count",
            "total_revenue",
            "avg_fare",
            "avg_trip_distance",
        ],
        aliases=[
            "Zone:",
            "Borough:",
            "Hour:",
            "Pickups:",
            "Total revenue:",
            "Average fare:",
            "Avg trip distance from pickup zone:",
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

    layer = folium.FeatureGroup(name=f"{hour:02d}:00", show=show)

    geojson = folium.GeoJson(
        zones_wgs84,
        style_function=style_function_factory(metric_column, colormap),
        highlight_function=highlight_function_factory(highlight_color),
        tooltip=tooltip,
    )

    geojson.add_to(layer)
    return layer

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

    metric_color_scales = {
        "pickups": [
            "#f7fbff",
            "#e3eef9",
            "#c6dbef",
            "#9ecae1",
            "#6baed6",
            "#4292c6",
            "#2171b5",
            "#08519c",
            "#08306b",
        ],
        "dropoffs": [
            "#fcfbfd",
            "#efedf5",
            "#dadaeb",
            "#bcbddc",
            "#9e9ac8",
            "#807dba",
            "#6a51a3",
            "#54278f",
            "#3f007d",
        ],
        "revenue": [
            "#f7fcf5",
            "#e5f5e0",
            "#c7e9c0",
            "#a1d99b",
            "#74c476",
            "#41ab5d",
            "#238b45",
            "#006d2c",
            "#00441b",
        ],
        "avg_fare": [
            "#fff5eb",
            "#fee6ce",
            "#fdd0a2",
            "#fdae6b",
            "#fd8d3c",
            "#f16913",
            "#d94801",
            "#a63603",
            "#7f2704",
        ],
        "avg_trip_distance": [
            "#fff5f0",
            "#fee0d2",
            "#fcbba1",
            "#fc9272",
            "#fb6a4a",
            "#ef3b2c",
            "#cb181d",
            "#a50f15",
            "#67000d",
        ],
    }

    colors = metric_color_scales.get(metric, metric_color_scales["pickups"])

    # Keep enhanced contrast for pickups below 1000
    if metric == "pickups":
        raw_breaks = [0, 10, 25, 50, 100, 250, 500, 1000, vmax]
        raw_breaks = sorted(set(b for b in raw_breaks if b <= vmax))
        if raw_breaks[-1] != vmax:
            raw_breaks.append(vmax)

        if len(raw_breaks) < 2:
            raw_breaks = [0, vmax]

        colors = colors[:len(raw_breaks)]

        colormap = bcm.LinearColormap(
            colors=colors,
            index=raw_breaks,
            vmin=raw_breaks[0],
            vmax=raw_breaks[-1],
            caption=""
        )

    else:
        values_non_null = values.dropna()

        if len(values_non_null) == 0:
            vmin, vmax = 0.0, 1.0
            colormap = bcm.LinearColormap(
                colors=colors,
                vmin=vmin,
                vmax=vmax,
                caption=""
            )
        else:
            quantiles = values_non_null.quantile([0, 0.2, 0.4, 0.6, 0.8, 1.0]).tolist()
            quantiles = sorted(set(float(q) for q in quantiles))

            if len(quantiles) < 2:
                quantiles = [float(values_non_null.min()), float(values_non_null.max())]
                if quantiles[0] == quantiles[1]:
                    quantiles[1] = quantiles[0] + 1.0

            usable_colors = colors[:len(quantiles)]

            colormap = bcm.LinearColormap(
                colors=usable_colors,
                index=quantiles,
                vmin=quantiles[0],
                vmax=quantiles[-1],
                caption=""
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

def highlight_function_factory(highlight_color: str):
    def highlight_function(feature):
        return {
            "weight": 2.0,
            "color": highlight_color,
            "fillOpacity": 0.9,
        }

    return highlight_function


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
    highlight_color = METRIC_HIGHLIGHT_COLORS.get(metric, "#000000")

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
            "Avg trip distance from pickup zone:",
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
        highlight_function=highlight_function_factory(highlight_color),
        tooltip=tooltip,
        name=metric_label,
    )

    geojson.add_to(layer)
    return layer


class MetricSelectorControl(MacroElement):
    def __init__(self, metric_layers: dict, default_metric_label: str):
        super().__init__()
        self._name = "MetricSelectorControl"

        layer_map_entries = []
        radio_entries = []

        for label, layer in metric_layers.items():
            layer_map_entries.append(f'"{label}": {layer.get_name()}')
            checked = "checked" if label == default_metric_label else ""
            radio_entries.append(
                f'''
                <label style="display:block; margin-bottom:4px; cursor:pointer;">
                    <input type="radio" name="metric_selector" value="{label}" {checked}>
                    {label}
                </label>
                '''
            )

        layer_map_js = ",\n".join(layer_map_entries)
        radio_html = "\n".join(radio_entries)

        template_str = f"""
        {{% macro html(this, kwargs) %}}
        <div id="metric-selector-control" style="
            position: fixed;
            top: 30px;
            right: 30px;
            z-index: 9999;
            background-color: white;
            padding: 10px 12px;
            border: 1px solid #999999;
            border-radius: 6px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.25);
            font-size: 13px;
            min-width: 200px;
        ">
            <div style="font-weight: bold; margin-bottom: 8px;">Displayed metric</div>
            {radio_html}
        </div>
        {{% endmacro %}}

        {{% macro script(this, kwargs) %}}
        var metricLayers = {{
            {layer_map_js}
        }};

        function switchMetricLayer(selectedLabel) {{
            var map = {{{{this._parent.get_name()}}}};

            for (var label in metricLayers) {{
                var layer = metricLayers[label];
                if (map.hasLayer(layer)) {{
                    map.removeLayer(layer);
                }}
            }}

            if (metricLayers[selectedLabel]) {{
                map.addLayer(metricLayers[selectedLabel]);
            }}
        }}

        var radioButtons = document.querySelectorAll('input[name="metric_selector"]');
        radioButtons.forEach(function(radio) {{
            radio.addEventListener('change', function() {{
                switchMetricLayer(this.value);
            }});
        }});
        {{% endmacro %}}
        """

        self._template = Template(template_str)

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
        metric_label = SUPPORTED_METRICS[metric]["label"]
        layer = create_metric_layer(
            zones_gdf=zones_gdf,
            metric=metric,
            show=(metric == default_metric)
        )
        layer.add_to(base_map)
        metric_layers[metric_label] = layer

    default_metric_label = SUPPORTED_METRICS[default_metric]["label"]
    base_map.add_child(MetricSelectorControl(metric_layers, default_metric_label))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_map.save(output_path)

    return base_map

def create_hourly_metric_map(
    zones: gpd.GeoDataFrame,
    hourly_summary: pd.DataFrame,
    metric: str,
    output_path: Path,
    default_hour: int = 12
) -> folium.Map:
    if metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported metrics: {list(SUPPORTED_METRICS.keys())}"
        )

    center = get_map_center(zones)

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

    hour_layers = {}

    for hour in range(24):
        merged = merge_zones_with_hourly_summary(zones, hourly_summary, hour)

        layer = create_hour_layer(
            zones_gdf=merged,
            metric=metric,
            hour=hour,
            show=(hour == default_hour)
        )
        layer.add_to(base_map)
        hour_layers[f"{hour:02d}:00"] = layer

    base_map.add_child(HourSelectorControl(hour_layers, f"{default_hour:02d}:00"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_map.save(output_path)

    return base_map

def get_metric_color(metric: str, value: float, vmin: float, vmax: float) -> str:
    series = pd.Series([vmin, value, vmax])
    colormap = build_colormap(series, metric, "")
    return colormap(value)


def build_global_metric_range(hourly_summary: pd.DataFrame, metric: str) -> tuple[float, float]:
    metric_column = SUPPORTED_METRICS[metric]["column"]
    values = hourly_summary[metric_column].fillna(0)

    vmin = float(values.min())
    vmax = float(values.max())

    if vmin == vmax:
        vmax = vmin + 1.0

    return vmin, vmax


def build_timestamped_hourly_features(
    zones: gpd.GeoDataFrame,
    hourly_summary: pd.DataFrame,
    metric: str,
    day_string: str,
) -> dict:
    metric_column = SUPPORTED_METRICS[metric]["column"]
    highlight_color = METRIC_HIGHLIGHT_COLORS.get(metric, "#000000")

    zones_wgs84 = zones.to_crs(epsg=4326)
    vmin, vmax = build_global_metric_range(hourly_summary, metric)

    features = []

    for hour in range(24):
        merged = merge_zones_with_hourly_summary(zones_wgs84, hourly_summary, hour)

        timestamp = f"{day_string}T{hour:02d}:00:00"

        for _, row in merged.iterrows():
            value = float(row.get(metric_column, 0))
            fill_color = get_metric_color(metric, value, vmin, vmax)

            feature = {
                "type": "Feature",
                "geometry": row["geometry"].__geo_interface__,
                "properties": {
                    "time": timestamp,
                    "style": {
                        "color": "#444444",
                        "weight": 0.6,
                        "fillColor": fill_color,
                        "fillOpacity": 0.75,
                    },
                    "highlight": {
                        "color": highlight_color,
                        "weight": 2.0,
                        "fillOpacity": 0.9,
                    },
                    "popup": (
                        f"<b>Zone:</b> {row.get('zone', '')}<br>"
                        f"<b>Borough:</b> {row.get('borough', '')}<br>"
                        f"<b>Hour:</b> {hour:02d}:00<br>"
                        f"<b>Pickups:</b> {int(row.get('pickups_count', 0))}<br>"
                        f"<b>Total revenue:</b> {row.get('total_revenue', 0):.2f}<br>"
                        f"<b>Average fare:</b> {row.get('avg_fare', 0):.2f}<br>"
                        f"<b>Avg trip distance from pickup zone:</b> {row.get('avg_trip_distance', 0):.2f}"
                    ),
                },
            }

            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def create_animated_hourly_map(
    zones: gpd.GeoDataFrame,
    hourly_summary: pd.DataFrame,
    metric: str,
    output_path: Path,
    day_string: str,
) -> folium.Map:
    center = get_map_center(zones)

    base_map = folium.Map(
        location=center,
        zoom_start=10,
        tiles="CartoDB positron"
    )

    feature_collection = build_timestamped_hourly_features(
        zones=zones,
        hourly_summary=hourly_summary,
        metric=metric,
        day_string=day_string,
    )

    TimestampedGeoJson(
        feature_collection,
        period="PT1H",
        add_last_point=False,
        auto_play=False,
        loop=False,
        max_speed=4,
        loop_button=True,
        time_slider_drag_update=True,
        duration="PT1H",
        date_options="YYYY-MM-DD HH:mm",
    ).add_to(base_map)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_map.save(output_path)

    return base_map

def build_timestamped_geojson_layer(
    zones: gpd.GeoDataFrame,
    hourly_summary: pd.DataFrame,
    metric: str,
    day_string: str,
) -> TimestampedGeoJson:
    feature_collection = build_timestamped_hourly_features(
        zones=zones,
        hourly_summary=hourly_summary,
        metric=metric,
        day_string=day_string,
    )

    layer = TimestampedGeoJson(
        data=feature_collection,
        period="PT1H",
        add_last_point=False,
        auto_play=False,
        loop=False,
        max_speed=4,
        loop_button=True,
        time_slider_drag_update=True,
        duration="PT1H",
        date_options="YYYY-MM-DD HH:mm",
    )

    return layer

def create_single_html_animated_metric_map(
    zones: gpd.GeoDataFrame,
    hourly_summary: pd.DataFrame,
    output_path: Path,
    day_string: str,
    default_metric: str = "pickups",
) -> folium.Map:
    supported_test_metrics = [
    "pickups",
    "revenue",
    "avg_fare",
    "avg_trip_distance",
]

    if default_metric not in supported_test_metrics:
        raise ValueError(
            f"Default metric must be one of {supported_test_metrics}"
        )

    center = get_map_center(zones)

    base_map = folium.Map(
        location=center,
        zoom_start=10,
        tiles="CartoDB positron"
    )

    metric_layers = {}

    for metric in supported_test_metrics:
        layer = build_timestamped_geojson_layer(
            zones=zones,
            hourly_summary=hourly_summary,
            metric=metric,
            day_string=day_string,
        )
        layer.add_to(base_map)
        metric_layers[metric] = layer

    base_map.add_child(AnimatedMetricInitializer(metric_layers, default_metric))
    base_map.add_child(AnimatedMetricSelector(metric_layers, default_metric))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_map.save(output_path)

    return base_map

