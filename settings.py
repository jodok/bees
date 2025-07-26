import os
import json
from dotenv import load_dotenv

load_dotenv()

# API Configuration
BASE_URL = "https://main.beehivemonitoring.com"
HEADERS = {"X-Auth-Token": os.getenv("BEEHIVE_API_TOKEN")}

# Database Configuration
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://localhost/bees")

# Default configurations
DEFAULT_APIARIES = '[{"id":1,"name":"My Apiary"}]'
DEFAULT_HIVES = '[{"id":1,"name":"Hive 1","apiary_id":1}]'
DEFAULT_SENSORS = '[{"id":1,"name":"Sensor 1","modules":["weight"],"hive_id":1}]'
DEFAULT_ASSIGNMENTS = '[{"sensor_id":1,"hive_id":1}]'
# Load configurations from environment or use defaults
APIARIES = json.loads(os.getenv("APIARIES", DEFAULT_APIARIES))
HIVES = json.loads(os.getenv("HIVES", DEFAULT_HIVES))
SENSORS = json.loads(os.getenv("SENSORS", DEFAULT_SENSORS))
ASSIGNMENTS = json.loads(os.getenv("ASSIGNMENTS", DEFAULT_ASSIGNMENTS))

# Monitoring Attributes
ATTRIBUTES = (
    "weight;"
    "pressure;pressureGw;pressureEnv;"
    "inCounts;outCounts;inTotal;outTotal;"
    "magX;magY;magZ;accX;accY;accZ;"
    "tempIn;tempOut;tempEnv;"
    "humidityIn;humidityOut;humidityEnv;humiditySh1;humiditySh2;humiditySh3;"
    "frequency;amplitude;"
    "vbatIn;vbatOut;vbatEnv;vbatGw;vbatMap;"
    "rssiIn;rssiOut;rssiEnv;rssiGw;rssiMap;"
    "co2;tvoc;co;o2;o3;so;no;so2;pm25;pm10;"
    "fftPeak;fft"
)

# Attribute Type Definitions
# Define which attributes should be stored as arrays (ARRAY)
ARRAY_ATTRIBUTES = {"inCounts", "outCounts", "fft"}

# Define which attributes should be stored as integers
INTEGER_ATTRIBUTES = {"inTotal", "outTotal", "rssiIn", "rssiOut", "rssiGw", "fftPeak"}
