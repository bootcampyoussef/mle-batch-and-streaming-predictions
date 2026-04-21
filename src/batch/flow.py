import os
from datetime import datetime, timezone
from pathlib import Path

from src.common.config import get_settings
from src.common.features import (
    assign_ride_ids,
    build_prediction_frame,
    load_dataframe,
    prepare_dataframe,
    to_model_records,
)
from src.common.model_registry import (
    configure_tracking,
    load_pyfunc_model,
    resolve_model_uri,
)

# Prefect reads its API URL from the process environment when a flow starts.
# Loading the repo settings here keeps direct `python -m ...` and notebook runs
# attached to the local Prefect server defined in `.env`.
os.environ.setdefault("PREFECT_API_URL", get_settings().prefect_api_url)

from prefect import flow, get_run_logger, task  # noqa: E402


def default_output_path(output_dir: Path) -> Path:
    """Create a timestamped parquet path for one batch scoring run."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return output_dir / f"batch_predictions_{timestamp}.parquet"


@task(name="score_dataframe")
def score_dataframe(
    input_uri: str,
    tracking_uri: str,
    output_path: str,
    *,
    model_uri: str | None = None,
    model_name: str | None = None,
    model_alias: str | None = None,
    model_stage: str | None = None,
    model_version: str | None = None,
    run_id: str | None = None,
    model_artifact_path: str = "model",
) -> str:
    logger = get_run_logger()
    logger.info("Reading input from %s", input_uri)

    df = load_dataframe(input_uri)
    # Some inputs include observed durations and some do not. We keep one
    # flow entrypoint and infer whether the evaluation columns can be added.
    prepared = assign_ride_ids(
        prepare_dataframe(
            df,
            include_target={"lpep_pickup_datetime", "lpep_dropoff_datetime"}.issubset(
                df.columns
            ),
        )
    )

    configure_tracking(tracking_uri)
    resolved_model_uri = resolve_model_uri(
        tracking_uri=tracking_uri,
        model_uri=model_uri,
        model_name=model_name,
        model_alias=model_alias,
        model_stage=model_stage,
        model_version=model_version,
        run_id=run_id,
        artifact_path=model_artifact_path,
    )
    logger.info("Loading model from %s", resolved_model_uri)
    model = load_pyfunc_model(resolved_model_uri)

    predictions = model.predict(to_model_records(prepared))
    prediction_frame = build_prediction_frame(
        prepared,
        predictions,
        model_reference=resolved_model_uri,
    )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    prediction_frame.to_parquet(destination, index=False)
    logger.info("Saved predictions to %s", destination)
    return str(destination)


@flow(name="score-green-taxi-batch")
def score_batch_flow(
    input_uri: str | None = None,
    output_path: str | None = None,
    tracking_uri: str | None = None,
    model_uri: str | None = None,
    model_name: str | None = None,
    model_alias: str | None = None,
    model_stage: str | None = None,
    model_version: str | None = None,
    run_id: str | None = None,
    model_artifact_path: str | None = None,
) -> str:
    settings = get_settings()
    resolved_output_path = (
        Path(output_path)
        if output_path
        else default_output_path(settings.batch_output_dir)
    )

    return score_dataframe(
        input_uri=input_uri or settings.batch_input_uri,
        tracking_uri=tracking_uri or settings.mlflow_tracking_uri,
        output_path=str(resolved_output_path),
        model_uri=model_uri or settings.model_uri,
        model_name=model_name or settings.registered_model_name,
        model_alias=model_alias or settings.model_alias,
        model_stage=model_stage or settings.model_stage,
        model_version=model_version or settings.model_version,
        run_id=run_id or settings.run_id,
        model_artifact_path=model_artifact_path or settings.model_artifact_path,
    )


if __name__ == "__main__":
    print(score_batch_flow())
