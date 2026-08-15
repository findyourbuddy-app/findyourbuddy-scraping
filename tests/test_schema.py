from datetime import datetime

import pytest
from pydantic import ValidationError

from app.normalization.schema import EventPayload


def test_event_payload_accepts_valid_data() -> None:
    event = EventPayload(
        external_id="evt-1",
        source="test-source",
        title="Test Event",
        category="muzik",
        location_name="Venue",
        latitude=41.0,
        longitude=29.0,
        starts_at=datetime(2026, 9, 1, 20, 0),
    )

    assert event.description is None
    assert event.source_url is None
    assert event.image_url is None


def test_event_payload_requires_mandatory_fields() -> None:
    with pytest.raises(ValidationError):
        EventPayload(source="test-source", title="Test Event")
