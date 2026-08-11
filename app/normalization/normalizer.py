import logging
from typing import Any, Callable

from app.normalization.category_mapper import map_category
from app.normalization.schema import EventPayload

logger = logging.getLogger(__name__)

GeocodeFn = Callable[[str], tuple[float, float] | None]


def normalize_event(
    raw: dict[str, Any],
    source: str,
    category_mapping: dict[str, str],
    geocode_fn: GeocodeFn,
) -> EventPayload | None:
    coordinates = geocode_fn(raw["address"])
    if coordinates is None:
        logger.warning(f"Geocoding failed, skipping event: {raw.get('external_id')}")
        return None

    latitude, longitude = coordinates
    return EventPayload(
        external_id=raw["external_id"],
        source=source,
        title=raw["title"],
        description=raw.get("description"),
        category=map_category(raw["category_raw"], category_mapping),
        location_name=raw["location_name"],
        latitude=latitude,
        longitude=longitude,
        starts_at=raw["starts_at"],
        source_url=raw.get("source_url"),
    )


def normalize_events(
    raw_events: list[dict[str, Any]],
    source: str,
    category_mapping: dict[str, str],
    geocode_fn: GeocodeFn,
) -> list[EventPayload]:
    events: list[EventPayload] = []
    for raw in raw_events:
        event = normalize_event(raw, source, category_mapping, geocode_fn)
        if event is not None:
            events.append(event)
    return events
