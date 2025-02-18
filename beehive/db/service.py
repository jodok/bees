from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from beehive.db.models import Apiary, Hive, History


class BeehiveService:
    def __init__(self, db: Session):
        self.db = db

    def upsert_apiary(self, apiary_id: int, name: str) -> None:
        """Create or update an apiary."""
        apiary = Apiary(id=apiary_id, name=name)
        self.db.merge(apiary)

    def upsert_hive(self, hive_id: int, name: str, apiary_id: int) -> None:
        """Create or update a hive."""
        hive = Hive(id=hive_id, name=name, apiary_id=apiary_id)
        self.db.merge(hive)

    def get_latest_history(self, hive_id: int) -> Optional[datetime]:
        """Get the latest history timestamp for a hive."""
        result = (
            self.db.query(History.time)
            .filter(History.hive_id == hive_id)
            .order_by(History.time.desc())
            .first()
        )
        return result[0] if result else None

    def calculate_history_limit(self, latest_time: Optional[datetime]) -> int:
        """Calculate how many history records to fetch."""
        latest_ts = int(latest_time.timestamp()) if latest_time else 0
        current_ts = int(datetime.now(timezone.utc).timestamp())
        return max(int((current_ts - latest_ts) / 86.4), 100)  # 1000 records per day

    def upsert_history(self, history: History) -> None:
        """Create or update a history record."""
        self.db.merge(history)
