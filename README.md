# Urban Mobility NYC Geospatial Analysis

An end-to-end Python app for exploring NYC TLC taxi trip data through geospatial maps, interactive visual analytics, and business-oriented dashboard outputs.

The project focuses on **daily analysis** of **Yellow Taxi** and **Green Taxi** trip-record data from the NYC Taxi & Limousine Commission (TLC), with a user-facing Streamlit app that generates:
- daily static maps
- animated hourly maps
- KPI cards
- direct descriptive charts and tables
- filtered business-insight charts and tables

## Live App

The app is deployed online on **Streamlit Community Cloud**.

Replace the placeholder below with your deployed app URL:

```text
LIVE APP URL: https://urbanmobilitynycgeospatialanalysis-qsscpjra5ab4f7xnec3tfd.streamlit.app/

---

## 1. Project goals

This project was built to provide an accessible and extensible framework for analyzing urban mobility patterns in New York City using publicly available taxi trip data.

The main objectives are:

1. **Geospatial exploration**
   - visualize how pickups, dropoffs, revenue, and related quantities vary across NYC taxi zones

2. **Temporal exploration**
   - analyze how activity changes hour by hour during a selected day

3. **Business-oriented descriptive analytics**
   - build direct dashboards with volumes, revenues, and zone-based rankings

4. **Business-insight analytics**
   - derive more advanced indicators from the raw trip data, while using robustness filters to avoid unstable results

5. **User-facing delivery**
   - provide an app that allows the user to select the dataset, date, maps, and dashboard outputs from a simple interface

---

## 2. Data source

The project uses the publicly available **TLC Trip Record Data**.

Supported datasets:
- **Yellow Taxi**
- **Green Taxi**

The project also uses the NYC taxi zone shapefile for geographic aggregation and map generation.

---

## 3. Current scope

### Currently implemented
- Yellow Taxi and Green Taxi daily analysis
- daily static geospatial maps
- animated hourly map
- Streamlit app with multi-step interface
- KPI selection
- direct descriptive charts and tables
- filtered business-insight charts and tables
- dashboard validation notebook for metric testing

### Not implemented yet / future extensions
- full monthly mode in the UI
- automatic Power BI visual generation
- Power BI export layer finalization
- broader derived-metric library
- cross-day/month comparative analytics

---

## 4. Main outputs

### 4.1 Maps

#### Daily static map
A choropleth-style daily map showing selected quantities aggregated by zone, such as:
- pickups
- dropoffs
- revenue
- average fare
- average trip distance

#### Animated hourly map
An hourly animated map that shows how the selected daily activity evolves over time.

---

### 4.2 Dashboard categories

The app separates the dashboard outputs into three logical categories:

#### KPIs
Headline indicators such as:
- total pickups
- total dropoffs
- total revenue
- average fare
- average trip distance
- busiest pickup zone
- busiest dropoff zone

#### Charts & Tables
Direct descriptive outputs based on the full dataset, such as:
- pickups by hour
- revenue by hour
- top pickup zones
- top dropoff zones
- top zone-to-zone routes
- average fare by pickup zone
- average trip distance by pickup zone
- borough summary table
- borough bar chart

#### Business Insight Charts & Tables
More advanced derived outputs designed for business interpretation. Some of these are based on a **filtered trip-level dataset** to avoid unstable results caused by extreme short-distance anomalies. Other BI relevant functions will be added in future versions

Examples include:
- average fare per distance by pickup zone
- average fare per distance by hour
- average fare per distance by borough
- borough share summary

---

## 5. Why there are two dashboard layers

The project intentionally distinguishes between:

### A. Direct descriptive analytics
These outputs are computed from the **full dataset** and are suitable for:
- maps
- counts
- direct averages
- zone rankings
- revenue totals

### B. Business-insight analytics
These outputs involve **derived trip-level ratios**, such as:
- fare / distance

These metrics can become unstable when there are:
- extremely short trips
- zero or near-zero trip distances
- unusual or exceptional fare records

For this reason, some business-insight outputs are computed on a **filtered version of the trip-level data**, while direct descriptive outputs continue to use the full dataset.

This split keeps the descriptive layer faithful to the raw data, while making the derived BI layer more robust and interpretable.

---

## 6. Filtering strategy for business-insight metrics

As reported before, short trips (0.01 mi) in the minimum fare (3$) or airport stardard fare (70$) can rocket up the average fare per distance. Even if those exceptions are the minimum part of the data (the 99 percentile excludes those pathologic data most of the time) they still make the average absurdly high (e.g. in Hamilton heights, at Jan 15th 2025, would present an average fare over distance of around 200 $/mi). For this reason, filters to the dataset are applied to study this metric, excluding short trips leading to absurdely high fares. The process of testing the metric with and without filters, arriving to the conclusion for the filter choice, can be found in the Jupyter notebook notebooks/test_dashboard_metric_filter.ipynb .

The analysis lead to the current robustness filter used for fare-per-distance analysis, including the following impositions:

1. **Positive fare only**
   - `fare_amount > 0`

2. **Minimum trip distance**
   - `trip_distance >= 0.25`

3. **Maximum fare-per-distance threshold**
   - `fare_amount / trip_distance <= 100`

4. **Minimum sample size for reported groups**
   - at least `10` trips per aggregated group

This filter does not remove all the pathologic data (there are still fares at 100$/mi). However, the number of pathologic data/number of data is now so low that they don't affect the average metric, making those pathologic data completely irrelevant, as we wanted.

The purpose is not to “clean” the direct data outputs, but only to prevent unstable outliers from dominating the **Business Insight Charts & Tables**.

---

## 7. Project structure

```text
urban_mobility_NYC_geospatial_analysis/
│
├── app.py
├── app_backend.py
├── README.md
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── download.py
│   ├── validate.py
│   ├── preprocess.py
│   ├── mapping.py
│   ├── dashboard.py
│   └── render_python.py
│
├── data/
│   └── reference/
│       └── taxi_zones/
│
├── notebooks/
│   └── test_dashboard_metric_filter.ipynb
│
└── outputs/
    ├── maps/
    ├── dashboard/
    └── powerbi/
