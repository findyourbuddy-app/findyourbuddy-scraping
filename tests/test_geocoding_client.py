import httpx
import respx

from app.geocoding.client import geocode


@respx.mock
def test_geocode_returns_coordinates_on_success() -> None:
    respx.get("https://geocode.example.com/search").mock(
        return_value=httpx.Response(200, json=[{"lat": "41.0082", "lon": "28.9784"}])
    )

    result = geocode(
        "Istanbul",
        delay_seconds=0,
        base_url="https://geocode.example.com",
        user_agent="test-agent",
    )

    assert result == (41.0082, 28.9784)


@respx.mock
def test_geocode_returns_none_when_no_results() -> None:
    respx.get("https://geocode.example.com/search").mock(return_value=httpx.Response(200, json=[]))

    result = geocode(
        "Nonexistent Place",
        delay_seconds=0,
        base_url="https://geocode.example.com",
        user_agent="test-agent",
    )

    assert result is None


@respx.mock
def test_geocode_returns_none_on_http_error() -> None:
    respx.get("https://geocode.example.com/search").mock(return_value=httpx.Response(500))

    result = geocode(
        "Istanbul",
        delay_seconds=0,
        base_url="https://geocode.example.com",
        user_agent="test-agent",
    )

    assert result is None
