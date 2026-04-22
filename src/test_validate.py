import pandas as pd
from validate import validate_dataset_name, validate_trip_columns, validate_zone_columns

# Fake yellow trip dataframe
trip_df = pd.DataFrame(columns=[
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "trip_distance",
    "fare_amount",
    "total_amount",
])

# Fake zones dataframe
zones_df = pd.DataFrame(columns=[
    "LocationID",
    "zone",
    "borough",
    "geometry",
])

validate_dataset_name("yellow")
validate_trip_columns(trip_df, "yellow")
validate_zone_columns(zones_df)

print("All validation tests passed.")