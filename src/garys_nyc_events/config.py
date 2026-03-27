from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PipelineConfig:
    cron_schedule: str = "0 8 * * *"
    timezone: str = "UTC"
    scraper_strategy: str = "web"
    scraper_search_term: str = ""
    scraper_limit: int = 0
    db_path: str = "./garys_events.db"
    retry_attempts: int = 3
    retry_backoff_seconds: float = 5.0
    scraper_dedup_window_days: int = 0
    gemini_api_key: Optional[str] = None
    tagging_enabled: bool = True
    api_token: Optional[str] = None


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


def load_config_from_env() -> PipelineConfig:
    return PipelineConfig(
        cron_schedule=os.getenv("CRON_SCHEDULE", "0 8 * * *"),
        timezone=os.getenv("TZ", "UTC"),
        scraper_strategy=os.getenv("SCRAPER_STRATEGY", "web"),
        scraper_search_term=os.getenv("SCRAPER_SEARCH_TERM", ""),
        scraper_limit=_env_int("SCRAPER_LIMIT", 0),
        db_path=os.getenv("DB_PATH", "./garys_events.db"),
        retry_attempts=_env_int("RETRY_ATTEMPTS", 3),
        retry_backoff_seconds=_env_float("RETRY_BACKOFF_SECONDS", 5.0),
        scraper_dedup_window_days=_env_int("SCRAPER_DEDUP_WINDOW_DAYS", 0),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        tagging_enabled=os.getenv("TAGGING_ENABLED", "true").lower() != "false",
        api_token=os.getenv("API_TOKEN"),
    )
