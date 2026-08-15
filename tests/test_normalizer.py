from datetime import datetime
from typing import Any

from app.normalization.normalizer import normalize_event, normalize_events


def _raw_event(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "external_id": "evt-1",
        "title": "Test Event",
        "description": "desc",
        "category_raw": "concert",
        "location_name": "Venue",
        "address": "Some Address, Istanbul",
        "starts_at": datetime(2026, 9, 1, 20, 0),
        "source_url": "https://example.com/evt-1",
    }
    base.update(overrides)
    return base


def test_normalize_event_maps_fields() -> None:
    event = normalize_event(
        _raw_event(),
        source="test-source",
        category_mapping={"concert": "muzik"},
        geocode_fn=lambda address: (41.0, 29.0),
    )

    assert event is not None
    assert event.external_id == "evt-1"
    assert event.source == "test-source"
    assert event.category == "muzik"
    assert event.latitude == 41.0
    assert event.longitude == 29.0


def test_normalize_event_skips_when_geocoding_fails() -> None:
    event = normalize_event(
        _raw_event(),
        source="test-source",
        category_mapping={"concert": "muzik"},
        geocode_fn=lambda address: None,
    )

    assert event is None


def test_normalize_event_uses_provided_coordinates_without_geocoding() -> None:
    def geocode_fn(address: str) -> tuple[float, float] | None:
        raise AssertionError("geocode_fn should not be called when coordinates are provided")

    event = normalize_event(
        _raw_event(latitude=41.5, longitude=29.5),
        source="test-source",
        category_mapping={"concert": "muzik"},
        geocode_fn=geocode_fn,
    )

    assert event is not None
    assert event.latitude == 41.5
    assert event.longitude == 29.5


def test_normalize_event_maps_image_url() -> None:
    event = normalize_event(
        _raw_event(image_url="https://example.com/poster.jpg"),
        source="test-source",
        category_mapping={"concert": "muzik"},
        geocode_fn=lambda address: (41.0, 29.0),
    )

    assert event is not None
    assert event.image_url == "https://example.com/poster.jpg"


def test_normalize_events_filters_out_skipped() -> None:
    raw_events = [
        _raw_event(external_id="evt-1", address="Address A"),
        _raw_event(external_id="evt-2", address="Address B"),
    ]

    def geocode_fn(address: str) -> tuple[float, float] | None:
        return None if address == "Address B" else (41.0, 29.0)

    events = normalize_events(raw_events, "test-source", {"concert": "muzik"}, geocode_fn)

    assert len(events) == 1
    assert events[0].external_id == "evt-1"
