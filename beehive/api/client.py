from typing import Dict, List
import requests
from beehive.config import settings


class BeehiveClient:
    def __init__(
        self, base_url: str = settings.BASE_URL, headers: Dict = settings.HEADERS
    ):
        self.base_url = base_url
        self.headers = headers

    def get_hives(self) -> List[Dict]:
        """Fetch all hives from the API."""
        response = requests.get(f"{self.base_url}/api/hives", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_hive_history(self, hive_id: int, limit: int) -> List[Dict]:
        """Fetch history for a specific hive."""
        response = requests.get(
            f"{self.base_url}/api/hives/{hive_id}/history",
            params={
                "limit": limit,
                "reverse": "true",
                "attributes": settings.ATTRIBUTES,
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
