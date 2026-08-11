import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.normalization.schema import EventPayload

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 50
INGEST_PATH = "/internal/events/ingest"
MAX_RETRY_ATTEMPTS = 3
RETRY_WAIT_MIN_SECONDS = 2
RETRY_WAIT_MAX_SECONDS = 30


@retry(
    stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
    wait=wait_exponential(min=RETRY_WAIT_MIN_SECONDS, max=RETRY_WAIT_MAX_SECONDS),
)
def _post_batch(
    client: httpx.Client,
    url: str,
    api_key: str,
    batch: list[EventPayload],
) -> dict[str, Any]:
    response = client.post(
        url,
        json=[event.model_dump(mode="json") for event in batch],
        headers={"X-Scraper-Api-Key": api_key},
    )
    response.raise_for_status()
    return response.json()


def ingest_events(
    events: list[EventPayload],
    backend_api_url: str,
    scraper_api_key: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> None:
    url = f"{backend_api_url.rstrip('/')}{INGEST_PATH}"
    with httpx.Client(timeout=30.0) as client:
        for start in range(0, len(events), batch_size):
            batch = events[start : start + batch_size]
            result = _post_batch(client, url, scraper_api_key, batch)
            logger.info(f"Batch ingested ({len(batch)} events): {result}")
