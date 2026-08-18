import logging
import os
import signal
from types import FrameType

from app.config import Settings, get_settings, load_app_config
from app.scheduler import start_scheduler
from app.sources.base import SourceAdapter
from app.sources.etkinlikio import EtkinlikIoSource

logging.basicConfig(level=logging.INFO)


def build_source_registry(settings: Settings) -> dict[str, SourceAdapter]:
    registry: dict[str, SourceAdapter] = {}
    if settings.etkinlik_io_api_token:
        registry["etkinlik_io"] = EtkinlikIoSource(api_token=settings.etkinlik_io_api_token)
    return registry


def _force_exit(signum: int, frame: FrameType | None) -> None:
    # BlockingScheduler waits for the running job's worker thread on shutdown,
    # so a normal exit blocks until the in-flight source finishes. os._exit
    # kills the process immediately instead.
    os._exit(1)


def main() -> None:
    signal.signal(signal.SIGINT, _force_exit)
    settings = get_settings()
    app_config = load_app_config(settings.config_path)
    source_registry = build_source_registry(settings)
    active_sources = {
        name: source_registry[name]
        for name in app_config.active_sources
        if name in source_registry
    }
    start_scheduler(active_sources, settings, app_config.category_mapping)


if __name__ == "__main__":
    main()
