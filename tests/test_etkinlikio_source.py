import httpx
import respx

from app.sources.etkinlikio import EtkinlikIoSource

EVENTS_URL = "https://etkinlik.io/api/v2/events"


def _event(
    id: int,
    venue_type: str = "VENUE",
    venue_data: dict | None = None,
) -> dict:
    if venue_data is None:
        venue_data = {
            "name": "Salon X",
            "address": "Istiklal Cad. No:1",
            "lat": "41.0082",
            "lng": "28.9784",
        }
    return {
        "id": id,
        "name": f"Event {id}",
        "content": "<p>desc</p>",
        "start_r001": "2026-09-01T18:00:00+00:00",
        "category": {"id": 1, "name": "Konser", "slug": "konser"},
        "venue_type": venue_type,
        "venue_data": venue_data,
        "url": f"https://etkinlik.io/etkinlik/{id}",
        "poster_url": f"https://etkinlik.io/posters/{id}.jpg",
    }


@respx.mock
def test_fetch_raw_events_maps_venue_with_coordinates() -> None:
    respx.get(EVENTS_URL).mock(
        return_value=httpx.Response(
            200, json={"meta": {"total_count": 1}, "items": [_event(1)]}
        )
    )

    events = EtkinlikIoSource(api_token="token").fetch_raw_events()

    assert len(events) == 1
    event = events[0]
    assert event["external_id"] == "1"
    assert event["title"] == "Event 1"
    assert event["category_raw"] == "konser"
    assert event["location_name"] == "Salon X"
    assert event["latitude"] == 41.0082
    assert event["longitude"] == 28.9784
    assert event["image_url"] == "https://etkinlik.io/posters/1.jpg"
    assert event["source_url"] == "https://etkinlik.io/etkinlik/1"


@respx.mock
def test_fetch_raw_events_maps_venue_without_coordinates() -> None:
    venue_without_coords = {
        "name": "Hilltown Sahne",
        "address": "Aydinevler Siteler Yolu No:28",
        "lat": None,
        "lng": None,
        "city": {"id": 40, "name": "Istanbul", "slug": "istanbul"},
        "district": {"id": 467, "name": "Maltepe", "slug": "maltepe"},
        "neighborhood": None,
    }
    respx.get(EVENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "meta": {"total_count": 1},
                "items": [_event(4, venue_type="VENUE", venue_data=venue_without_coords)],
            },
        )
    )

    events = EtkinlikIoSource(api_token="token").fetch_raw_events()

    assert len(events) == 1
    event = events[0]
    assert "latitude" not in event
    assert "longitude" not in event
    assert event["address"] == "Aydinevler Siteler Yolu No:28, Maltepe, Istanbul"


@respx.mock
def test_fetch_raw_events_maps_manual_venue_without_coordinates() -> None:
    manual_venue = {
        "name": "Kiraathane",
        "address": "Bahce Sk. No:2",
        "neighborhood_name": "Moda",
        "district_name": "Kadikoy",
        "city_name": "Istanbul",
    }
    respx.get(EVENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "meta": {"total_count": 1},
                "items": [_event(2, venue_type="MANUAL", venue_data=manual_venue)],
            },
        )
    )

    events = EtkinlikIoSource(api_token="token").fetch_raw_events()

    assert len(events) == 1
    event = events[0]
    assert "latitude" not in event
    assert "longitude" not in event
    assert event["address"] == "Bahce Sk. No:2, Moda, Kadikoy, Istanbul"


@respx.mock
def test_fetch_raw_events_skips_online_events() -> None:
    respx.get(EVENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "meta": {"total_count": 1},
                "items": [_event(3, venue_type="ONLINE", venue_data=None)],
            },
        )
    )

    events = EtkinlikIoSource(api_token="token").fetch_raw_events()

    assert events == []


@respx.mock
def test_fetch_raw_events_paginates_until_total_count_reached() -> None:
    page_one = [_event(i) for i in range(100)]
    page_two = [_event(100)]
    route = respx.get(EVENTS_URL).mock(
        side_effect=[
            httpx.Response(200, json={"meta": {"total_count": 101}, "items": page_one}),
            httpx.Response(200, json={"meta": {"total_count": 101}, "items": page_two}),
        ]
    )

    events = EtkinlikIoSource(api_token="token").fetch_raw_events()

    assert route.call_count == 2
    assert len(events) == 101


@respx.mock
def test_fetch_raw_events_sends_token_header() -> None:
    route = respx.get(EVENTS_URL).mock(
        return_value=httpx.Response(200, json={"meta": {"total_count": 0}, "items": []})
    )

    EtkinlikIoSource(api_token="secret-token").fetch_raw_events()

    assert route.calls.last.request.headers["X-Etkinlik-Token"] == "secret-token"
