import sys
import requests
from datetime import datetime, timezone
from settings import BASE_URL, HEADERS, APIARIES, ATTRIBUTES
from models import Apiary, Hive, History
from database import init_db, get_session, close_session


def upsert_apiaries(session):
    """Update or insert apiaries from configuration."""
    for apiary in APIARIES:
        apiary_obj = Apiary(id=apiary["id"], name=apiary["name"])
        try:
            session.merge(apiary_obj)
            session.commit()
        except Exception as e:
            print(f"Error upserting apiary: {e}")
            session.rollback()


def get_hive_list():
    """Fetch list of hives from the API."""
    response = requests.get(f"{BASE_URL}/api/hives", headers=HEADERS)
    return response.json()


def get_apiary_id_for_hive(hive_id):
    """Find the apiary ID for a given hive."""
    return next(apiary["id"] for apiary in APIARIES if hive_id in apiary["hives"])


def upsert_hive(session, hive_data):
    """Update or insert a hive and return its data."""
    hive_id = hive_data["id"]
    hive_name = hive_data["name"]
    apiary_id = get_apiary_id_for_hive(hive_id)

    hive = Hive(id=hive_id, name=hive_name, apiary_id=apiary_id)
    try:
        session.merge(hive)
        session.commit()
    except Exception as e:
        print(f"Error upserting hive: {e}")
        session.rollback()

    return {"name": hive_name, "raw": hive_data, "history": {}}


def get_history_limit(session, hive_id):
    """Calculate how many history records to fetch."""
    latest = (
        session.query(History.time)
        .filter(History.hive_id == hive_id)
        .order_by(History.time.desc())
        .first()
    )
    latest_ts = int(latest[0].timestamp()) if latest else 0
    current_ts = int(datetime.now(timezone.utc).timestamp())
    return max(int((current_ts - latest_ts) / 86.4), 100)  # 1000 records per day


def fetch_hive_history(hive_id, limit):
    """Fetch history data for a hive from the API."""
    response = requests.get(
        f"{BASE_URL}/api/hives/{hive_id}/history?limit={limit}&reverse=true&attributes={ATTRIBUTES}",
        headers=HEADERS,
    )
    return response.json()


def upsert_history_reading(session, hive_id, measurement):
    """Update or insert a history reading."""
    time = measurement.pop("time")
    dt = datetime.fromtimestamp(time / 1000, tz=timezone.utc)
    reading = History(
        hive_id=hive_id, time=dt, **{k: v for k, v in measurement.items()}
    )
    try:
        session.merge(reading)
        session.commit()
    except Exception as e:
        print(f"Error upserting reading: {e}")
        session.rollback()


def main(argv):
    # Initialize database
    init_db()
    session = get_session()

    try:
        # Update apiaries
        upsert_apiaries(session)

        # Process hives
        hives = {}
        for hive_data in get_hive_list():
            hive_id = hive_data["id"]
            hives[hive_id] = upsert_hive(session, hive_data)

            # Fetch and process history
            limit = get_history_limit(session, hive_id)
            history_data = fetch_hive_history(hive_id, limit)

            for measurement in history_data:
                upsert_history_reading(session, hive_id, measurement)

    finally:
        close_session()


if __name__ == "__main__":
    main(sys.argv[1:])
