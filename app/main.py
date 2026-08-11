import logging

from app.config import get_settings, load_app_config
from app.scheduler import start_scheduler
from app.sources.base import SourceAdapter

logging.basicConfig(level=logging.INFO)

# Her kaynak secildikce buraya kaydedilir: {"biletix": BiletixSource()}
SOURCE_REGISTRY: dict[str, SourceAdapter] = {}


def main() -> None:
    settings = get_settings()
    app_config = load_app_config(settings.config_path)
    active_sources = {
        name: SOURCE_REGISTRY[name]
        for name in app_config.active_sources
        if name in SOURCE_REGISTRY
    }
    start_scheduler(active_sources, settings, app_config.category_mapping)


if __name__ == "__main__":
    main()
