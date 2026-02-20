from __future__ import annotations

from typing import Optional


class GarysGuideError(Exception):
    pass


class ScraperNetworkError(GarysGuideError):
    def __init__(self, message: str, cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.cause = cause


class ScraperTimeoutError(ScraperNetworkError):
    pass


class ScraperParseError(GarysGuideError):
    pass


class StorageError(GarysGuideError):
    pass
