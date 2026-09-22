import pandas as pd
import pytest

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
                ["2025-01-01T10:00:00", "2025-01-01T11:00:00"]
            ),
            "lpep_dropoff_datetime": pd.to_datetime(
                ["2025-01-01T10:10:00", "2025-01-01T11:22:00"]
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


@pytest.mark.parametrize("include_target", [True, False])
def test_distance_filter_applies_only_when_preparing_target(include_target):
    distances = [0.0, 0.09, 0.1, 1.5, 100.0, 100.01, float("nan"), float("inf")]
    raw = pd.concat([sample_dataframe().iloc[[0]]] * len(distances), ignore_index=True)
    raw["trip_distance"] = distances
    if not include_target:
        raw = raw.drop(columns=["lpep_dropoff_datetime"])

    prepared = prepare_dataframe(raw, include_target=include_target)

    if include_target:
        assert prepared["trip_distance"].tolist() == [0.1, 1.5, 100.0]
        assert prepared.index.tolist() == [2, 3, 4]
    else:
        assert len(prepared) == len(raw)
        pd.testing.assert_series_equal(prepared["trip_distance"], raw["trip_distance"])
        assert TARGET_COLUMN not in prepared


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
