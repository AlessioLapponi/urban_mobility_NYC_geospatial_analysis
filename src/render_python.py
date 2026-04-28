from __future__ import annotations

from typing import Any, Dict, Iterable

import pandas as pd
import streamlit as st

import matplotlib.pyplot as plt

# =========================
# Formatting helpers
# =========================
def format_number(value: float | int) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.2f}"

def prettify_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "pickups_count": "Pickups Count",
        "dropoffs_count": "Dropoffs Count",
        "total_pickups": "Total Pickups",
        "total_dropoffs": "Total Dropoffs",
        "total_revenue": "Total Revenue ($)",
        "avg_fare": "Average Fare ($)",
        "avg_trip_distance": "Average Trip Distance (mi)",
        "pickup_hour": "Hour",
        "zone": "Zone",
        "borough": "Borough",
        "pickup_zone": "Pickup Zone",
        "pickup_borough": "Pickup Borough",
        "dropoff_zone": "Dropoff Zone",
        "dropoff_borough": "Dropoff Borough",
        "trips_count": "Trips Count",
        "revenue_per_distance": "Revenue per Distance ($/mi)",
        "fare_per_distance": "Average Fare per Distance ($/mi)",
        "pickup_share": "Pickup Share (%)",
        "revenue_share": "Revenue Share (%)",
        "revenue_share_vs_pickup_share": "Revenue Share vs Pickup Share",
        "avg_fare_per_distance": "Average Fare per Distance ($/mi)",
    }

    pretty_df = df.rename(columns=rename_map).copy()

    # Convert shares to percentages for display
    for col in ["Pickup Share (%)", "Revenue Share (%)"]:
        if col in pretty_df.columns:
            pretty_df[col] = pretty_df[col] * 100

    return pretty_df

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

    numeric_kpis = []
    text_kpis = []

    for kpi_key in selected_kpis:
        value = kpi_data.get(kpi_key, "N/A")
        if isinstance(value, (int, float)):
            numeric_kpis.append((kpi_key, value))
        else:
            text_kpis.append((kpi_key, value))

    if numeric_kpis:
        columns = st.columns(len(numeric_kpis))
        for col, (kpi_key, value) in zip(columns, numeric_kpis):
            label = get_kpi_label(kpi_key)
            formatted_value = format_kpi_value(kpi_key, value)
            with col:
                st.metric(label=label, value=formatted_value)

    if text_kpis:
        st.markdown("#### Text KPIs")
        for kpi_key, value in text_kpis:
            label = get_kpi_label(kpi_key)
            st.markdown(f"**{label}:** {value}")


# =========================
# Table / chart renderers
# =========================
def render_pickups_by_hour(df: pd.DataFrame) -> None:
    st.markdown("#### Pickups by Hour")
    pretty_df = prettify_columns(df.copy())
    st.bar_chart(pretty_df.set_index("Hour")["Pickups Count"])


def render_revenue_by_hour(df: pd.DataFrame) -> None:
    st.markdown("#### Revenue by Hour")
    pretty_df = prettify_columns(df.copy())
    st.bar_chart(pretty_df.set_index("Hour")["Total Revenue"])


def render_table(title: str, df: pd.DataFrame) -> None:
    st.markdown(f"#### {title}")
    pretty_df = prettify_columns(df.copy())
    st.dataframe(pretty_df, use_container_width=True)

def render_borough_bar_chart(df: pd.DataFrame) -> None:
    st.markdown("#### Borough Bar Chart")
    pretty_df = prettify_columns(df.copy())

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(pretty_df["Borough"], pretty_df["Total Pickups"])
    ax.set_xlabel("Borough")
    ax.set_ylabel("Total Pickups")
    ax.set_title("Total Pickups by Borough")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    st.pyplot(fig)


def render_average_fare_by_pickup_zone(df: pd.DataFrame) -> None:
    st.markdown("#### Average Fare by Pickup Zone")
    pretty_df = prettify_columns(df.copy())
    st.dataframe(pretty_df, use_container_width=True)


