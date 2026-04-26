import os

from src.batch.flow import score_batch_flow
from src.common.config import get_settings


def main() -> None:
    settings = get_settings()
    cron = os.getenv("BATCH_CRON", "0 6 1 * *")

    # This helper mirrors the batch lesson: create a simple deployment that
    # can be inspected and triggered from the local Prefect UI.
    score_batch_flow.serve(
        name="green-taxi-batch",
        cron=cron,
        parameters={
            "input_uri": settings.batch_input_uri,
            "tracking_uri": settings.mlflow_tracking_uri,
            "model_uri": settings.model_uri,
            "model_name": settings.registered_model_name,
            "model_alias": settings.model_alias,
            "model_stage": settings.model_stage,
            "model_version": settings.model_version,
            "run_id": settings.run_id,
            "model_artifact_path": settings.model_artifact_path,
        },
        tags=["batch", "local", "prefect"],
    )


if __name__ == "__main__":
    main()
