# 01. Setup The Local MLOps Stack

This guide sets up the local infrastructure used by the rest of the repository. The goal is to run the same model lifecycle on your machine without relying on external cloud services.

## What You Will Start

- `Postgres` for MLflow and Prefect metadata
- `MLflow` for experiment tracking and model registration
- `Prefect` for batch orchestration
- `FastAPI` for online predictions

## Architecture

```mermaid
flowchart TD
    A["Local Python environment"] --> B["Training notebook"]
    B --> C["MLflow server"]
    C --> D["Prefect batch flow"]
    C --> E["FastAPI prediction service"]
    D --> F["Parquet prediction files"]
    E --> G["JSON response"]
    H["Postgres"] --> C
    H --> D
```

## Prerequisites

- Python `3.11.3`
- Docker Desktop or another Docker-compatible runtime
- enough disk space to pull the Docker images used by the local stack

## Create The Environment

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

After copying `.env.example` to `.env`, keep the default local URLs unless you intentionally change the local stack ports.

## Check The Environment Before Docker

Run this command from the project root:

```bash
python --version
python -c "import fastapi, mlflow, prefect; print('Core imports look good.')"
```

You should see the active Python version and a short success message confirming that `FastAPI`, `MLflow`, and `Prefect` all import correctly.

## Start The Services

```bash
mkdir -p storage/mlartifacts data/predictions
docker compose -f infra/compose.yml up -d
```

The first boot can take a minute because the `mlflow` and `prefect` containers install their runtime dependencies inside the container before starting the service process.

When the stack is running, you should have:

- MLflow at `http://127.0.0.1:5001`
- Prefect at `http://127.0.0.1:4200`
- Postgres at `localhost:5432`

If `docker compose -f infra/compose.yml up -d` fails immediately, check that Docker Desktop is running before trying again.
If the services start slowly, watch the boot process with:

```bash
docker compose -f infra/compose.yml logs -f postgres mlflow prefect
```

## Confirm The Services

Use these checks before moving on to the notebooks:

```bash
curl http://127.0.0.1:5001
curl http://127.0.0.1:4200/api/health
```

You should also see the running containers with:

```bash
docker compose -f infra/compose.yml ps
```

## Sanity Check

Run these commands from the project root:

```bash
python -m src.training.train
python -m src.batch.flow
```

If both commands complete, the environment is ready for the notebooks. The batch command should create a parquet file under `data/predictions/`.

## What Each Service Does

- `Postgres` stores MLflow and Prefect metadata.
- `MLflow` tracks training runs and stores registered model versions.
- `Prefect` orchestrates the batch workflow and provides a UI for runs and deployments.
- `FastAPI` is not started during setup, but the later lesson uses the same registered model for online inference.

## Why This Setup Matters

This stack keeps the learning focus on model lifecycle concepts:

- training and tracking;
- registered models;
- repeatable batch scoring;
- lightweight online inference.

The next notebook uses the running MLflow server to train and register the first model version.

## Cleanup

When you are done for the day, stop the local services but keep the database volume and generated files:

```bash
docker compose -f infra/compose.yml down
```

To fully reset the local state before rerunning the lessons from scratch:

```bash
docker compose -f infra/compose.yml down -v
rm -rf data/predictions storage/mlartifacts .env
mkdir -p data
touch data/.gitkeep
```

This removes local MLflow artifacts, registered model metadata, Prefect run history, batch output files, and your copied `.env`.
