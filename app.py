from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from app_backend import run_analysis

import streamlit as st

import streamlit.components.v1 as components


# =========================
# Configuration
# =========================
APP_TITLE = "Urban Mobility NYC Geospatial Analysis"
SUPPORTED_DATASETS = {
    "yellow": "Yellow Taxi",
    "green": "Green Taxi",
}
MAP_OPTIONS = {
    "daily_static": "Daily static map",
    "animated_hourly": "Animated hourly map",
}
DASHBOARD_KPIS = [
    "Total pickups",
    "Total dropoffs",
    "Total revenue",
    "Average fare",
    "Average trip distance",
    "Busiest pickup zone",
    "Busiest dropoff zone",
]
DASHBOARD_CHARTS = [
    "Pickups by hour",
    "Revenue by hour",
    "Top pickup zones",
    "Top dropoff zones",
    "Top zone-to-zone routes",
    "Average fare by pickup zone",
    "Average trip distance by pickup zone",
    "Borough summary table",
    "Borough bar chart",
]
OUTPUT_TYPES = {
    "python": "Python-native dashboard output",
    "powerbi": "Power BI-ready export",
}


# =========================
# Data structures
# =========================
@dataclass
class AnalysisSelection:
    dataset: str
    year: int
    month: int
    day: int
    selected_maps: List[str]
    analysis_mode: str = "day"  # reserved for later month mode


