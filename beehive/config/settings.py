import os
import json
from dotenv import load_dotenv

load_dotenv()

# API Settings
BASE_URL = "https://main.beehivemonitoring.com"
API_TOKEN = os.getenv("BEEHIVE_API_TOKEN")
HEADERS = {"X-Auth-Token": API_TOKEN}

# Database Settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/bees")

# Apiary Settings
APIARIES = json.loads(os.getenv("APIARIES", "[]"))

# History Settings
ATTRIBUTES = (
    "weight;pressure;pressureGw;pressureEnv;inTotal;outTotal;magX;magY;magZ;"
    "accX;accY;accZ;tempIn;tempOut;tempEnv;humidityIn;humidityOut;humidityEnv;"
    "humiditySh1;humiditySh2;humiditySh3;frequency;amplitude;vbatIn;vbatOut;"
    "vbatEnv;vbatGw;vbatMap;rssiIn;rssiOut;rssiEnv;rssiGw;rssiMap;co2;tvoc;"
    "co;o2;o3;so;no;so2;pm25;pm10"
)
