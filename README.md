# Batch And Stream Predictions

In this repository, you will explore a local-first MLOps workflow using [MLflow](https://mlflow.org/), [Prefect](https://docs.prefect.io/), and [FastAPI](https://fastapi.tiangolo.com/).
You will train a regression model on the NYC Green Taxi dataset, register it in MLflow, orchestrate a batch prediction workflow with Prefect, and expose the same model through a lightweight online inference API.

## Repository Workflow

```mermaid
flowchart LR
    A["Create Python 3.11.3 environment"] --> B["Start local Postgres, MLflow, and Prefect"]
    B --> C["Train and register a model in MLflow"]
    C --> D["Run batch scoring with Prefect"]
    C --> E["Serve online predictions with FastAPI"]
```

## Learning Path

Work through the material in this order:

1. [01 - Setup the local stack](01-setup-local-stack.md): Set up the local Docker-backed services, create the Python environment, and confirm that MLflow, Prefect, and Postgres are ready for the lessons.
2. [02 - Train and register the model](02-train-ml-model.ipynb): Prepare taxi features, train a baseline regression pipeline, compare it to a simple baseline, and register the model in MLflow.
3. [03 - Batch predictions with Prefect](03-batch-deployment.ipynb): Run a batch scoring workflow with Prefect, inspect the prediction output, and understand how the registered MLflow model is reused for scheduled inference.
4. [04 - Online inference with FastAPI](04-online-inference-with-fastapi.ipynb): Send online prediction requests through FastAPI and compare how the API responds to different trip inputs.
5. [05 - Optional local extension exercise](05-OPTIONAL-local-extension-exercise.md): Extend the local workflow by comparing a second model or updating the active prediction target in MLflow.

## Local Data Services

This repository includes a Docker-based local stack for `Postgres`, `MLflow`, and `Prefect`. You will run `docker compose -f infra/compose.yml up -d` from the project root to start the local services used throughout the lessons.

When the stack is running, the local endpoints are:

- `Postgres`: `localhost:5432`
- `MLflow`: `http://127.0.0.1:5001`
- `Prefect`: `http://127.0.0.1:4200`

## Mermaid Diagrams

This repository contains Mermaid diagrams. If you want them to render in VS Code, we recommend installing the `Markdown Preview Mermaid Support` extension:

- [Install in VS Code](vscode:extension/bierner.markdown-mermaid)
- [View on Marketplace](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid)

## Environment

Please make sure you **use this repository as a template** and set up a new virtual environment.

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows

For `PowerShell` CLI:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For `Git-Bash` CLI:

```bash
py -3 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Then copy the default local environment file:

```bash
cp .env.example .env
```

For PowerShell, use:

```powershell
Copy-Item .env.example .env
```

The [requirements.txt](requirements.txt) file contains the libraries and dependencies needed to run the examples and lesson workflows in this repository. After copying `.env.example` to `.env`, keep the default local URLs unless you intentionally change the local stack ports.

The most important environment variables are:

- `MLFLOW_TRACKING_URI`: MLflow server URL used by training, batch, and API code
- `PREFECT_API_URL`: local Prefect API URL
- `MLFLOW_MODEL_NAME`: registered model name that batch and online inference will resolve by default
- `BATCH_INPUT_URI`: parquet file scored in the batch chapter

## Setup

You will need **Docker Desktop** installed and running on your machine. If you do not have it installed, please follow the [installation instructions](https://docs.docker.com/get-docker/).

Use this sequence when you first walk through the repo:

### 1. Confirm The Python Environment

```bash
python --version
python -c "import fastapi, mlflow, prefect; print('Core imports look good.')"
```

### 2. Start The Local Services

```bash
mkdir -p storage/mlartifacts data/predictions
docker compose -f infra/compose.yml up -d
```

The first boot can take a minute because the `mlflow` and `prefect` containers install a few Python dependencies before starting.

If you want to watch that startup in real time:

```bash
docker compose -f infra/compose.yml logs -f postgres mlflow prefect
```

### 3. Confirm The Services Are Reachable

```bash
docker compose -f infra/compose.yml ps
curl http://127.0.0.1:5001
curl http://127.0.0.1:4200/api/health
```

### 4. Run The Training And Batch Steps

```bash
python -m src.training.train
python -m src.batch.flow
```

After `python -m src.batch.flow`, you should see a new parquet file in `data/predictions/`.

### 5. Start And Test The API

```bash
python -m uvicorn src.serve.api:app --reload
```

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"PULocationID": 1, "DOLocationID": 2, "trip_distance": 3.5}'
```

## Cleanup

When you are done for the day, stop the local services but keep the Postgres volume and generated files:

```bash
docker compose -f infra/compose.yml down
```

To fully reset the repo to a clean local state, remove Docker volumes and generated lesson outputs:

```bash
docker compose -f infra/compose.yml down -v
rm -rf data/predictions storage/mlartifacts .env
mkdir -p data
touch data/.gitkeep
```

The reset command removes local MLflow runs, registered model metadata, batch prediction parquet files, and your copied `.env`. Run the setup steps again before restarting the lessons.

## Learning Objectives

By the end of this repository, you should be able to:

- Explain how a local-first MLOps workflow connects model training, registration, batch scoring, and online inference.
- Prepare taxi trip features and train a baseline regression pipeline for trip-duration prediction.
- Track experiments and register reusable model versions with MLflow.
- Run a local Prefect-backed batch workflow that scores a parquet dataset and saves the prediction output.
- Understand how scheduled Prefect runs reuse the latest registered MLflow model.
- Serve the registered model through a FastAPI prediction endpoint and compare outputs for different request scenarios.
- Extend the project by testing a stronger model and updating the active prediction target in MLflow.
