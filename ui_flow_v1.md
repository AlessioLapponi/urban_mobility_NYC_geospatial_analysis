# UI Flow v1

## Goal
Provide a simple user interface that lets the user:
- choose the TLC dataset and analysis date
- choose which map outputs to generate
- optionally generate a dashboard
- optionally export dashboard-ready data for Power BI

The UI should stay simple in v1 while preserving a clean path for later month-mode support.

---

## Screen 1 — Welcome

### Contents
- Short textual description of the app
- Brief explanation of what the app can produce:
  - daily static geospatial map
  - animated hourly choropleth map
  - optional dashboard
  - optional Power BI-ready export
- **Continue** button

### Purpose
Introduce the app and move the user to the configuration screen.

---

## Screen 2 — Analysis Setup

### Contents
- Dataset selector:
  - Yellow Taxi
  - Green Taxi
- Year selector
- Month selector
- Day selector

### Map output selector
The user must also choose which map outputs to generate:
- Daily static map
- Animated hourly map

Rules:
- one or both may be selected
- if neither is selected, the app may still continue for dashboard/export-only mode

### Month mode placeholder
The architecture should already support:
- `analysis_mode = "day"`
- `analysis_mode = "month"`

### v1 behavior
For version 1:
- day mode is the only enabled mode in the UI
- the day selector is therefore effectively required

### Later extension
Month mode should be easy to add later by allowing:
- no day selection
- or a toggle between:
  - Daily analysis
  - Monthly analysis

### Future month-mode rule
If month mode is enabled later:
- animated hourly maps are disabled
- daily static maps are disabled unless a specific day is selected
- dashboard and export remain available
- optional monthly aggregated map can be added later

### Continue button behavior
When the user clicks **Continue**, the system should:
1. validate the selected inputs
2. download/load the relevant TLC parquet
3. preprocess the selected data
4. generate only the selected map outputs:
   - daily static map HTML if selected
   - animated hourly map HTML if selected
5. store the generated output paths
6. move to Screen 3

### Processing feedback
Between Screen 2 and Screen 3, the UI should show a simple processing status, for example:
- Downloading data...
- Preparing summaries...
- Generating selected maps...
- Done

---

## Screen 3 — Outputs and Dashboard Options

### Map outputs
Show buttons or links only for the outputs that were actually generated:
- **Open Daily Static Map**
- **Open Animated Hourly Map**

If a map type was not selected in Screen 2, its button should be hidden or disabled.

### Dashboard section
Allow the user to configure dashboard generation only at this stage.

#### Dashboard options
- KPI selector
- chart/table selector
- output type selector:
  - Python-native dashboard output
  - Power BI-ready export

#### Generate button
A button such as:
- **Generate Dashboard / Export**

This button should trigger only the dashboard/export part, not the map generation.

---

## Dashboard Block Vocabulary (v1)

### KPI cards
- total pickups
- total dropoffs
- total revenue
- average fare
- average trip distance
- busiest pickup zone
- busiest dropoff zone

### Charts / tables
- pickups by hour
- revenue by hour
- top pickup zones
- top dropoff zones
- top zone-to-zone routes
- average fare by pickup zone
- average trip distance by pickup zone
- borough summary table
- borough bar chart

### Recommended selection rule
To avoid clutter in v1:
- maximum 4 dashboard elements total

---

## Output Logic

### If day mode is used
Available outputs:
- daily static map
- animated hourly map
- dashboard
- Power BI-ready export

### If month mode is added later
Available outputs:
- monthly dashboard
- Power BI-ready export
- optional monthly aggregated map

Unavailable outputs:
- animated hourly map
- daily static day-specific map unless a day is chosen

---

## Backend Contract

### Inputs
- dataset
- year
- month
- day
- analysis_mode
- selected_map_outputs

### v1 default
- `analysis_mode = "day"`

### Required backend stages
1. data download/load
2. schema validation
3. preprocessing
4. summary table generation
5. selected map generation
6. dashboard generation
7. export packaging

### Design requirement
Even in v1, the internal logic should not hardcode the assumption that only daily mode will ever exist.

---

## Power BI Strategy v1

### v1 objective
Support **Power BI-ready outputs**, not fully automatic Power BI dashboard creation.

### Export package examples
- daily_zone_summary.csv
- hourly_zone_summary.csv
- od_summary.csv
- borough_summary.csv
- dashboard_kpis.csv

Optional:
- dashboard_manifest.json

---

## Version 1 Scope

### Included
- Yellow Taxi
- Green Taxi
- map-type selection in Screen 2
- daily static map generated only if selected
- animated hourly map generated only if selected
- dashboard configuration in Screen 3
- Power BI-ready export in Screen 3
- architecture prepared for future month mode

### Not included yet
- month mode enabled in the UI
- automatic Power BI visual construction
- unlimited dashboard customization

---

## Success Criteria

The UI flow is successful if the user can:
1. open the app
2. select dataset and date
3. choose which map outputs to generate
4. trigger preprocessing and selected map generation
5. access the generated maps from Screen 3
6. choose dashboard items
7. generate Python-native or Power BI-ready dashboard outputs
8. later extend the same logic to month mode without rewriting the architecture
