"""Run a single scrape cycle (no BlockingScheduler). For manual backfills."""

import logging

from app.config import get_settings, load_app_config
from app.main import build_source_registry
from app.scheduler import run_all_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

if __name__ == "__main__":
    settings = get_settings()
    cfg = load_app_config(settings.config_path)
    registry = build_source_registry(settings)
    active = {name: registry[name] for name in cfg.active_sources if name in registry}
    logging.info("active sources: %s", list(active))
    run_all_sources(active, settings, cfg.category_mapping)
    logging.info("scrape cycle finished")