def render_average_trip_distance_by_pickup_zone(df: pd.DataFrame) -> None:
    st.markdown("#### Average Trip Distance by Pickup Zone")
    pretty_df = prettify_columns(df.copy())
    st.dataframe(pretty_df, use_container_width=True)

def render_average_fare_per_distance_by_hour(df: pd.DataFrame) -> None:
    st.markdown("#### Average Fare per Distance by Hour")
    pretty_df = prettify_columns(df.copy())
    st.line_chart(pretty_df.set_index("Hour")["Average Fare per Distance ($/mi)"])


def render_revenue_per_distance_by_pickup_zone(df: pd.DataFrame) -> None:
    st.markdown("#### Revenue per Distance by Pickup Zone")
    pretty_df = prettify_columns(df.copy())
    st.dataframe(pretty_df, use_container_width=True)


def render_borough_share_summary(df: pd.DataFrame) -> None:
    st.markdown("#### Borough Share Summary")
    pretty_df = prettify_columns(df.copy())
    st.dataframe(pretty_df, use_container_width=True)


def render_average_fare_per_distance_by_borough(df: pd.DataFrame) -> None:
    st.markdown("#### Average Fare per Distance by Borough")
    pretty_df = prettify_columns(df.copy())

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(pretty_df["Borough"], pretty_df["Average Fare per Distance ($/mi)"])
    ax.set_xlabel("Borough")
    ax.set_ylabel("Average Fare per Distance ($/mi)")
    ax.set_title("Average Fare per Distance by Borough")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    st.pyplot(fig)

def render_average_fare_per_distance_by_pickup_zone(df: pd.DataFrame) -> None:
    st.markdown("#### Average Fare per Distance by Pickup Zone")
    pretty_df = prettify_columns(df.copy())
    st.dataframe(pretty_df, use_container_width=True)


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
    elif chart_key == "average_fare_per_distance_by_pickup_zone":
        render_average_fare_per_distance_by_pickup_zone(tables["average_fare_per_distance_by_pickup_zone"])
    elif chart_key == "average_fare_per_distance_by_borough":
        render_average_fare_per_distance_by_borough(tables["average_fare_per_distance_by_borough"])
    elif chart_key == "borough_bar_chart":
        render_borough_bar_chart(tables["borough_bar_chart"])
    elif chart_key == "average_fare_by_pickup_zone":
        render_average_fare_by_pickup_zone(tables["average_fare_by_pickup_zone"])
    elif chart_key == "average_trip_distance_by_pickup_zone":
        render_average_trip_distance_by_pickup_zone(tables["average_trip_distance_by_pickup_zone"])
    elif chart_key == "revenue_per_distance_by_pickup_zone":
        render_revenue_per_distance_by_pickup_zone(tables["revenue_per_distance_by_pickup_zone"])
    elif chart_key == "average_fare_per_distance_by_hour":
        render_average_fare_per_distance_by_hour(tables["average_fare_per_distance_by_hour"])
    elif chart_key == "borough_share_summary":
        render_borough_share_summary(tables["borough_share_summary"])
    elif chart_key == "revenue_per_distance_by_borough":
        render_revenue_per_distance_by_borough(tables["revenue_per_distance_by_borough"])
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
    "Average fare per distance by pickup zone": "average_fare_per_distance_by_pickup_zone",
    "Borough bar chart": "borough_bar_chart",
    "Average fare by pickup zone": "average_fare_by_pickup_zone",
    "Average trip distance by pickup zone": "average_trip_distance_by_pickup_zone",
    "Average fare per distance by pickup zone": "average_fare_per_distance_by_pickup_zone",
    "Average fare per distance by hour": "average_fare_per_distance_by_hour",
    "Borough share summary": "borough_share_summary",
    "Average fare per distance by borough": "average_fare_per_distance_by_borough",
}


def map_selected_kpis(ui_selected_kpis: Iterable[str]) -> list[str]:
    return [KPI_UI_TO_KEY[item] for item in ui_selected_kpis if item in KPI_UI_TO_KEY]


def map_selected_charts(ui_selected_charts: Iterable[str]) -> list[str]:
    return [CHART_UI_TO_KEY[item] for item in ui_selected_charts if item in CHART_UI_TO_KEY]