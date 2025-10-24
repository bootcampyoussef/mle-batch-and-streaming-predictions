import json
import os
import base64
import mlflow
import functions_framework
from google.cloud import pubsub_v1


def transform_input(event):
    """Decode Pub/Sub message from CloudEvent and prepare model input."""
    print("📥 Received event:", event)

    try:
        pubsub_message = event.data["message"]
        encoded_data = pubsub_message["data"]
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        data = json.loads(decoded_data)

        ride_id = data["ride_id"]
        pick_up_location = data["PULocationID"]
        dropoff_location = data["DOLocationID"]
        trip_distance = data["trip_distance"]

        message_id = pubsub_message["message_id"]
        publish_time = pubsub_message["publish_time"]

        metadata = {
            "ride_id": ride_id,
            "message_id": message_id,
            "publish_time": publish_time,
            "PULocationID": pick_up_location,
            "DOLocationID": dropoff_location,
            "trip_distance": trip_distance,
        }

        prediction_input = {
            "trip_route": f"{pick_up_location}_{dropoff_location}",
            "trip_distance": trip_distance,
        }

        print("✅ Prepared prediction input:", prediction_input)
        return prediction_input, metadata

    except Exception as e:
        raise ValueError(f"❌ Error parsing Pub/Sub message: {e}")


def load_model(gs_path_artifact):
    """Load MLflow model from GCS path."""
    print(f"📦 Loading model from: {gs_path_artifact}")
    loaded_model = mlflow.pyfunc.load_model(gs_path_artifact)
    return loaded_model


def apply_model(model, prediction_input):
    """Apply model to input data."""
    prediction = model.predict(prediction_input)
    return prediction


@functions_framework.cloud_event
def predict_duration(cloudevent):
    """Main entry point — triggered by Pub/Sub CloudEvent."""
    # --- Environment variables ---
    GC_PATH_MODEL_ARTIFACT = os.environ.get("GC_PATH_MODEL_ARTIFACT")
    PROJECT_ID = os.environ.get("GCP_PROJECT")# or os.environ.get("GOOGLE_CLOUD_PROJECT")
    topic_name = os.environ["RESULT_TOPIC"]

    print(f"🧭 Detected PROJECT_ID: {PROJECT_ID}")
    print(f"🧠 Model Artifact Path: {GC_PATH_MODEL_ARTIFACT}")
    print(f"📤 Output Topic: {topic_name}")

    publisher = pubsub_v1.PublisherClient()

    # --- Step 1: Parse input ---
    print("➡️ Loading data...")
    prediction_input, metadata = transform_input(cloudevent)

    # --- Step 2: Load model ---
    print("➡️ Loading model...")
    model = load_model(GC_PATH_MODEL_ARTIFACT)

    # --- Step 3: Make prediction ---
    print("➡️ Making prediction...")
    prediction = apply_model(model, prediction_input)

    # --- Step 4: Publish result ---
    message = {
        "ride_id": metadata['ride_id'],
        "message_id": metadata['message_id'],
        "publish_time": metadata['publish_time'],
        "pick_up_location": metadata["PULocationID"],
        "dropoff_location": metadata["DOLocationID"],
        "trip_distance": metadata["trip_distance"],
        "prediction": float(prediction[0])
        }

    print("📤 Publishing prediction message:")
    print(json.dumps(message, indent=2))

    message_data = json.dumps(message).encode("utf-8")
    topic_path = publisher.topic_path(PROJECT_ID, topic_name)
    future = publisher.publish(topic_path, data=message_data)
    message_id = future.result()

    print(f"✅ Prediction published to {topic_path} (message_id={message_id})")

    return "OK", 200
