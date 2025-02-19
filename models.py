from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from settings import ATTRIBUTES

Base = declarative_base()


class Apiary(Base):
    __tablename__ = "apiary"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class Hive(Base):
    __tablename__ = "hive"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    apiary_id = Column(Integer, ForeignKey("apiary.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class History(Base):
    __tablename__ = "history"

    hive_id = Column(Integer, ForeignKey("hive.id"), primary_key=True)
    time = Column(DateTime(timezone=True), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


# Dynamically create columns from ATTRIBUTES
for attr in ATTRIBUTES.split(";"):
    setattr(History, attr, Column(Float))
