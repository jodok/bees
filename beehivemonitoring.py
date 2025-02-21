import sys
import requests
from datetime import datetime, timezone
from settings import BASE_URL, HEADERS, APIARIES, HIVES, SENSORS, ATTRIBUTES
from models import Apiary, Hive, Sensor, History
from database import init_db, get_session, close_session


def upsert_defaults(session):
    """Update or insert default data from configuration."""
    try:
        for apiary in APIARIES:
            session.merge(Apiary(id=apiary["id"], name=apiary["name"]))
        for hive in HIVES:
            session.merge(
                Hive(id=hive["id"], name=hive["name"], apiary_id=hive["apiary_id"])
            )
        for sensor in SENSORS:
            session.merge(
                Sensor(
                    id=sensor["id"],
                    name=sensor["name"],
                    modules=sensor["modules"],
                    hive_id=sensor["hive_id"],
                )
            )
        session.commit()
    except Exception as e:
        print(f"Error upserting defaults: {e}")
        session.rollback()


def get_sensor_list():
    """Fetch list of sensors from the API."""
    response = requests.get(f"{BASE_URL}/api/hives", headers=HEADERS)
    return response.json()


def get_apiary_id_for_hive(hive_id):
    """Find the apiary ID for a given hive."""
    return next(apiary["id"] for apiary in APIARIES if hive_id in apiary["hives"])


def upsert_sensor(session, sensor_id, sensor_data):
    """Update or insert a sensor and return its data."""
    sensor = session.get(Sensor, sensor_id)
    if sensor:
        sensor.name = sensor_data["name"]
        sensor.raw = sensor_data
    else:
        sensor = Sensor(id=sensor_id, name=sensor_data["name"], raw=sensor_data)
    try:
        session.merge(sensor)
        session.commit()
    except Exception as e:
        print(f"Error upserting sensor: {e}")
        session.rollback()


def get_history_limit(session, sensor_id):
    """Calculate how many history records to fetch."""
    latest = (
        session.query(History.time)
        .filter(History.sensor_id == sensor_id)
        .order_by(History.time.desc())
        .first()
    )
    latest_ts = int(latest[0].timestamp()) if latest else 0
    current_ts = int(datetime.now(timezone.utc).timestamp())
    return max(int((current_ts - latest_ts) / 86.4), 100)  # 1000 records per day


def fetch_sensor_history(sensor_id, limit):
    """Fetch history data for a sensor from the API."""
    response = requests.get(
        f"{BASE_URL}/api/hives/{sensor_id}/history?limit={limit}&reverse=true&attributes={ATTRIBUTES}",
        headers=HEADERS,
    )
    return response.json()


def upsert_history_readings(session, readings):
    """Update or insert multiple history readings in a batch."""
    try:
        for reading in readings:
            session.merge(reading)
        session.commit()
    except Exception as e:
        print(f"Error upserting readings batch: {e}")
        session.rollback()


def main(argv):
    # Initialize database
    init_db()
    session = get_session()

    try:
        # Set defaults
        upsert_defaults(session)

        for sensor_data in get_sensor_list():
            sensor_id = sensor_data["id"]
            upsert_sensor(session, sensor_id, sensor_data)

            # Fetch and process history
            limit = get_history_limit(session, sensor_id)
            history_data = fetch_sensor_history(sensor_id, limit)

            # Prepare batch of readings
            readings = []
            for measurement in history_data:
                time = measurement.pop("time")
                reading = History(
                    sensor_id=sensor_id,
                    time=datetime.fromtimestamp(time / 1000, tz=timezone.utc),
                    **{k: v for k, v in measurement.items()},
                )
                readings.append(reading)

            upsert_history_readings(session, readings)

    finally:
        close_session()


if __name__ == "__main__":
    main(sys.argv[1:])