```

### Notes
- `app.py` contains the Streamlit UI logic.
- `app_backend.py` connects the UI to preprocessing, map generation, and dashboard preparation.
- `src/dashboard.py` contains analytical functions for KPI and dashboard payload generation.
- `src/render_python.py` contains Streamlit-side rendering logic for the Python dashboard.
- `notebooks/test_dashboard_metric_filter.ipynb` documents the reasoning used to validate and filter the fare-per-distance business metrics.

---

## 8. Core modules

### `src/config.py`
Contains dataset-specific column mappings and shared configuration values.

### `src/download.py`
Downloads or loads TLC parquet files.

### `src/validate.py`
Validates dataset names, required columns, and other structural assumptions.

### `src/preprocess.py`
Builds the daily processed outputs:
- filtered daily trip data
- daily zone summary
- hourly summary
- OD summary

### `src/mapping.py`
Handles:
- zone loading
- zone-summary merging
- map generation
- animated HTML map generation

### `src/dashboard.py`
Builds:
- KPI payloads
- direct dashboard tables
- business-insight filtered tables

### `src/render_python.py`
Renders dashboard content in Streamlit:
- KPI blocks
- tables
- bar charts
- line charts
- business-insight outputs

---

## 9. Installation

### 9.1 Create / activate environment

Example with conda:

```bash
conda create -n portfolio_env python=3.11
conda activate portfolio_env
```

### 9.2 Install dependencies

Install the libraries required by the project. Depending on your setup, these typically include:

```bash
pip install pandas geopandas matplotlib streamlit requests pyarrow folium branca
```

### 9.3 Parquet support

This project uses TLC parquet files. Make sure you have at least one parquet engine installed, for example:

```bash
pip install pyarrow
```

---

## 10. Running the app

From the project root:

```bash
python -m streamlit run app.py
```

If you are using Anaconda Prompt:

```bash
conda activate portfolio_env
python -m streamlit run app.py
```

To stop the app:

```text
Ctrl + C
```

---

## 11. How the app works

### Screen 1 — Welcome
Introduces the app and the outputs it can generate.

### Screen 2 — Analysis Setup
The user selects:
- dataset (Yellow or Green Taxi)
- year
- month
- day
- which map outputs to generate

Then the app:
- downloads / loads the relevant parquet
- preprocesses the selected day
- generates only the selected maps
- stores the processed daily data for dashboard use

### Screen 3 — Outputs and Dashboard Options
The user can:
- preview the generated maps
- optionally download them
- select KPI / Charts & Tables / Business Insight Charts & Tables
- generate the Python dashboard output
- later, select Power BI export when that layer is connected

---

## 12. Notebook for metric validation

The notebook:

```text
notebooks/test_dashboard_metric_filter.ipynb
```

was used to validate the derived business metrics before integrating them into the app.

Its purpose is to:
- inspect extreme short-distance trips
- test different robustness filters
- compare unstable and filtered versions of fare-per-distance metrics
- justify the final BI filtering strategy

This notebook is intentionally separated from the production app logic so that metric design can be validated independently.

---

## 13. Methodological note on fare-per-distance metrics

A raw average of:

```text
fare_amount / trip_distance
```

can become unstable because a small number of trips with very small distances can produce extremely large values.

For that reason, the project does **not** use the raw unfiltered mean for business-insight outputs.

Instead, the BI layer uses a filtered trip-level dataset before computing the average ratio.

This makes the resulting business-insight charts:
- more stable
- more interpretable
- more useful for dashboarding

while preserving the direct descriptive outputs on the full dataset.

---

## 14. Current limitations

- The current version focuses on **daily** analysis.
- Monthly analysis logic is planned but not yet fully enabled in the UI.
- The Power BI integration is still under development, even if present in the UI architecture of the following version.
- Some business metrics may still be refined as additional validation is performed.
- The animated HTML map can be heavy, so the app handles it differently from the static map.

---

## 15. Future work

Planned improvements include:
- monthly analysis mode
- Power BI-ready export pipeline
- automatic Power BI chart generation
- richer derived business metrics
- comparison across multiple dates
- stronger caching and output management
- improved dashboard styling and exportability

---

## 16. Why this project matters

This project is not only a map viewer or a chart generator.

Its purpose is to connect:
- **public urban mobility data**
- **geospatial visualization**
- **business-oriented descriptive analytics**
- **derived insight generation**
- **interactive delivery through a user-facing app**

The long-term goal is to make urban mobility analytics more accessible, reproducible, and extensible, while keeping a strong distinction between:
- raw descriptive reporting
- robust business insight analysis

---

## 17. Suggested use cases

Possible use cases include:
- exploratory urban mobility analysis
- portfolio demonstration of geospatial analytics
- business-style dashboard prototyping
- experimentation with TLC trip data
- validation of robust metrics for short-trip-heavy datasets
- future Power BI automation experiments

---

## 18. Status

The project is currently in an **advanced prototype stage**:
- the core app flow works
- map generation works
- dashboard generation works
- direct and business-insight layers are separated conceptually
- Power BI automation remains a future extension

---

## 19. License / usage

If you want, add your preferred license here.

Example:

```text
MIT License
```

or:

```text
This project is shared for portfolio and educational purposes.
```
