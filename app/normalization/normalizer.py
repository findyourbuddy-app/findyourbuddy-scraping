import logging
from typing import Any, Callable

from app.normalization.category_mapper import map_category
from app.normalization.schema import EventPayload

logger = logging.getLogger(__name__)

GeocodeFn = Callable[[str], tuple[float, float] | None]
EnrichFn = Callable[[EventPayload], EventPayload]


def _identity_enrich(payload: EventPayload) -> EventPayload:
    return payload


import html
import re

def clean_html(text: str | None) -> str | None:
    if not text:
        return text
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return re.sub(r'\n\s*\n+', '\n\n', text).strip()

def normalize_event(
    raw: dict[str, Any],
    source: str,
    category_mapping: dict[str, str],
    geocode_fn: GeocodeFn,
    enrich_fn: EnrichFn = _identity_enrich,
) -> EventPayload | None:
    if raw.get("latitude") is not None and raw.get("longitude") is not None:
        latitude, longitude = raw["latitude"], raw["longitude"]
    else:
        address = clean_html(raw["address"]) or raw["address"]
        coordinates = geocode_fn(address)
        if coordinates is None:
            logger.warning(f"Geocoding failed, skipping event: {raw.get('external_id')}")
            return None
        latitude, longitude = coordinates

    payload = EventPayload(
        external_id=raw["external_id"],
        source=source,
        title=clean_html(raw["title"]) or raw["title"],
        description=clean_html(raw.get("description")),
        category=map_category(raw["category_raw"], category_mapping),
        location_name=raw["location_name"],
        latitude=latitude,
        longitude=longitude,
        starts_at=raw["starts_at"],
        source_url=raw.get("source_url"),
        image_url=raw.get("image_url"),
    )

    return enrich_fn(payload)


def normalize_events(
    raw_events: list[dict[str, Any]],
    source: str,
    category_mapping: dict[str, str],
    geocode_fn: GeocodeFn,
    enrich_fn: EnrichFn = _identity_enrich,
) -> list[EventPayload]:
    events: list[EventPayload] = []
    for raw in raw_events:
        event = normalize_event(raw, source, category_mapping, geocode_fn, enrich_fn)
        if event is not None:
            events.append(event)
    return events
