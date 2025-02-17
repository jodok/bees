import json
import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()

BASE_URL = "https://main.beehivemonitoring.com"
ATTRIBUTES = "weight;pressure;pressureGw;pressureEnv;inTotal;outTotal;magX;magY;magZ;accX;accY;accZ;tempIn;tempOut;tempEnv;humidityIn;humidityOut;humidityEnv;humiditySh1;humiditySh2;humiditySh3;frequency;amplitude;vbatIn;vbatOut;vbatEnv;vbatGw;vbatMap;rssiIn;rssiOut;rssiEnv;rssiGw;rssiMap;co2;tvoc;co;o2;o3;so;no;so2;pm25;pm10"
HEADERS = {"X-Auth-Token": os.getenv("BEEHIVE_API_TOKEN")}
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://localhost/bees")

APIARIES = os.getenv("APIARIES")
APIARIES = json.loads(APIARIES)


def main(argv):
    # Create SQLAlchemy engine for PostgreSQL
    engine = create_engine(DB_CONNECTION)
    Base = declarative_base()

    class Apiary(Base):
        __tablename__ = "apiary"

        id = Column(Integer, primary_key=True)
        name = Column(String)
        created_at = Column(DateTime, default=datetime.now(timezone.utc))
        updated_at = Column(
            DateTime,
            default=datetime.now(timezone.utc),
            onupdate=datetime.now(timezone.utc),
        )

    class Hive(Base):
        __tablename__ = "hive"

        id = Column(Integer, primary_key=True)
        name = Column(String)
        apiary_id = Column(Integer, ForeignKey("apiary.id"))
        created_at = Column(DateTime, default=datetime.now(timezone.utc))
        updated_at = Column(
            DateTime,
            default=datetime.now(timezone.utc),
            onupdate=datetime.now(timezone.utc),
        )

    class History(Base):
        __tablename__ = "history"

        hive_id = Column(Integer, ForeignKey("hive.id"), primary_key=True)
        time = Column(DateTime, primary_key=True)
        # Dynamically create columns from ATTRIBUTES
        for attr in ATTRIBUTES.split(";"):
            locals()[attr] = Column(Float)
        created_at = Column(DateTime, default=datetime.now(timezone.utc))
        updated_at = Column(
            DateTime,
            default=datetime.now(timezone.utc),
            onupdate=datetime.now(timezone.utc),
        )

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
