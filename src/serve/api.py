from functools import lru_cache
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.common.config import get_settings
from src.common.model_registry import (
    configure_tracking,
    load_pyfunc_model,
    resolve_model_uri,
)


class PredictionRequest(BaseModel):
    PULocationID: str | int = Field(..., description="Pickup location ID")
    DOLocationID: str | int = Field(..., description="Dropoff location ID")
    trip_distance: float = Field(..., ge=0, description="Trip distance in miles")


class PredictionResponse(BaseModel):
    prediction: float
    model_uri: str


app = FastAPI(title="Green Taxi Duration API", version="0.1.0")


@lru_cache(maxsize=1)
def get_model_bundle() -> tuple[str, Any]:
    """Load the active MLflow model once and reuse it across API requests."""
    settings = get_settings()
    configure_tracking(settings.mlflow_tracking_uri)
    model_uri = resolve_model_uri(
        tracking_uri=settings.mlflow_tracking_uri,
        model_uri=settings.model_uri,
        model_name=settings.registered_model_name,
        model_alias=settings.model_alias,
        model_stage=settings.model_stage,
        model_version=settings.model_version,
        run_id=settings.run_id,
        artifact_path=settings.model_artifact_path,
    )
    return model_uri, load_pyfunc_model(model_uri)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    model_uri, model = get_model_bundle()
    record = {
        "trip_route": f"{request.PULocationID}_{request.DOLocationID}",
        "trip_distance": request.trip_distance,
    }
    prediction = model.predict([record])
    return PredictionResponse(prediction=float(prediction[0]), model_uri=model_uri)
