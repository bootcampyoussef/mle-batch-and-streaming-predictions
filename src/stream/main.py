import json
import os
import base64
import mlflow

import functions_framework
from google.cloud import pubsub_v1


def transfrom_input(event):
    # Extract the message body, expected to be a JSON representation of a
    # dictionary, and extract the fields from that dictionary.
    print('Recieved event:', event)
    pubsub_message = event.data["message"]
    try:
        encoded_data = pubsub_message["data"]
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        data = json.loads(decoded_data)
        ride_id = data["ride_id"]
        pick_up_location = data["PULocationID"]
        dropoff_up_location = data["DOLocationID"]
        trip_distance = data["trip_distance"]

        message_id = pubsub_message["message_id"]
        publish_time = pubsub_message["publish_time"]
        
        metadata = {
            "ride_id": ride_id,
            "message_id": message_id,
            "publish_time": publish_time,
            "PULocationID":pick_up_location,
            "DOLocationID":dropoff_up_location,
            "trip_distance":trip_distance
        }


        prediction_input = {
            'trip_route': f"{pick_up_location}_{dropoff_up_location}",
            'trip_distance': trip_distance
        }
        print('prediction_input:', prediction_input)
        return prediction_input, metadata
    except Exception as e:
        raise ValueError(f"Missing or malformed PubSub message.{event}. {e}")
 

def load_model(run_id):
    logged_model = f'gs://neuefische-mlflow-artifacts/1/{run_id}/artifacts/model'
    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model)
    return loaded_model


def apply_model(model, prediction_input):
    # Apply model to prediction input.
    prediction = model.predict(prediction_input)
    return prediction


@functions_framework.cloud_event
def predict_duration(cloudevent):
    # Get environment variables
    RUN_ID = os.environ.get("RUN_ID")
    PROJECT_ID = os.environ.get("GCP_PROJECT")
    topic_name = os.environ["RESULT_TOPIC"]
    publisher = pubsub_v1.PublisherClient()
    
    # get data from cloudevent
    print('Loading data...')
    prediction_input, metadata = transfrom_input(cloudevent)
    # Load model
    print('Loading model...')
    model = load_model(RUN_ID)
    # make prediction
    print('Making prediction...')
    prediction = apply_model(model, prediction_input)
    # publish prediction
    message = {
        "ride_id": metadata['ride_id'],
        "message_id":metadata['message_id'],
        "publish_time": metadata['publish_time'],
        "pick_up_location": metadata["PULocationID"],
        "dropoff_up_location": metadata["DOLocationID"],
        "trip_distance": metadata["trip_distance"],
        "prediction": prediction[0]
    }
    
    print('Publishing prediction...')
    print(message)
    
    message_data = json.dumps(message).encode('utf-8')
    topic_path = publisher.topic_path(PROJECT_ID, topic_name)
    future = publisher.publish(topic_path, data=message_data)
    future.result()
    return  200, {"status": "success"}


