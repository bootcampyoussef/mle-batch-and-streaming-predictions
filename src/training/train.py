import click
import mlflow
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from src.common.config import get_settings
from src.common.features import (
    TARGET_COLUMN,
    load_dataframe,
    prepare_dataframe,
    to_model_records,
)
from src.common.model_registry import configure_tracking, ensure_experiment

settings = get_settings()


@click.command(help="Train the taxi duration model.")
@click.option(
    "--data-uri",
    default=settings.train_data_uri,
    help="URI to training data.",
)
@click.option(
    "--tracking-uri",
    default=settings.mlflow_tracking_uri,
    help="MLflow tracking server URI.",
)
@click.option(
    "--experiment-name",
    default=settings.experiment_name,
    help="MLflow experiment name.",
)
@click.option(
    "--registered-model-name",
    default=settings.registered_model_name,
    help="MLflow model name.",
)
@click.option(
    "--model-artifact-path",
    default=settings.model_artifact_path,
    help="Path to save model artifacts.",
)
@click.option(
    "--test-size",
    type=float,
    default=0.2,
    help="Fraction of data to use for testing.",
)
@click.option(
    "--random-state",
    type=int,
    default=42,
    help="Random seed for reproducibility.",
)
@click.option(
    "--run-name",
    default="train-linear-regression",
    help="MLflow run name.",
)
def main(
    data_uri: str,
    tracking_uri: str,
    experiment_name: str,
    registered_model_name: str,
    model_artifact_path: str,
    test_size: float,
    random_state: int,
    run_name: str,
) -> None:

    # Create the experiment on demand and log a single baseline pipeline.
    configure_tracking(tracking_uri)
    experiment_id = ensure_experiment(experiment_name)
    mlflow.set_experiment(experiment_name)

    df = load_dataframe(data_uri)
    prepared = prepare_dataframe(df, include_target=True)

    records = to_model_records(prepared)
    target = prepared[TARGET_COLUMN]
    train_records, valid_records, y_train, y_valid = train_test_split(
        records,
        target,
        test_size=test_size,
        random_state=random_state,
    )

    model = make_pipeline(DictVectorizer(), LinearRegression())

    with mlflow.start_run(
        experiment_id=experiment_id,
        run_name=run_name,
    ) as run:
        model.fit(train_records, y_train)
        predictions = model.predict(valid_records)
        rmse = root_mean_squared_error(y_valid, predictions)

        mlflow.log_params(
            {
                "train_data_uri": data_uri,
                "test_size": test_size,
                "random_state": random_state,
                "model_type": "LinearRegression",
                "feature_columns": "trip_route,trip_distance",
            }
        )
        mlflow.log_metric("rmse", float(rmse))
        mlflow.sklearn.log_model(
            sk_model=model,
            name=model_artifact_path,
            registered_model_name=registered_model_name,
            serialization_format="skops",
        )

        print(f"Run ID: {run.info.run_id}")
        print(f"RMSE: {rmse:.4f}")
        print(
            "Registered model: "
            f"{registered_model_name} (latest version will be auto-resolved by the batch flow and API)"
        )


if __name__ == "__main__":
    main()
