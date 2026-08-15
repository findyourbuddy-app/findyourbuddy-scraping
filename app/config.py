import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    backend_api_url: str
    scraper_api_key: str
    etkinlik_io_api_token: str = ""
    schedule_interval_hours: float = 6.0
    geocoding_delay_seconds: float = 1.0
    geocoding_base_url: str = "https://nominatim.openstreetmap.org"
    geocoding_user_agent: str
    config_path: Path = Path("config.json")
    gemini_api_key: str = ""


class AppConfig(BaseModel):
    active_sources: list[str]
    category_mapping: dict[str, dict[str, str]]


def load_app_config(config_path: Path) -> AppConfig:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return AppConfig.model_validate(raw)


@lru_cache
def get_settings() -> Settings:
    return Settings()
