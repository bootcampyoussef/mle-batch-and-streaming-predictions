import os
import uuid
import pandas as pd
from datetime import datetime
import mlflow
from prefect import task, flow, get_run_logger
from prefect.context import get_run_context

def generate_uuids(n):
    ride_ids = []
    for i in range(n):
        ride_ids.append(str(uuid.uuid4()))
    return ride_ids


def read_dataframe(filename: str):
    df = pd.read_parquet(filename)

    df['trip_duration_minutes'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.trip_duration_minutes = df.trip_duration_minutes.dt.total_seconds() / 60
    df = df[(df.trip_duration_minutes >= 1) & (df.trip_duration_minutes <= 60)]
    df['ride_id'] = generate_uuids(len(df))
    return df


def preprocess(df):
    df = df.copy()
    categorical_features = ["PULocationID", "DOLocationID"]
    df[categorical_features] = df[categorical_features].astype(str)
    
    df['trip_route'] = df["PULocationID"] + "_" + df["DOLocationID"]
    dicts = df[['trip_route', 'trip_distance']].to_dict(orient='records')
    return dicts


def load_model(run_id, MLFLOW_TRACKING_URI):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    logged_model = f'runs:/{run_id}/model'
    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model)
    return loaded_model


def save_results(df, y_pred, run_id, output_filename):
    df_result = pd.DataFrame()
    df_result['ride_id'] = df['ride_id']
    df_result['lpep_pickup_datetime'] = df['lpep_pickup_datetime']
    df_result['PULocationID'] = df['PULocationID']
    df_result['DOLocationID'] = df['DOLocationID']
    df_result['actual_duration'] = df['trip_duration_minutes']
    df_result['predicted_duration'] = y_pred
    df_result['diff'] = df_result['actual_duration'] - df_result['predicted_duration']
    df_result['model_version'] = run_id
    df_result.to_parquet(output_filename, index=False)


@task
def apply_model(filename, 
                run_id, 
                output_filename,
                MLFLOW_TRACKING_URI):
    logger = get_run_logger()
    logger.info(f"Reading data from {filename}")
    df = read_dataframe(filename)
    dicts = preprocess(df)
    
    logger.info(f"Loading the model {run_id}")
    loaded_model = load_model(run_id, MLFLOW_TRACKING_URI)
    y_pred = loaded_model.predict(dicts)
    
    logger.info(f"Saving results to {output_filename}")
    save_results(df, y_pred, run_id, output_filename)
    
    
@flow(name="Predict Green Taxi Trip Duration")
def run(bucket_name:str, 
        run_id:str, 
        google_sa_key:str,
        MLFLOW_TRACKING_URI,
        run_date:datetime = None):
    logger = get_run_logger()
    logger.info(f"Running with parameters: bucket_name={bucket_name}, run_id={run_id}, google_sa_key={google_sa_key}, run_date={run_date}")
    path = os.path.dirname(__file__)
    logger.info(f"Current path: {path}")
    if run_date is None:
        ctx = get_run_context()
        date = ctx.flow_run.expected_start_time
        month = date.month - 1
        
    year = 2021
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_sa_key
    df_input = pd.read_parquet(f"https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet")
    df_input.to_parquet(f"gs://{bucket_name}/raw/green_tripdata_{year}-{month:02d}.parquet")
    
    filename = f"gs://{bucket_name}/raw/green_tripdata_{year}-{month:02d}.parquet"
    output_filename = f"gs://{bucket_name}/predictions/green_tripdata_{year}-{month:02d}.parquet"
    run_id = run_id
    apply_model(filename,
                run_id,
                output_filename,
                MLFLOW_TRACKING_URI)
    
    

if __name__ == "__main__":
    run()