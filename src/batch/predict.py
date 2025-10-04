import os
import uuid
import pandas as pd
import click
import mlflow


# Generate UUIDs for ride IDs
def generate_uuids(n):
    ride_ids = []
    for i in range(n):
        ride_ids.append(str(uuid.uuid4()))
    return ride_ids

# Read the input parquet file and filter the data
def read_dataframe(file_path_input: str):
    df = pd.read_parquet(file_path_input)

    df['trip_duration_minutes'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.trip_duration_minutes = df.trip_duration_minutes.dt.total_seconds() / 60
    df = df[(df.trip_duration_minutes >= 1) & (df.trip_duration_minutes <= 60)]
    
    df['ride_id'] = generate_uuids(len(df))

    return df


# Preprocess the data for prediction
def preprocess(df):
    df = df.copy()
    categorical_features = ["PULocationID", "DOLocationID"]
    df[categorical_features] = df[categorical_features].astype(str)
    
    df['trip_route'] = df["PULocationID"] + "_" + df["DOLocationID"]
    dicts = df[['trip_route', 'trip_distance']].to_dict(orient='records')
    
    return dicts

# Load the model from MLflow
def load_model(mlflow_tracking_uri, run_id,  model_name='mlflow-model-v1',):
    # Set the MLflow tracking URI
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    logged_model_name = f'runs:/{run_id}/{model_name}'
    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model_name)
    return loaded_model

# Save the prediction results to a parquet file
def save_results(df, y_pred, run_id, model_name, file_path_predictions):
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


# Main function to apply the model and save predictions
def apply_model(file_path_input, mlflow_tracking_uri, run_id, model_name, file_path_predictions):
    df = read_dataframe(file_path_input)
    dicts = preprocess(df)
    
    loaded_model = load_model(mlflow_tracking_uri, run_id, model_name)
    y_pred = loaded_model.predict(dicts)
    
    save_results(df, y_pred, run_id, model_name, file_path_predictions)

# Command-line interface using Click 
@click.command()
@click.option("--file_path_input", help="Path to the input parquet file")
@click.option("--mlflow_tracking_uri", help="MLflow tracking URI")
@click.option("--run_id", help="MLflow run ID")
@click.option("--model_name", help="MLflow model name")
@click.option("--file_path_predictions", help="Path to the output parquet file")
@click.option("--google_sa_key", help="Path to the Google Service Account Key JSON file")
def run(file_path_input, mlflow_tracking_uri, run_id, model_name, file_path_predictions, google_sa_key):
    file_path_input = file_path_input
    file_path_predictions = file_path_predictions
    run_id = run_id
    model_name = model_name
    # Set the environment variable for Google Application Credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_sa_key
    apply_model(file_path_input,
                mlflow_tracking_uri,
                run_id,
                model_name,
                file_path_predictions)
    
    

if __name__ == "__main__":
    # this will be invoked when we run `python src/batch/predict.py ...` as a script. 
    # in case of `import src.batch.predict` this will not be invoked.
    run()