from __future__ import annotations

import argparse

from croniter import croniter

from .config import load_config_from_env
from .exceptions import ScraperNetworkError



def validate_cron_schedule(schedule: str) -> None:
    if not croniter.is_valid(schedule):
        raise ValueError(f"Invalid cron schedule: {schedule}")


def is_transient_error(exc: Exception) -> bool:
    return isinstance(exc, ScraperNetworkError)


def backoff_seconds(base_seconds: float, attempt: int) -> float:
    return max(0.0, base_seconds) * max(1, attempt)



def main() -> int:
    parser = argparse.ArgumentParser(description="Validate cron schedule for garys_nyc_events")
    parser.add_argument("--schedule", help="Cron schedule to validate. Defaults to CRON_SCHEDULE env.")
    args = parser.parse_args()

    schedule = args.schedule or load_config_from_env().cron_schedule
    validate_cron_schedule(schedule)
    print(f"Valid cron schedule: {schedule}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
