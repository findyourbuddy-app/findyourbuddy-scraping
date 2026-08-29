import logging
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://etkinlik.io/api/v2"
PAGE_SIZE = 50  # Reduced from 100 to keep p95 latency under 300ms per Etkinlik.io docs
MAX_RETRY_ATTEMPTS = 2
RETRY_WAIT_MIN_SECONDS = 2
RETRY_WAIT_MAX_SECONDS = 10


@retry(
    stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
    wait=wait_exponential(min=RETRY_WAIT_MIN_SECONDS, max=RETRY_WAIT_MAX_SECONDS),
)
def _fetch_page(client: httpx.Client, skip: int) -> dict[str, Any]:
    response = client.get(
        "/events",
        params={"take": PAGE_SIZE, "skip": skip, "sort_by": "upcoming"},
    )
    response.raise_for_status()
    return response.json()


def _record_impression(client: httpx.Client, event_id: str) -> None:
    """Records an event impression on Etkinlik.io API per vendor recommendation."""
    try:
        client.post(f"/events/{event_id}/impressions")
    except Exception as exc:
        logger.debug(f"Failed to record impression for Etkinlik.io event {event_id}: {exc}")


class EtkinlikIoSource:
    """https://api-docs.etkinlik.io (OAS: Etkinlik.io V2 API) uzerinden
    calisan etkinlikleri ceker. Sadece fiziksel bir venue'su olan
    etkinlikler (venue_type VENUE veya MANUAL) alinir; ONLINE etkinlikler
    konum tabanli oldugumuz icin atlanir."""

    def __init__(self, api_token: str, base_url: str = DEFAULT_BASE_URL) -> None:
        self._api_token = api_token
        self._base_url = base_url.rstrip("/")

    def fetch_raw_events(self) -> list[dict[str, Any]]:
        raw_events: list[dict[str, Any]] = []
        skip = 0
        with httpx.Client(
            base_url=self._base_url,
            headers={"X-Etkinlik-Token": self._api_token},
            timeout=60.0,
        ) as client:
            while True:
                payload = _fetch_page(client, skip)
                items = payload["items"]

                for item in items:
                    raw = _map_event(item)
                    if raw is not None:
                        raw_events.append(raw)
                        _record_impression(client, str(item["id"]))

                skip += PAGE_SIZE
                if skip >= payload["meta"]["total_count"]:
                    break

        return raw_events


def _map_event(item: dict[str, Any]) -> dict[str, Any] | None:
    location = _map_location(item)
    if location is None:
        logger.info(f"Skipping event without a physical venue: {item.get('id')}")
        return None

    raw: dict[str, Any] = {
        "external_id": str(item["id"]),
        "title": item["name"],
        "description": item.get("content"),
        "category_raw": item["category"]["slug"],
        "location_name": location["location_name"],
        "address": location["address"],
        "starts_at": datetime.fromisoformat(item["start_r001"]),
        "source_url": item.get("url"),
        "image_url": item.get("poster_url"),
    }
    if "latitude" in location:
        raw["latitude"] = location["latitude"]
        raw["longitude"] = location["longitude"]
    return raw


def _map_location(item: dict[str, Any]) -> dict[str, Any] | None:
    venue = item.get("venue_data")
    if venue is None:
        return None

    if item.get("venue_type") == "VENUE":
        # Real data shows registered venues don't always have lat/lng set,
        # despite being venue_type VENUE -- fall back to address-based
        # geocoding (like MANUAL) rather than crashing on float(None).
        address_parts = [
            venue.get("address"),
            (venue.get("neighborhood") or {}).get("name"),
            (venue.get("district") or {}).get("name"),
            (venue.get("city") or {}).get("name"),
        ]
        location: dict[str, Any] = {
            "location_name": venue["name"],
            "address": ", ".join(part for part in address_parts if part),
        }
        lat, lng = venue.get("lat"), venue.get("lng")
        if lat is not None and lng is not None:
            location["latitude"] = float(lat)
            location["longitude"] = float(lng)
        return location

    if item.get("venue_type") == "MANUAL":
        address_parts = [
            venue.get("address"),
            venue.get("neighborhood_name"),
            venue.get("district_name"),
            venue.get("city_name"),
        ]
        return {
            "location_name": venue["name"],
            "address": ", ".join(part for part in address_parts if part),
        }

    return None
