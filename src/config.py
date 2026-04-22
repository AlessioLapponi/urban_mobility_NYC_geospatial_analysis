SUPPORTED_DATASETS = {
    "yellow": {
        "file_prefix": "yellow_tripdata",
        "pickup_datetime": "tpep_pickup_datetime",
        "dropoff_datetime": "tpep_dropoff_datetime",
        "pickup_zone": "PULocationID",
        "dropoff_zone": "DOLocationID",
        "trip_distance": "trip_distance",
        "fare_amount": "fare_amount",
        "total_amount": "total_amount",
    },
    "green": {
        "file_prefix": "green_tripdata",
        "pickup_datetime": "lpep_pickup_datetime",
        "dropoff_datetime": "lpep_dropoff_datetime",
        "pickup_zone": "PULocationID",
        "dropoff_zone": "DOLocationID",
        "trip_distance": "trip_distance",
        "fare_amount": "fare_amount",
        "total_amount": "total_amount",
    },
}

SUPPORTED_METRICS = {
    "pickups": {
        "label": "Number of Pickups",
        "column": "pickups_count",
    },
    "dropoffs": {
        "label": "Number of Dropoffs",
        "column": "dropoffs_count",
    },
    "revenue": {
        "label": "Total Revenue",
        "column": "total_revenue",
    },
    "avg_fare": {
        "label": "Average Fare",
        "column": "avg_fare",
    },
    "avg_trip_distance": {
        "label": "Average Trip Distance",
        "column": "avg_trip_distance",
    },
}

REQUIRED_ZONE_COLUMNS = [
    "LocationID",
    "zone",
    "borough",
    "geometry",
]