from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PipelineConfig:
    cron_schedule: str = "0 */6 * * *"
    timezone: str = "UTC"
    scraper_strategy: str = "web"
    scraper_search_term: str = ""
    scraper_limit: int = 0
    db_path: str = "/data/garys_events.db"
    retry_attempts: int = 3
    retry_backoff_seconds: float = 5.0
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
        cron_schedule=os.getenv("CRON_SCHEDULE", "0 */6 * * *"),
        timezone=os.getenv("TZ", "UTC"),
        scraper_strategy=os.getenv("SCRAPER_STRATEGY", "web"),
        scraper_search_term=os.getenv("SCRAPER_SEARCH_TERM", ""),
        scraper_limit=_env_int("SCRAPER_LIMIT", 0),
        db_path=os.getenv("DB_PATH", "/data/garys_events.db"),
        retry_attempts=_env_int("RETRY_ATTEMPTS", 3),
        retry_backoff_seconds=_env_float("RETRY_BACKOFF_SECONDS", 5.0),
        api_token=os.getenv("API_TOKEN"),
    )
