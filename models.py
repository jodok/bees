from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, ARRAY, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from settings import ATTRIBUTES

Base = declarative_base()


class Apiary(Base):
    __tablename__ = "apiary"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)


class Hive(Base):
    __tablename__ = "hive"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    apiary_id = Column(Integer, ForeignKey("apiary.id"))


class Sensor(Base):
    __tablename__ = "sensor"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    modules = Column(ARRAY(Text))
    hive_id = Column(Integer, ForeignKey("hive.id"))
    raw = Column(JSONB)


class History(Base):
    __tablename__ = "history"

    sensor_id = Column(Integer, ForeignKey("sensor.id"), primary_key=True)
    time = Column(DateTime(timezone=True), primary_key=True)
    # Dynamically create columns from ATTRIBUTES
    for attr in ATTRIBUTES.split(";"):
        locals()[attr] = Column(Float)


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True), nullable=True)
    title = Column(Text, nullable=False)
    tags = Column(ARRAY(Text), nullable=True)
