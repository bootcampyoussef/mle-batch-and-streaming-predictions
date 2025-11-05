import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from flow_prefect import run
from prefect.client.schemas.schedules import RRuleSchedule, CronSchedule 


# Load environment variables from a .env file
load_dotenv()

# Create a schedule that runs every 2 months on the same day and time as now + 2 minutes
# This is to give you time to start the prefect server and run this script
now = datetime.now(timezone.utc) + timedelta(minutes=2)
rrule_string = (
    f"DTSTART:{now.strftime('%Y%m%dT%H%M%SZ')}\n"
    f"FREQ=MONTHLY;INTERVAL=2;BYMONTHDAY={now.day};BYHOUR={now.hour};BYMINUTE={now.minute}"
)


schedule_rule = RRuleSchedule(rrule=rrule_string)

if __name__ == "__main__":
    # Start the flow with a schedule
    run.serve(
        name="ride_duration_prediction",
        schedules=[
            schedule_rule,
            ],
        parameters={
            "bucket_name": os.getenv("BUCKET_NAME"),
            "mlflow_tracking_uri": os.getenv("MLFLOW_TRACKING_URI"),
            "run_id": os.getenv("RUN_ID"),
            "model_name": os.getenv("MODEL_NAME"),
            "google_sa_key": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            "data_reference_date": os.getenv("DATA_REFERENCE_DATE"),
        },
        tags=["batch", "predict", "prefect"],
    )


