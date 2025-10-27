# Batch and Stream Predictions

In this repository you will get a short introduction into `MLflow` and how to use it for experiment and model tracking. You will deploy your own MLflow server on GCP and use the model registry to deploy a model as a batch and stream prediction service.

We first will train a simple model on the `Green Taxi Trip Records` dataset from the [NYC Taxi and Limousine Commission](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page). The experiments will be tracked with `MLflow` and the best model will be registered in the model registry. This step is normally done by a data scientist.

The batch prediction service will be orchestrated with `Prefect` and will upload the raw data and predictions to a GCS bucket. The stream prediction service will be deployed as a `Google Cloud Function`.

In the end you will have a fully functional MLflow server and an understanding of how to build batch and streaming prediction services.

## Setup

### Google Cloud SDK
You need the Google Cloud SDK installed and configured. If you don't have it installed follow the instructions [here](https://cloud.google.com/sdk/docs/install) or use:

#### **`macOS`**
```bash
brew install --cask google-cloud-sdk
```

#### **`WindowsOS`**
```PowerShell
choco install googlecloudsdk -y
```

### MLflow Server

Follow the steps in [01-setup-mlflow-server](./01-setup-mlflow-server.md) to setup your own MLflow server on GCP.

### Train the Model

Follow the steps in [02-train-ml-model](./02-train-ml-model.ipynb) to train a simple model on the `Green Taxi Trip Records` dataset from the [NYC Taxi and Limousine Commission](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page) and learn how to track the experiments with `MLflow`.

### Batch Prediction Service

Follow the steps in [03-batch-deployment](./03-batch-deployment.ipynb) and the python scripts in [src/batch](./src/batch) to setup a batch prediction service with `Prefect` and `MLflow`.

### Stream Prediction Service

Follow the steps in [04-OPTIONAL-stream-deployment](./04-OPTIONAL-stream-deployment.md) and the python scripts in [src/stream](./src/stream) to setup a stream prediction service with `Google Cloud Function`, `MLflow` and `PubSub`.


## Environment

Please make sure you have forked the repo and set up a new virtual environment. For this purpose you can use the following commands:

### **`macOS`**
```BASH
  pyenv local 3.11.3
  python -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```
### **`WindowsOS`**
 For `PowerShell` CLI :

  ```PowerShell
  pyenv local 3.11.3
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

  For `Git-Bash` CLI :

  ```
  pyenv local 3.11.3
  python -m venv .venv
  source .venv/Scripts/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

# IMPORTANT

Don't forget to **STOP** the `Cloud Services` after you are done, especially the `SQL Instance`. You can always start them again when you need them.
