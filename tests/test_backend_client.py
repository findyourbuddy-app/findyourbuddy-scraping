import json
from datetime import datetime

import httpx
import respx

from app.ingestion.backend_client import fetch_known_external_ids, ingest_events
from app.normalization.schema import EventPayload

INGEST_URL = "https://backend.example.com/internal/events/ingest"
KNOWN_IDS_URL = "https://backend.example.com/internal/events/known-ids"


def _sample_event(external_id: str) -> EventPayload:
    return EventPayload(
        external_id=external_id,
        source="test-source",
        title="Test Event",
        category="muzik",
        location_name="Test Location",
        latitude=41.0,
        longitude=29.0,
        starts_at=datetime(2026, 9, 1, 20, 0),
    )


@respx.mock
def test_ingest_events_sends_single_batch() -> None:
    route = respx.post(INGEST_URL).mock(
        return_value=httpx.Response(200, json={"created": 1, "updated": 0, "skipped": 0, "errors": []})
    )

    ingest_events([_sample_event("evt-1")], "https://backend.example.com", "test-key")

    assert route.called
    assert route.calls.last.request.headers["X-Scraper-Api-Key"] == "test-key"
    sent_body = json.loads(route.calls.last.request.content)
    assert "events" in sent_body
    assert sent_body["events"][0]["external_id"] == "evt-1"


@respx.mock
def test_ingest_events_splits_into_batches() -> None:
    route = respx.post(INGEST_URL).mock(
        return_value=httpx.Response(200, json={"created": 1, "updated": 0, "skipped": 0, "errors": []})
    )

    events = [_sample_event(f"evt-{i}") for i in range(75)]
    ingest_events(events, "https://backend.example.com", "test-key", batch_size=50)

    assert route.call_count == 2


@respx.mock
def test_fetch_known_external_ids_returns_set() -> None:
    route = respx.get(KNOWN_IDS_URL, params={"source": "biletix"}).mock(
        return_value=httpx.Response(200, json={"external_ids": ["evt-1", "evt-2"]})
    )

    result = fetch_known_external_ids("https://backend.example.com", "test-key", "biletix")

    assert result == {"evt-1", "evt-2"}
    assert route.calls.last.request.headers["X-Scraper-Api-Key"] == "test-key"


@respx.mock
def test_fetch_known_external_ids_returns_empty_set_on_failure() -> None:
    respx.get(KNOWN_IDS_URL, params={"source": "biletix"}).mock(
        return_value=httpx.Response(500)
    )

    result = fetch_known_external_ids("https://backend.example.com", "test-key", "biletix")

    assert result == set()
