# Batch and Stream Predictions

In this repository you will get a short introduction into `MLFlow` and how to use it for experiment and model tracking. You will deploy your own MLFlow server on GCP and use the model registry to deploy a model as a batch and stream prediction service.

We first will train a simple model on the `Green Taxi Trip Records` dataset from the [NYC Taxi and Limousine Commission](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page). The experiments will be tracked with `MLFlow` and the best model will be registered in the model registry. This step is normally done by a data scientist.

The batch prediction service will be orchestrated with `prefect` and will upload the raw data and predictions to a GCS bucket. The stream prediction service will be deployed as a `Google Cloud Function`.

In the end you will have a fully functional MLFlow server and an understanding how to build batch and streaming prediction services.

## Setup

### MLFlow Server

Follow the steps in [01_setup_mlflow_server](./01_setup_mlflow_server.md) to setup your own MLFlow server on GCP.

### Train the Model

Follow the steps in [02_train_ml_model](./02_train_ml_model.ipynb) to train a simple model on the `Green Taxi Trip Records` dataset from the [NYC Taxi and Limousine Commission](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page) and how to track the experiments with `MLFlow`.

### Batch Prediction Service

Follow the steps in [03_batch_deployment](./03_batch_deployment.ipynb) and the python scripts in [src/batch](./src/batch) to setup a batch prediction service with `prefect` and `MLFlow`.

### Stream Prediction Service

Follow the steps in [04_stream_deployment](./04_stream_deployment.md) and the python scripts in [src/stream](./src/stream) to setup a stream prediction service with `Google Cloud Function`, `MLFlow` and `PubSub`.

## Environment

```bash
pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## IMPORTANT

Don't forget to **STOP** the `Cloud Services` after you are done, especially the `SQL Instance`. You can always start them again when you need them.