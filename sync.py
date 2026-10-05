import os
import time
from datetime import datetime, timezone

import requests
from google.cloud import bigquery

API_BASE = os.environ["HOTEL_API_URL"].rstrip("/")
API_TOKEN = os.environ["HOTEL_API_TOKEN"]
PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("BQ_DATASET", "hotel_raw")


def fetch_json(path: str, params=None, attempts: int = 4):
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}
    last = None
    for attempt in range(attempts):
        try:
            response = requests.get(
                f"{API_BASE}/{path.lstrip('/')}",
                headers=headers,
                params=params or {},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise last


def normalize_availability(hotel_id: str, payload):
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    items = payload.get("availability", payload if isinstance(payload, list) else [])
    for item in items:
        rows.append(
            {
                "hotel_id": hotel_id,
                "room_type_id": str(item["room_type_id"]),
                "date": item["date"],
                "available_rooms": int(item["available_rooms"]),
                "captured_at": now,
            }
        )
    return rows


def merge_rows(rows, target="availability"):
    if not rows:
        return 0
    client = bigquery.Client(project=PROJECT)
    target_id = f"{PROJECT}.{DATASET}.{target}"
    staging_id = f"{PROJECT}.{DATASET}._staging_{target}_{int(time.time())}"

    client.load_table_from_json(rows, staging_id).result()

    sql = f"""
    MERGE `{target_id}` T
    USING `{staging_id}` S
      ON T.hotel_id = S.hotel_id
     AND T.room_type_id = S.room_type_id
     AND T.date = S.date
    WHEN MATCHED THEN UPDATE SET
      available_rooms = S.available_rooms,
      captured_at = S.captured_at
    WHEN NOT MATCHED THEN INSERT
      (hotel_id, room_type_id, date, available_rooms, captured_at)
    VALUES
      (S.hotel_id, S.room_type_id, S.date, S.available_rooms, S.captured_at)
    """
    client.query(sql).result()
    client.delete_table(staging_id, not_found_ok=True)
    return len(rows)


def sync_hotel(hotel_id: str, start_date: str, end_date: str):
    payload = fetch_json(
        "/availability",
        {"hotel_id": hotel_id, "from": start_date, "to": end_date},
    )
    return merge_rows(normalize_availability(hotel_id, payload))


if __name__ == "__main__":
    print(
        {
            "rows_merged": sync_hotel(
                os.environ["HOTEL_ID"],
                os.environ["DATE_FROM"],
                os.environ["DATE_TO"],
            )
        }
    )
