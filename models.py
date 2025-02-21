from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, ARRAY, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from settings import ATTRIBUTES

Base = declarative_base()


class Apiary(Base):
    __tablename__ = "apiary"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    hives = relationship("Hive", cascade="all, delete-orphan", back_populates="apiary")


class Hive(Base):
    __tablename__ = "hive"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    apiary_id = Column(
        Integer, ForeignKey("apiary.id", ondelete="CASCADE"), nullable=False
    )
    apiary = relationship("Apiary", back_populates="hives")
    sensor_assignments = relationship(
        "SensorAssignment", cascade="all, delete-orphan", back_populates="hive"
    )


class Sensor(Base):
    __tablename__ = "sensor"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    modules = Column(ARRAY(Text))
    raw = Column(JSONB)
    assignments = relationship(
        "SensorAssignment", cascade="all, delete-orphan", back_populates="sensor"
    )
    history = relationship(
        "History", cascade="all, delete-orphan", back_populates="sensor"
    )


class SensorAssignment(Base):
    __tablename__ = "sensor_assignment"

    id = Column(Integer, primary_key=True)
    sensor_id = Column(
        Integer, ForeignKey("sensor.id", ondelete="CASCADE"), nullable=False
    )
    hive_id = Column(Integer, ForeignKey("hive.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    sensor = relationship("Sensor", back_populates="assignments")
    hive = relationship("Hive", back_populates="sensor_assignments")


class History(Base):
    __tablename__ = "history"

    sensor_id = Column(
        Integer, ForeignKey("sensor.id", ondelete="CASCADE"), primary_key=True
    )
    time = Column(DateTime(timezone=True), primary_key=True)
    sensor = relationship("Sensor", back_populates="history")
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
