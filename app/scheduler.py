import logging
from functools import partial

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import Settings
from app.geocoding.client import geocode
from app.ingestion.backend_client import ingest_events
from app.normalization.normalizer import normalize_events
from app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)


def run_source(
    name: str,
    adapter: SourceAdapter,
    settings: Settings,
    category_mapping: dict[str, str],
) -> None:
    try:
        geocode_fn = partial(
            geocode,
            delay_seconds=settings.geocoding_delay_seconds,
            base_url=settings.geocoding_base_url,
            user_agent=settings.geocoding_user_agent,
        )
        raw_events = adapter.fetch_raw_events()
        events = normalize_events(raw_events, name, category_mapping, geocode_fn)
        ingest_events(events, settings.backend_api_url, settings.scraper_api_key)
    except Exception:
        logger.exception(f"Source failed, skipping: {name}")


def run_all_sources(
    sources: dict[str, SourceAdapter],
    settings: Settings,
    category_mapping_by_source: dict[str, dict[str, str]],
) -> None:
    for name, adapter in sources.items():
        run_source(name, adapter, settings, category_mapping_by_source.get(name, {}))


def start_scheduler(
    sources: dict[str, SourceAdapter],
    settings: Settings,
    category_mapping_by_source: dict[str, dict[str, str]],
) -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_all_sources,
        "interval",
        hours=settings.schedule_interval_hours,
        args=[sources, settings, category_mapping_by_source],
    )
    scheduler.start()
