from __future__ import annotations

from typing import Any, Dict, Iterable

import pandas as pd
import streamlit as st


# =========================
# Formatting helpers
# =========================
def format_number(value: float | int) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.2f}"


def format_currency(value: float | int) -> str:
    return f"${value:,.2f}"


def get_kpi_label(kpi_key: str) -> str:
    labels = {
        "total_pickups": "Total Pickups",
        "total_dropoffs": "Total Dropoffs",
        "total_revenue": "Total Revenue",
        "average_fare": "Average Fare",
        "average_trip_distance": "Average Trip Distance",
        "busiest_pickup_zone": "Busiest Pickup Zone",
        "busiest_dropoff_zone": "Busiest Dropoff Zone",
    }
    return labels.get(kpi_key, kpi_key.replace("_", " ").title())


def format_kpi_value(kpi_key: str, value: Any) -> str:
    if kpi_key == "total_revenue":
        return format_currency(float(value))
    if kpi_key in {"average_fare"}:
        return format_currency(float(value))
    if kpi_key in {"average_trip_distance"}:
        return f"{float(value):,.2f}"
    if kpi_key in {"total_pickups", "total_dropoffs"}:
        return format_number(int(value))
    return str(value)


# =========================
# KPI rendering
# =========================
def render_kpi_cards(selected_kpis: Iterable[str], payload: Dict[str, Any]) -> None:
    kpi_data = payload["kpis"]
    selected_kpis = list(selected_kpis)

    if not selected_kpis:
        st.info("No KPI cards selected.")
        return

    columns = st.columns(len(selected_kpis))

    for col, kpi_key in zip(columns, selected_kpis):
        value = kpi_data.get(kpi_key, "N/A")
        label = get_kpi_label(kpi_key)
        formatted_value = format_kpi_value(kpi_key, value)

        with col:
            st.metric(label=label, value=formatted_value)


# =========================
# Table / chart renderers
# =========================
def render_pickups_by_hour(df: pd.DataFrame) -> None:
    st.markdown("#### Pickups by Hour")
    st.bar_chart(df.set_index("pickup_hour")["pickups_count"])


def render_revenue_by_hour(df: pd.DataFrame) -> None:
    st.markdown("#### Revenue by Hour")
    st.bar_chart(df.set_index("pickup_hour")["total_revenue"])


def render_table(title: str, df: pd.DataFrame) -> None:
    st.markdown(f"#### {title}")
    st.dataframe(df, use_container_width=True)

def render_borough_bar_chart(df: pd.DataFrame) -> None:
    st.markdown("#### Borough Bar Chart")
    if "borough" in df.columns and "total_pickups" in df.columns:
        st.bar_chart(df.set_index("borough")["total_pickups"])
    else:
        st.warning("Borough bar chart data is not available.")

def render_average_fare_by_pickup_zone(df: pd.DataFrame) -> None:
    st.markdown("#### Average Fare by Pickup Zone")
    st.dataframe(df, use_container_width=True)


def render_average_trip_distance_by_pickup_zone(df: pd.DataFrame) -> None:
    st.markdown("#### Average Trip Distance by Pickup Zone")
    st.dataframe(df, use_container_width=True)


def render_chart_or_table(chart_key: str, payload: Dict[str, Any]) -> None:
    tables = payload["tables"]

    if chart_key == "pickups_by_hour":
        render_pickups_by_hour(tables["pickups_by_hour"])
    elif chart_key == "revenue_by_hour":
        render_revenue_by_hour(tables["revenue_by_hour"])
    elif chart_key == "top_pickup_zones":
        render_table("Top Pickup Zones", tables["top_pickup_zones"])
    elif chart_key == "top_dropoff_zones":
        render_table("Top Dropoff Zones", tables["top_dropoff_zones"])
    elif chart_key == "top_od_routes":
        render_table("Top Zone-to-Zone Routes", tables["top_od_routes"])
    elif chart_key == "borough_summary":
        render_table("Borough Summary", tables["borough_summary"])
    elif chart_key == "borough_bar_chart":
        render_borough_bar_chart(tables["borough_bar_chart"])
    elif chart_key == "average_fare_by_pickup_zone":
        render_average_fare_by_pickup_zone(tables["average_fare_by_pickup_zone"])
    elif chart_key == "average_trip_distance_by_pickup_zone":
        render_average_trip_distance_by_pickup_zone(tables["average_trip_distance_by_pickup_zone"])
    else:
        st.warning(f"Unsupported chart/table key: {chart_key}")


def render_dashboard_blocks(
    selected_kpis: Iterable[str],
    selected_charts: Iterable[str],
    payload: Dict[str, Any],
) -> None:
    selected_kpis = list(selected_kpis)
    selected_charts = list(selected_charts)

    if selected_kpis:
        st.markdown("### KPI Overview")
        render_kpi_cards(selected_kpis, payload)

    if selected_charts:
        st.markdown("### Analytical Views")
        for chart_key in selected_charts:
            render_chart_or_table(chart_key, payload)




# =========================
# UI option mapping helpers
# These convert the UI strings into backend keys
# =========================
KPI_UI_TO_KEY = {
    "Total pickups": "total_pickups",
    "Total dropoffs": "total_dropoffs",
    "Total revenue": "total_revenue",
    "Average fare": "average_fare",
    "Average trip distance": "average_trip_distance",
    "Busiest pickup zone": "busiest_pickup_zone",
    "Busiest dropoff zone": "busiest_dropoff_zone",
}

CHART_UI_TO_KEY = {
    "Pickups by hour": "pickups_by_hour",
    "Revenue by hour": "revenue_by_hour",
    "Top pickup zones": "top_pickup_zones",
    "Top dropoff zones": "top_dropoff_zones",
    "Top zone-to-zone routes": "top_od_routes",
    "Borough summary table": "borough_summary",
    "Borough bar chart": "borough_bar_chart", 
    "Average fare by pickup zone": "average_fare_by_pickup_zone",  
    "Average trip distance by pickup zone": "average_trip_distance_by_pickup_zone",  
}


def map_selected_kpis(ui_selected_kpis: Iterable[str]) -> list[str]:
    return [KPI_UI_TO_KEY[item] for item in ui_selected_kpis if item in KPI_UI_TO_KEY]


def map_selected_charts(ui_selected_charts: Iterable[str]) -> list[str]:
    return [CHART_UI_TO_KEY[item] for item in ui_selected_charts if item in CHART_UI_TO_KEY]