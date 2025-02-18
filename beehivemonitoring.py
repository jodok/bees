import json
import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Apiary, Hive, History, ATTRIBUTES


load_dotenv()

BASE_URL = "https://main.beehivemonitoring.com"
HEADERS = {"X-Auth-Token": os.getenv("BEEHIVE_API_TOKEN")}
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://localhost/bees")

APIARIES = os.getenv("APIARIES")
APIARIES = json.loads(APIARIES)


def main(argv):
    # Create SQLAlchemy engine for PostgreSQL
    engine = create_engine(DB_CONNECTION)

    # Create tables
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    for apiary in APIARIES:
        apiary_id = apiary["id"]
        apiary_name = apiary["name"]
        apiary = Apiary(id=apiary_id, name=apiary_name)
        try:
            session.merge(apiary)
            session.commit()
        except Exception as e:
            print(f"Error upserting apiary: {e}")
            session.rollback()

    hives = {}
    hives_response = requests.get(f"{BASE_URL}/api/hives", headers=HEADERS)
    for hive in hives_response.json():
        hive_id = hive["id"]
        hive_name = hive["name"]
        apiary_id = next(
            apiary["id"] for apiary in APIARIES if hive_id in apiary["hives"]
        )
        hives[hive_id] = {"name": hive_name, "raw": hive, "history": {}}
        hive = Hive(id=hive_id, name=hive_name, apiary_id=apiary_id)
        try:
            session.merge(hive)
            session.commit()
        except Exception as e:
            print(f"Error upserting hive: {e}")
            session.rollback()

        # determine how many records to fetch
        latest = (
            session.query(History.time)
            .filter(History.hive_id == hive_id)
            .order_by(History.time.desc())
            .first()
        )
        latest_ts = int(latest[0].timestamp()) if latest else 0
        current_ts = int(datetime.now(timezone.utc).timestamp())
        limit = max(int((current_ts - latest_ts) / 86.4), 100)  # 1000 records per day

        history_response = requests.get(
            f"{BASE_URL}/api/hives/{hive_id}/history?limit={limit}&reverse=true&attributes={ATTRIBUTES}",
            headers=HEADERS,
        )
        ts = {}
        for m in history_response.json():
            t = m.pop("time")
            dt = datetime.fromtimestamp(t / 1000, tz=timezone.utc)
            reading = History(hive_id=hive_id, time=dt, **{k: v for k, v in m.items()})
            try:
                session.merge(reading)
                session.commit()
            except Exception as e:
                print(f"Error upserting reading: {e}")
                session.rollback()

    session.close()


if __name__ == "__main__":
    main(sys.argv[1:])
