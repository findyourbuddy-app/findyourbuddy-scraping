import logging
from datetime import datetime, timezone
from functools import partial

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import Settings
from app.geocoding.client import geocode
from app.ingestion.backend_client import fetch_known_external_ids, ingest_events
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
        known_ids = fetch_known_external_ids(settings.backend_api_url, settings.scraper_api_key, name)

        # Pass the known set INTO the fetch so the adapter skips already-ingested
        # events before any per-event work (impression pings, geocoding budget).
        raw_events = adapter.fetch_raw_events(known_ids)

        # Belt-and-suspenders in case a source ignores `known_ids`.
        new_raw_events = [e for e in raw_events if e["external_id"] not in known_ids]
        logger.info(f"{name}: {len(new_raw_events)} yeni etkinlik islenecek.")
        if not new_raw_events:
            return

        geocode_fn = partial(
            geocode,
            delay_seconds=settings.geocoding_delay_seconds,
            base_url=settings.geocoding_base_url,
            user_agent=settings.geocoding_user_agent,
        )
        enrich_fn = build_enrich_fn(settings)
        events = normalize_events(new_raw_events, name, category_mapping, geocode_fn, enrich_fn)
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
