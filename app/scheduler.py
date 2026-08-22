import logging
from datetime import datetime, timezone
from functools import partial

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import Settings
from app.geocoding.client import geocode
from app.ingestion.backend_client import ingest_events
from app.normalization.ai_enrichment import enrich_event_with_ai, enrich_event_with_novita
from app.normalization.normalizer import EnrichFn, normalize_events
from app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)


def build_enrich_fn(settings: Settings) -> EnrichFn:
    if settings.novita_api_key:
        return partial(
            enrich_event_with_novita,
            api_key=settings.novita_api_key,
            base_url=settings.novita_base_url,
            model=settings.novita_model,
        )
    return partial(
        enrich_event_with_ai,
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )


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
        enrich_fn = build_enrich_fn(settings)
        raw_events = adapter.fetch_raw_events()
        events = normalize_events(raw_events, name, category_mapping, geocode_fn, enrich_fn)
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
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
