from typing import Any

import mlflow
from mlflow import MlflowClient


def configure_tracking(tracking_uri: str) -> None:
    """Point MLflow APIs at the configured tracking server."""
    mlflow.set_tracking_uri(tracking_uri)


def ensure_experiment(experiment_name: str) -> str:
    """Create the experiment on demand and return its identifier."""
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is not None:
        return experiment.experiment_id

    return mlflow.create_experiment(experiment_name)


def resolve_model_uri(
    *,
    tracking_uri: str,
    model_uri: str | None = None,
    model_name: str | None = None,
    model_version: str | None = None,
    model_alias: str | None = None,
    model_stage: str | None = None,
    run_id: str | None = None,
    artifact_path: str = "model",
) -> str:
    """Resolve a model URI from either a direct URI, a run ID, or the registry.

    The teaching repo uses this one resolution path everywhere so the
    training script, batch flow, and API all agree on which model version
    should be active.
    """
    configure_tracking(tracking_uri)

    # Keep the override order explicit: direct URI first, then a run artifact,
    # then progressively more specific registry selectors.
    if model_uri:
        return model_uri

    if run_id:
        return f"runs:/{run_id}/{artifact_path}"

    if not model_name:
        raise ValueError(
            "Model resolution requires either MODEL_URI, MODEL_RUN_ID, or MLFLOW_MODEL_NAME."
        )

    if model_alias:
        return f"models:/{model_name}@{model_alias}"

    if model_version:
        return f"models:/{model_name}/{model_version}"

    client = MlflowClient(tracking_uri=tracking_uri)
    versions = list(client.search_model_versions(f"name='{model_name}'"))
    if not versions:
        raise ValueError(
            f"No registered model versions found for '{model_name}'. "
            "Train and register a model first, or set MODEL_RUN_ID."
        )

    if model_stage:
        staged_versions = [
            version for version in versions if version.current_stage == model_stage
        ]
        if not staged_versions:
            raise ValueError(
                f"No versions for '{model_name}' found in stage '{model_stage}'."
            )
        latest = max(staged_versions, key=lambda version: int(version.version))
        return f"models:/{model_name}/{latest.version}"

    latest = max(versions, key=lambda version: int(version.version))
    return f"models:/{model_name}/{latest.version}"


def load_pyfunc_model(model_uri: str) -> Any:
    """Load a pyfunc model from MLflow."""
    return mlflow.pyfunc.load_model(model_uri)
