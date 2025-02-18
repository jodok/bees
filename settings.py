import os
import json
from dotenv import load_dotenv

load_dotenv()

# API Configuration
BASE_URL = "https://main.beehivemonitoring.com"
HEADERS = {"X-Auth-Token": os.getenv("BEEHIVE_API_TOKEN")}

# Database Configuration
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://localhost/bees")

# Apiary Configuration
APIARIES = os.getenv("APIARIES")
APIARIES = json.loads(APIARIES)

# Monitoring Attributes
ATTRIBUTES = (
    "weight;pressure;pressureGw;pressureEnv;inTotal;outTotal;magX;magY;magZ;"
    "accX;accY;accZ;tempIn;tempOut;tempEnv;humidityIn;humidityOut;humidityEnv;"
    "humiditySh1;humiditySh2;humiditySh3;frequency;amplitude;vbatIn;vbatOut;"
    "vbatEnv;vbatGw;vbatMap;rssiIn;rssiOut;rssiEnv;rssiGw;rssiMap;co2;tvoc;"
    "co;o2;o3;so;no;so2;pm25;pm10"
)
