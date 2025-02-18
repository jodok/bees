from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Apiary(Base):
    __tablename__ = "apiary"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class Hive(Base):
    __tablename__ = "hive"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
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

    # Dynamically create columns for all sensor attributes
    ATTRIBUTES = "weight;pressure;pressureGw;pressureEnv;inTotal;outTotal;magX;magY;magZ;accX;accY;accZ;tempIn;tempOut;tempEnv;humidityIn;humidityOut;humidityEnv;humiditySh1;humiditySh2;humiditySh3;frequency;amplitude;vbatIn;vbatOut;vbatEnv;vbatGw;vbatMap;rssiIn;rssiOut;rssiEnv;rssiGw;rssiMap;co2;tvoc;co;o2;o3;so;no;so2;pm25;pm10"

    for attr in ATTRIBUTES.split(";"):
        locals()[attr] = Column(Float)

    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
