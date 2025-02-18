from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from beehive.config import settings

Base = declarative_base()


class Apiary(Base):
    __tablename__ = "apiary"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, unique=True, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at: datetime = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class Hive(Base):
    __tablename__ = "hive"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, unique=True, nullable=False)
    apiary_id: int = Column(Integer, ForeignKey("apiary.id"))
    created_at: datetime = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at: datetime = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class History(Base):
    __tablename__ = "history"

    hive_id: int = Column(Integer, ForeignKey("hive.id"), primary_key=True)
    time: datetime = Column(DateTime, primary_key=True)
    created_at: datetime = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at: datetime = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    # Dynamically create columns for all sensor attributes
    for attr in settings.ATTRIBUTES.split(";"):
        locals()[attr] = Column(Float)

    @classmethod
    def from_api_data(
        cls, hive_id: int, time_ms: int, data: Dict[str, Any]
    ) -> "History":
        """Create a History instance from API data."""
        dt = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc)
        return cls(hive_id=hive_id, time=dt, **data)
