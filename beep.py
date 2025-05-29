import requests
import time
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models import History
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import argparse
import logging
from filelock import FileLock, Timeout
from beep_sensors import (
    HIVES,
    DEVICES,
    SENSORS_HEART,
    SENSORS_SCALE,
)
from database import get_session, close_session
import atexit
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# If running in cron (no TTY), set to WARNING level
if not os.isatty(0):
    logging.getLogger().setLevel(logging.WARNING)

# Lockfile mechanism
LOCK_FILE = "/tmp/beep.lock"
lock = FileLock(
    LOCK_FILE, timeout=0
)  # timeout=0 means it will fail immediately if lock exists

try:
    lock.acquire()
except Timeout:
    # If we can't acquire the lock, another instance is running
    if os.isatty(0):  # Only log if running in terminal
        logging.warning("Another instance is already running. Exiting.")
    exit(0)

# Register cleanup function to release lock on exit
atexit.register(lock.release)

load_dotenv()


BASE_URL = "https://api.beep.nl"
HEADERS = {"Authorization": f"Bearer {os.getenv('BEEP_API_TOKEN')}"}

# Beehivemonitor -> Beep
HIVE_MAP = {
    30522: 66651,  # Beute 1
    30523: 66652,  # Beute 2
    30602: 66653,  # Beute 3
    30603: 66654,  # Beute 4
    30604: 66699,  # Beute 5
    30605: 66700,  # Beute 6
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


def rate_limit_aware_request(method, url, **kwargs):
    """
    Helper function to make rate-limited requests to the BEEP API.
    Handles rate limiting by checking response headers and waiting when necessary.
    """
    while True:
        response = requests.request(method, url, **kwargs)

        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        limit = int(response.headers.get("X-RateLimit-Limit", 60))

        if remaining < limit * 0.1:  # If less than 10% remaining
            sleep_time = 60  # Default to 60 seconds if no reset header
            if "X-RateLimit-Reset" in response.headers:
                reset_time = int(response.headers["X-RateLimit-Reset"])
                sleep_time = max(1, reset_time - int(time.time()))
            logging.info(f"Rate limit low. Waiting {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            return response


def setup_devices():
    for device in DEVICES:
        device["type"] = "other"
        res = rate_limit_aware_request(
            "POST", f"{BASE_URL}/api/devices", headers=HEADERS, json=device
        )
        logging.info(f"Device setup: {res.status_code} {res.text}")


def setup_sensors():
    for device in DEVICES:
        if device["type"] == "heart":
            sensors = SENSORS_HEART
        elif device["type"] == "scale":
            sensors = SENSORS_SCALE
        else:
            continue

        for sensor in sensors:
            sensor["device_id"] = device["id"]
            res = rate_limit_aware_request(
                "POST", f"{BASE_URL}/api/sensordefinition", headers=HEADERS, json=sensor
            )
            logging.info(f"Sensor setup: {res.status_code} {res.text}")


def sync_measurements():
    # Get database session
    session = get_session()

    try:
        for hive in HIVES:
            res = rate_limit_aware_request(
                "GET",
                f"{BASE_URL}/api/sensors/lastvalues",
                headers=HEADERS,
                params={"hive_id": hive["id"]},
            )
            if res.status_code != 200:
                last = datetime.now() - timedelta(days=1)
            else:
                last = res.json()["time"]  # "2025-02-14T01:35:04Z"
                last = datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ")

            bhm_id = get_bhm_hive_id(hive["id"])
            measurements = []

            # Scales
            for device in DEVICES:
                res = rate_limit_aware_request(
                    "GET", f"{BASE_URL}/api/devices/{device['id']}", headers=HEADERS
                )
                if res.status_code != 200:
                    logging.error(f"Device {device['id']} not found")
                    continue
                # needed to send measurement
                key = res.json()["key"]

                # Query all measurements for the hive that have either weight or tempIn data
                stmt = (
                    select(History)
                    .where(
                        History.sensor_id == bhm_id,
                        History.time > last - timedelta(minutes=15),
                    )
                    .order_by(History.time.desc())
                )
                results = session.execute(stmt).scalars().all()

                for r in results:
                    frequency_band = None
                    for (lower, upper), band_name in FREQUENCY_BANDS.items():
                        if r.frequency and lower <= r.frequency < upper:
                            frequency_band = band_name
                            break

                    # Determine if this is a scale or heart measurement based on available data
                    if r.weight is not None:
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
                    elif r.tempIn is not None:
                        data = {
                            "key": key,
                            "time": r.time.timestamp(),
                            "t_i": r.tempIn,
                            "h_i": r.humidityIn,
                            "bv": r.vbatIn,
                            "rssi": r.rssiIn,
                            "frequency_band": frequency_band,
                        }
                    else:
                        # Enhanced error logging with measurement details
                        measurement_details = {
                            "sensor_id": r.sensor_id,
                            "time": r.time,
                            "device_type": device["type"],
                            "all_attributes": {
                                attr: getattr(r, attr, None)
                                for attr in dir(r)
                                if not attr.startswith("_")  # Skip private attributes
                                and not callable(getattr(r, attr))  # Skip methods
                                and attr
                                not in [
                                    "metadata",
                                    "query",
                                    "query_class",
                                ]  # Skip SQLAlchemy internals
                            },
                        }
                        logging.error(
                            f"Unknown measurement type for sensor {r.sensor_id}. "
                            f"Device type: {device['type']}. "
                            f"Measurement details: {json.dumps(measurement_details, default=str)}"
                        )
                        continue
                    measurements.append(data)

            for data in measurements:
                res = rate_limit_aware_request(
                    "POST",
                    f"{BASE_URL}/api/sensors?key={data.pop('key')}",
                    headers=HEADERS,
                    json=data,
                )
                logging.info(f"{data} -> {res.status_code} {res.text}")
    finally:
        close_session()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BEEP API interaction tool")
    parser.add_argument(
        "action",
        choices=["setup", "sync"],
        default="sync",
        nargs="?",
        help="Action to perform: setup (devices and sensors) or sync (measurements)",
    )
    args = parser.parse_args()

    if args.action == "setup":
        setup_devices()
        setup_sensors()
    else:  # sync is default
        sync_measurements()
