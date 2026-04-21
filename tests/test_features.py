import pandas as pd

from src.common.features import (
    TARGET_COLUMN,
    assign_ride_ids,
    build_prediction_frame,
    prepare_dataframe,
    to_model_records,
)


def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "lpep_pickup_datetime": pd.to_datetime(
                ["2023-01-01T10:00:00", "2023-01-01T11:00:00"]
            ),
            "lpep_dropoff_datetime": pd.to_datetime(
                ["2023-01-01T10:10:00", "2023-01-01T11:22:00"]
            ),
            "PULocationID": [1, 2],
            "DOLocationID": [3, 4],
            "trip_distance": [1.5, 2.5],
        }
    )


def test_prepare_dataframe_builds_features_and_target():
    prepared = prepare_dataframe(sample_dataframe(), include_target=True)

    assert TARGET_COLUMN in prepared.columns
    assert prepared["trip_route"].tolist() == ["1_3", "2_4"]
    assert prepared[TARGET_COLUMN].round(0).tolist() == [10.0, 22.0]


def test_assign_ride_ids_adds_column_once():
    prepared = assign_ride_ids(
        prepare_dataframe(sample_dataframe(), include_target=True)
    )

    assert "ride_id" in prepared.columns
    assert len(prepared["ride_id"].unique()) == len(prepared)


def test_build_prediction_frame_includes_actuals_when_present():
    prepared = assign_ride_ids(
        prepare_dataframe(sample_dataframe(), include_target=True)
    )
    records = to_model_records(prepared)
    prediction_frame = build_prediction_frame(
        prepared,
        predictions=[12.0, 20.0],
        model_reference="runs:/abc/model",
    )

    assert len(records) == 2
    assert prediction_frame["model_reference"].iloc[0] == "runs:/abc/model"
    assert prediction_frame["diff"].round(0).tolist() == [-2.0, 2.0]
