import logging
import time

import httpx

logger = logging.getLogger(__name__)


def geocode(
    address: str,
    delay_seconds: float,
    base_url: str,
    user_agent: str,
) -> tuple[float, float] | None:
    time.sleep(delay_seconds)
    try:
        response = httpx.get(
            f"{base_url}/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": user_agent},
            timeout=10.0,
        )
        response.raise_for_status()
        results = response.json()
    except httpx.HTTPError:
        logger.warning(f"Geocoding request failed for address: {address}")
        return None

    if not results:
        return None

    return float(results[0]["lat"]), float(results[0]["lon"])
