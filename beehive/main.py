import sys
from beehive.api.client import BeehiveClient
from beehive.config import settings
from beehive.db.models import History
from beehive.db.service import BeehiveService
from beehive.db.session import init_db, get_db


def main(argv: list[str]) -> None:
    """Main function to sync beehive data."""
    # Initialize the database
    init_db()

    # Create API client
    client = BeehiveClient()

    # Process all apiaries and hives
    with get_db() as db:
        service = BeehiveService(db)

        # Upsert apiaries
        for apiary in settings.APIARIES:
            service.upsert_apiary(apiary["id"], apiary["name"])

        # Fetch and process hives
        hives = client.get_hives()
        for hive in hives:
            hive_id = hive["id"]
            hive_name = hive["name"]

            # Find apiary for this hive
            apiary_id = next(
                apiary["id"]
                for apiary in settings.APIARIES
                if hive_id in apiary["hives"]
            )

            # Update hive information
            service.upsert_hive(hive_id, hive_name, apiary_id)

            # Get latest history timestamp and calculate limit
            latest_time = service.get_latest_history(hive_id)
            limit = service.calculate_history_limit(latest_time)

            # Fetch and process history
            history_data = client.get_hive_history(hive_id, limit)
            for entry in history_data:
                time_ms = entry.pop("time")
                history = History.from_api_data(hive_id, time_ms, entry)
                service.upsert_history(history)


if __name__ == "__main__":
    main(sys.argv[1:])
