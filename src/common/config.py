import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Show only errors from mlflow.utils; skip info and warning messages.
logging.getLogger("mlflow.utils").setLevel(logging.ERROR)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(
    path_value: str | None, *, default: Path | None = None
) -> Path:
    """Resolve a path relative to the project root when not absolute."""
    if not path_value:
        if default is None:
            raise ValueError("Expected a path value or default path.")
        return default

    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


@dataclass(frozen=True)
class ProjectSettings:
    """Centralized settings used by the scripts and notebooks."""

    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
    prefect_api_url: str = os.getenv("PREFECT_API_URL", "http://127.0.0.1:4200/api")
    experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "green-taxi-duration")
    registered_model_name: str = os.getenv("MLFLOW_MODEL_NAME", "green-taxi-duration")
    model_uri: str | None = os.getenv("MODEL_URI") or None
    model_alias: str | None = os.getenv("MODEL_ALIAS") or None
    model_stage: str | None = os.getenv("MODEL_STAGE") or None
    model_version: str | None = os.getenv("MODEL_VERSION") or None
    run_id: str | None = os.getenv("MODEL_RUN_ID") or None
    model_artifact_path: str = os.getenv("MODEL_ARTIFACT_PATH", "model")
    train_data_uri: str = os.getenv(
        "TRAIN_DATA_URI",
        "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-01.parquet",
    )
    batch_input_uri: str = os.getenv(
        "BATCH_INPUT_URI",
        "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-02.parquet",
    )
    batch_output_dir: Path = field(
        default_factory=lambda: resolve_project_path(
            os.getenv("BATCH_OUTPUT_DIR"), default=PROJECT_ROOT / "data" / "predictions"
        )
    )
    artifacts_dir: Path = field(
        default_factory=lambda: resolve_project_path(
            os.getenv("MLFLOW_ARTIFACTS_DIR"),
            default=PROJECT_ROOT / "storage" / "mlartifacts",
        )
    )


def get_settings() -> ProjectSettings:
    """Return project settings loaded from environment variables."""
    return ProjectSettings()
