import requests
import time
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from beehivemonitoring import HiveHistory
from dotenv import load_dotenv
import os

load_dotenv()


BASE_URL = "https://api.beep.nl"
HEADERS = {"Authorization": f"Bearer {os.getenv('BEEP_API_TOKEN')}"}

HIVE_MAP = {
    30522: "ypx0zaf9wcfdsecm",  # Rossstall 001
    30523: "3sa5ug7nzyrphvrn",  # Rossstall 002
}

FREQUENCY_BANDS = {
    (0, 146): "s_bin098_146Hz",
    #    (98, 146): "s_bin098_146Hz",
    (146, 195): "s_bin146_195Hz",
    (195, 244): "s_bin195_244Hz",
    (244, 293): "s_bin244_293Hz",
    (293, 342): "s_bin293_342Hz",
    (342, 391): "s_bin342_391Hz",
    (391, 439): "s_bin391_439Hz",
    (439, 488): "s_bin439_488Hz",
    (488, 537): "s_bin488_537Hz",
    # (537, 586): "s_bin537_586Hz",
    (537, 999999): "s_bin537_586Hz",
}


def get_beep_hive_id(bhm_hive_id):
    return HIVE_MAP.get(bhm_hive_id)


def get_bhm_hive_id(beep_hive_id):
    for bhm_id, beep_id in HIVE_MAP.items():
        if beep_id == beep_hive_id:
            return bhm_id
    return None


# Create SQLAlchemy engine and session
engine = create_engine("postgresql://localhost/bees")
Session = sessionmaker(bind=engine)
session = Session()

bhm_id = 30522
measurements = []

# Scale
# Query measurements for hive 30522 where weight is not null
key = "ypx0zaf9wcfdsecm"
stmt = (
    select(HiveHistory)
    .where(HiveHistory.hive_id == bhm_id, HiveHistory.weight.isnot(None))
    .order_by(HiveHistory.time.desc())
)
results = session.execute(stmt).scalars().all()

for r in results:
    frequency_band = None
    for (lower, upper), band_name in FREQUENCY_BANDS.items():
        if r.frequency and lower <= r.frequency < upper:
            frequency_band = band_name
            break

    data = {
        "key": key,
        "time": r.time.timestamp(),
        "w_v": r.weight,
        "t": r.tempOut,
        "h": r.humidityOut,
        "bv": r.vbatOut,
        "rssi": r.rssiOut,
        "p": r.pressure,
    }
    measurements.append(data)

# Hiveheart
# Query measurements for hive 30522 where tempIn is not null
key = "f0bdcettzyyryegl"
stmt = (
    select(HiveHistory)
    .where(HiveHistory.hive_id == bhm_id, HiveHistory.tempIn.isnot(None))
    .order_by(HiveHistory.time.desc())
)
results = session.execute(stmt).scalars().all()

for r in results:
    frequency_band = None
    for (lower, upper), band_name in FREQUENCY_BANDS.items():
        if r.frequency and lower <= r.frequency < upper:
            frequency_band = band_name
            break

    data = {
        "key": key,
        "time": r.time.timestamp(),
        "t_i": r.tempIn,
        "h_i": r.humidityIn,
        "bv": r.vbatIn,
        "rssi": r.rssiIn,
        "frequency_band": frequency_band,
    }
    measurements.append(data)

for data in measurements:
    res = requests.post(
        f"{BASE_URL}/api/sensors?key={data.pop('key')}", headers=HEADERS, json=data
    )
    print(f"{data} -> {res.status_code} {res.text}")
    remaining = int(res.headers.get("X-RateLimit-Remaining", 0))
    limit = int(res.headers.get("X-RateLimit-Limit", 60))
    if remaining < limit * 0.1:  # If less than 10% remaining
        sleep_time = 60  # Default to 60 seconds if no reset header
        if "X-RateLimit-Reset" in res.headers:
            reset_time = int(res.headers["X-RateLimit-Reset"])
            sleep_time = max(1, reset_time - int(time.time()))
        time.sleep(sleep_time)


session.close()
