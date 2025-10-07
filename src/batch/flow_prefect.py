import os
import uuid
import pandas as pd
import mlflow
from datetime import date
from prefect import task, flow, get_run_logger
from prefect.context import get_run_context


# --------------------------------------------------------------------
# Utility functions
# --------------------------------------------------------------------

def generate_uuids(n: int) -> list[str]:
    """Generate n unique UUID strings for ride IDs."""
    ride_ids = []
    for i in range(n):
        ride_ids.append(str(uuid.uuid4()))
    return ride_ids


def read_dataframe(file_path_input: str) -> pd.DataFrame:
    """
    Read the input parquet file and filter the data.

    Filters out trips shorter than 1 minute or longer than 60 minutes
    and adds a unique ride ID column.
    """
    df = pd.read_parquet(file_path_input)
    df['trip_duration_minutes'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.trip_duration_minutes = df.trip_duration_minutes.dt.total_seconds() / 60
    
    df = df[(df.trip_duration_minutes >= 1) & (df.trip_duration_minutes <= 60)]
    df['ride_id'] = generate_uuids(len(df))

    return df


def preprocess(df: pd.DataFrame) -> list[dict]:
    """
    Prepare data for model prediction.

    Converts categorical features to strings and builds the
    'trip_route' feature combining pickup and dropoff locations.
    """
    df = df.copy()
    categorical_features = ["PULocationID", "DOLocationID"]
    df[categorical_features] = df[categorical_features].astype(str)
    
    df['trip_route'] = df["PULocationID"] + "_" + df["DOLocationID"]
    dicts = df[['trip_route', 'trip_distance']].to_dict(orient='records')
    print(f"First 5 preprocessed records: {dicts[:5]}")
    return dicts
    


# Load the model from MLflow
def load_model(mlflow_tracking_uri: str, run_id: str,  model_name: str='mlflow-model-v1'):
    """
    Load a model from MLflow by run ID and model name.
    """
    # Set the MLflow tracking URI
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    logged_model_name = f'runs:/{run_id}/{model_name}'
    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model_name)
    return loaded_model


# Save the prediction results to a parquet file
def save_results(df: pd.DataFrame, y_pred, run_id: str, model_name: str, file_path_predictions: str):
    """
    Save the prediction results to a Parquet file, including
    actual vs. predicted durations and model metadata.
    """
    df_result = pd.DataFrame()
    df_result['ride_id'] = df['ride_id']
    df_result['lpep_pickup_datetime'] = df['lpep_pickup_datetime']
    df_result['PULocationID'] = df['PULocationID']
    df_result['DOLocationID'] = df['DOLocationID']
    df_result['actual_duration'] = df['trip_duration_minutes']
    df_result['predicted_duration'] = y_pred
    df_result['diff'] = df_result['actual_duration'] - df_result['predicted_duration']
    df_result['model_version'] = run_id
    df_result['model_name'] = model_name
    df_result.to_parquet(file_path_predictions, index=False)

# --------------------------------------------------------------------
# Prefect tasks and flow
# --------------------------------------------------------------------

@task(name="apply_model_task")
def apply_model(file_path_input: str, 
                mlflow_tracking_uri: str, 
                run_id: str, 
                model_name: str, 
                file_path_predictions: str):
    """
    Task to apply the MLflow model and save predictions to GCS.
    """
    logger = get_run_logger()
    logger.info(f"Reading data from {file_path_input}")
    df = read_dataframe(file_path_input)
    logger.info(f"Preprocessing {df} rows")
    
    dicts = preprocess(df)
    
    logger.info(f"Loading the model {run_id}")
    loaded_model = load_model(mlflow_tracking_uri, run_id, model_name)
    logger.info(f"Model flavor: {loaded_model.metadata.flavors}")
    logger.info(f"{type(loaded_model._model_impl.sklearn_model)}")

    y_pred = loaded_model.predict(dicts)
    
    logger.info(f"Saving results to {file_path_predictions}")
    save_results(df, y_pred, run_id, model_name, file_path_predictions)
    

@flow(name="Predict Green Taxi Trip Duration")
def run(bucket_name: str,
        mlflow_tracking_uri: str, 
        run_id: str,
        model_name: str, 
        google_sa_key: str,
        data_reference_date: date
        ):
    """
    Predict green taxi trip durations for the previous month.

    This flow:
      1. Downloads the monthly public dataset for NYC green taxis.
      2. Applies a pre-trained MLflow model to estimate trip durations.
      3. Saves raw and predicted data to Google Cloud Storage.

    Parameters
    ----------
    bucket_name : str
        The name of the Google Cloud Storage bucket to save outputs.
    mlflow_tracking_uri : str
        The MLflow tracking URI where the model artifacts are stored.
    run_id : str
        The MLflow run ID of the pre-trained model to use.
    model_name : str
        The name of the registered model in MLflow.
    google_sa_key : str
        Path to the Google Service Account key JSON for GCS authentication.
    data_reference_date : date
        Reference date used to determine which month of data to process. 
        The flow processes the previous month.
    """
    
    logger = get_run_logger()
    logger.info(
        f"Running with parameters: bucket_name={bucket_name}, run_id={run_id}, google_sa_key={google_sa_key}"
    )
    path = os.path.dirname(__file__)
    logger.info(f"Current path: {path}")
    
    # Use the provided data_reference_date
    reference_date = data_reference_date

    # Compute previous month
    # Those defines the year and month we want to process
    year = reference_date.year
    month = reference_date.month - 1
    if month == 0:
        month = 12
        year -= 1
    
    logger.info(f"Processing data for {year}-{month:02d}")
    
    # Set the environment variable for Google Application Credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_sa_key
    
    # Read the data for the previous month from the public URL
    df_input = pd.read_parquet(f"https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet")
    logger.info(f"Read {len(df_input)} rows.")
    
    # Save raw data to the bucket
    raw_path = f"gs://{bucket_name}/raw/green_tripdata_{year}-{month:02d}.parquet"
    df_input.to_parquet(raw_path)
    logger.info(f"Raw data saved to {raw_path}")

    
    # Define input and output filenames in GCS
    file_path_input = raw_path
    file_path_prediction = f"gs://{bucket_name}/predictions/green_tripdata_{year}-{month:02d}.parquet"
    
    mlflow_tracking_uri = mlflow_tracking_uri
    run_id = run_id
    model_name = model_name

    # Run model inference task
    apply_model(file_path_input,
                mlflow_tracking_uri,
                run_id,
                model_name,
                file_path_prediction,
                )
    
    

