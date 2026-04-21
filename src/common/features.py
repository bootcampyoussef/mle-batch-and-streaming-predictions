import uuid
from typing import Iterable

import pandas as pd


CATEGORICAL_COLUMNS = ["PULocationID", "DOLocationID"]
FEATURE_COLUMNS = ["trip_route", "trip_distance"]
TARGET_COLUMN = "trip_duration_minutes"
RIDE_ID_COLUMN = "ride_id"


def generate_ride_ids(n_rows: int) -> list[str]:
    """Generate stable identifiers for batch prediction rows."""
    return [str(uuid.uuid4()) for _ in range(n_rows)]


def load_dataframe(source_uri: str) -> pd.DataFrame:
    """Load a Parquet dataset from a local path or URL."""
    return pd.read_parquet(source_uri)


def prepare_dataframe(df: pd.DataFrame, *, include_target: bool) -> pd.DataFrame:
    """Apply the shared feature engineering used by training and inference."""
    prepared = df.copy()
    prepared[CATEGORICAL_COLUMNS] = prepared[CATEGORICAL_COLUMNS].astype(str)

    if include_target:
        required_columns = {"lpep_pickup_datetime", "lpep_dropoff_datetime"}
        missing_columns = required_columns.difference(prepared.columns)
        if missing_columns:
            raise ValueError(
                "Cannot compute trip duration without these columns: "
                + ", ".join(sorted(missing_columns))
            )
        duration = prepared["lpep_dropoff_datetime"] - prepared["lpep_pickup_datetime"]
        prepared[TARGET_COLUMN] = duration.dt.total_seconds() / 60
        prepared = prepared[
            (prepared[TARGET_COLUMN] >= 1) & (prepared[TARGET_COLUMN] <= 60)
        ]

    prepared["trip_route"] = prepared["PULocationID"] + "_" + prepared["DOLocationID"]
    return prepared


def assign_ride_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Add ride IDs when they are not present in the input dataset."""
    prepared = df.copy()
    if RIDE_ID_COLUMN not in prepared:
        prepared[RIDE_ID_COLUMN] = generate_ride_ids(len(prepared))
    return prepared


def to_model_records(df: pd.DataFrame) -> list[dict]:
    """Convert a feature dataframe into the dict records expected by the model."""
    return df[FEATURE_COLUMNS].to_dict(orient="records")


def build_prediction_frame(
    df: pd.DataFrame,
    predictions: Iterable[float],
    *,
    model_reference: str,
) -> pd.DataFrame:
    """Combine prediction output with the most useful input columns."""
    result = pd.DataFrame(
        {
            RIDE_ID_COLUMN: df[RIDE_ID_COLUMN],
            "lpep_pickup_datetime": df["lpep_pickup_datetime"],
            "PULocationID": df["PULocationID"],
            "DOLocationID": df["DOLocationID"],
            "trip_distance": df["trip_distance"],
            "predicted_duration": predictions,
            "model_reference": model_reference,
        }
    )

    if TARGET_COLUMN in df:
        result["actual_duration"] = df[TARGET_COLUMN]
        result["diff"] = result["actual_duration"] - result["predicted_duration"]

    return result