# =========================
# Session state helpers
# =========================
def init_state() -> None:
    defaults = {
        "screen": 1,
        "analysis_ready": False,
        "selection": None,
        "generated_outputs": {},
        "dashboard_generated": False,
        "dashboard_message": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_screen(screen_number: int) -> None:
    st.session_state.screen = screen_number
    st.rerun()


# =========================
# Placeholder backend hooks
# Replace these later with real generation functions
# =========================
def mock_run_analysis(selection: AnalysisSelection) -> Dict[str, str]:
    """Simulate preprocessing + selected map generation.

    Replace this function later with the real backend orchestration:
    - download/load parquet
    - preprocess selected day
    - generate only requested maps
    - return real output paths
    """
    outputs: Dict[str, str] = {}

    fake_output_dir = Path("outputs/maps")
    if "daily_static" in selection.selected_maps:
        outputs["daily_static"] = str(
            fake_output_dir / f"daily_static_{selection.dataset}_{selection.year}-{selection.month:02d}-{selection.day:02d}.html"
        )
    if "animated_hourly" in selection.selected_maps:
        outputs["animated_hourly"] = str(
            fake_output_dir / f"animated_hourly_{selection.dataset}_{selection.year}-{selection.month:02d}-{selection.day:02d}.html"
        )

    return outputs


def mock_generate_dashboard(
    selected_kpis: List[str],
    selected_charts: List[str],
    output_type: str,
) -> str:
    if not selected_kpis and not selected_charts:
        return "Please select at least one KPI or chart before generating the dashboard/export."

    total_items = len(selected_kpis) + len(selected_charts)
    if total_items > 4:
        return "Please select at most 4 dashboard elements in total."

    output_label = OUTPUT_TYPES[output_type]
    return (
        f"Dashboard/export prepared. "
        f"Selected {len(selected_kpis)} KPI(s), {len(selected_charts)} chart/table item(s). "
        f"Output mode: {output_label}."
    )


# =========================
# Screen renderers
# =========================
def render_screen_1() -> None:
    st.title(APP_TITLE)
    st.subheader("Welcome")

    st.markdown(
        """
        This app lets you analyze NYC TLC taxi data and generate:
        - a **daily static geospatial map**
        - an **animated hourly choropleth map**
        - an optional **dashboard**
        - an optional **Power BI-ready export**

        The current version already generates the selected map outputs and provides the dashboard/export selection flow.
        """
    )

    if st.button("Continue", type="primary"):
        go_to_screen(2)



def render_screen_2() -> None:
    st.title(APP_TITLE)
    st.subheader("Analysis Setup")

    st.markdown(
        "Choose the dataset, date, and which map outputs to generate. "
        "For version 1, only **daily mode** is enabled."
    )

    with st.form("analysis_setup_form"):
        dataset = st.selectbox(
            "Dataset",
            options=list(SUPPORTED_DATASETS.keys()),
            format_func=lambda key: SUPPORTED_DATASETS[key],
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.selectbox("Year", options=list(range(2022, 2027)), index=2)
        with col2:
            month = st.selectbox(
                "Month",
                options=list(range(1, 13)),
                index=0,
                format_func=lambda m: [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ][m - 1],
            )
        with col3:
            day = st.selectbox("Day", options=list(range(1, 32)), index=14)

        st.markdown("**Map outputs to generate**")
        selected_maps = []
        daily_static_checked = st.checkbox(MAP_OPTIONS["daily_static"], value=True)
        animated_hourly_checked = st.checkbox(MAP_OPTIONS["animated_hourly"], value=True)

        if daily_static_checked:
            selected_maps.append("daily_static")
        if animated_hourly_checked:
            selected_maps.append("animated_hourly")

        st.caption(
            "Month mode is reserved in the architecture but not enabled in v1. "
            "When added later, animated hourly maps will be disabled in month mode."
        )

        submitted = st.form_submit_button("Continue")

    if submitted:
        if not selected_maps:
            st.warning("No map selected. You can still proceed later for dashboard-only mode, but for this prototype select at least one map.")
            return

        selection = AnalysisSelection(
            dataset=dataset,
            year=year,
            month=month,
            day=day,
            selected_maps=selected_maps,
            analysis_mode="day",
        )

        # Placeholder processing status
        with st.status("Processing selected analysis...", expanded=True) as status:
            st.write("Validating inputs...")
            st.write("Downloading/loading data...")
            st.write("Preparing summaries...")
            st.write("Generating selected maps...")
            generated_outputs = run_analysis(selection)
            status.update(label="Analysis ready", state="complete")

        st.session_state.selection = selection
        st.session_state.generated_outputs = generated_outputs
        st.session_state.analysis_ready = True
        go_to_screen(3)

    if st.button("Back"):
        go_to_screen(1)



def render_screen_3() -> None:
    st.title(APP_TITLE)
    st.subheader("Outputs and Dashboard Options")

    selection: AnalysisSelection | None = st.session_state.selection
    generated_outputs: Dict[str, str] = st.session_state.generated_outputs

    if not st.session_state.analysis_ready or selection is None:
        st.warning("No analysis is ready yet. Please complete Screen 2 first.")
        if st.button("Go to Analysis Setup"):
            go_to_screen(2)
        return

    st.markdown("### Selected analysis")
    st.write(
        {
            "dataset": SUPPORTED_DATASETS[selection.dataset],
            "year": selection.year,
            "month": selection.month,
            "day": selection.day,
            "analysis_mode": selection.analysis_mode,
            "selected_maps": [MAP_OPTIONS[key] for key in selection.selected_maps],
        }
    )

    st.markdown("### Generated map outputs")

    available_map_options = {}

    if "daily_static" in generated_outputs:
        daily_path = Path(generated_outputs["daily_static"])
        if daily_path.exists():
            available_map_options["Daily static map"] = daily_path
        else:
            st.error(f"Daily static map file not found: {daily_path}")
    else:
        st.caption("Daily static map not generated.")

    if "animated_hourly" in generated_outputs:
        animated_path = Path(generated_outputs["animated_hourly"])
        if animated_path.exists():
            available_map_options["Animated hourly map"] = animated_path
        else:
            st.error(f"Animated hourly map file not found: {animated_path}")
    else:
        st.caption("Animated hourly map not generated.")

    if available_map_options:
        selected_map_label = st.radio(
            "Choose which generated map to display",
            options=list(available_map_options.keys()),
            horizontal=True,
        )

        selected_map_path = available_map_options[selected_map_label]

        try:
            html_content = selected_map_path.read_text(encoding="utf-8")
            components.html(html_content, height=700, scrolling=True)
        except Exception as e:
            st.error(f"Could not load the selected map: {e}")
    else:
        st.info("No generated maps are currently available to display.")

    st.divider()
    st.markdown("### Dashboard generation")
    st.caption("Select up to 4 total KPI/chart items.")

    with st.form("dashboard_form"):
        selected_kpis = st.multiselect("KPI cards", options=DASHBOARD_KPIS)
        selected_charts = st.multiselect("Charts / tables", options=DASHBOARD_CHARTS)
        output_type = st.radio(
            "Output type",
            options=list(OUTPUT_TYPES.keys()),
            format_func=lambda key: OUTPUT_TYPES[key],
            horizontal=False,
        )

        dashboard_submitted = st.form_submit_button("Generate Dashboard / Export")

    if dashboard_submitted:
        message = mock_generate_dashboard(selected_kpis, selected_charts, output_type)
        st.session_state.dashboard_generated = True
        st.session_state.dashboard_message = message
        st.rerun()

    if st.session_state.dashboard_generated:
        st.info(st.session_state.dashboard_message)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Back to Setup"):
            go_to_screen(2)

    with col2:
        if st.button("Start Over"):
            for key in [
                "screen",
                "analysis_ready",
                "selection",
                "generated_outputs",
                "dashboard_generated",
                "dashboard_message",
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            init_state()
            go_to_screen(1)


# =========================
# Main app entry point
# =========================
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_state()

    screen = st.session_state.screen

    if screen == 1:
        render_screen_1()
    elif screen == 2:
        render_screen_2()
    elif screen == 3:
        render_screen_3()
    else:
        st.error("Unknown screen state.")


if __name__ == "__main__":
    main()
