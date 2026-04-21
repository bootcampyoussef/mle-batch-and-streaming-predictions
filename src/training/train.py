import argparse

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the taxi duration model.")
    settings = get_settings()

    parser.add_argument("--data-uri", default=settings.train_data_uri)
    parser.add_argument("--tracking-uri", default=settings.mlflow_tracking_uri)
    parser.add_argument("--experiment-name", default=settings.experiment_name)
    parser.add_argument(
        "--registered-model-name", default=settings.registered_model_name
    )
    parser.add_argument("--model-artifact-path", default=settings.model_artifact_path)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--run-name", default="train-linear-regression")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Keep the script behavior aligned with the notebook chapter by creating
    # the experiment on demand and logging a single baseline pipeline.
    configure_tracking(args.tracking_uri)
    experiment_id = ensure_experiment(args.experiment_name)
    mlflow.set_experiment(args.experiment_name)

    df = load_dataframe(args.data_uri)
    prepared = prepare_dataframe(df, include_target=True)

    records = to_model_records(prepared)
    target = prepared[TARGET_COLUMN]
    train_records, valid_records, y_train, y_valid = train_test_split(
        records,
        target,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    model = make_pipeline(DictVectorizer(), LinearRegression())

    with mlflow.start_run(
        experiment_id=experiment_id,
        run_name=args.run_name,
    ) as run:
        model.fit(train_records, y_train)
        predictions = model.predict(valid_records)
        rmse = root_mean_squared_error(y_valid, predictions)

        mlflow.log_params(
            {
                "train_data_uri": args.data_uri,
                "test_size": args.test_size,
                "random_state": args.random_state,
                "model_type": "LinearRegression",
                "feature_columns": "trip_route,trip_distance",
            }
        )
        mlflow.log_metric("rmse", float(rmse))
        mlflow.sklearn.log_model(
            sk_model=model,
            name=args.model_artifact_path,
            registered_model_name=args.registered_model_name,
            serialization_format="skops",
        )

        print(f"Run ID: {run.info.run_id}")
        print(f"RMSE: {rmse:.4f}")
        print(
            "Registered model: "
            f"{args.registered_model_name} (latest version will be auto-resolved by the batch flow and API)"
        )


if __name__ == "__main__":
    main()
