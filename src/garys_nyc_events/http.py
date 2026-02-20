from __future__ import annotations

from typing import Dict

import requests

from .exceptions import ScraperNetworkError, ScraperTimeoutError


class RequestsHttpResponse:
    def __init__(self, response: requests.Response) -> None:
        self._response = response

    @property
    def text(self) -> str:
        return self._response.text

    def raise_for_status(self) -> None:
        try:
            self._response.raise_for_status()
        except requests.HTTPError as exc:
            raise ScraperNetworkError(
                f"Network error fetching {self._response.url}",
                cause=exc,
            ) from exc


class RequestsHttpClient:
    def get(self, url: str, *, headers: Dict[str, str], timeout: int) -> RequestsHttpResponse:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            return RequestsHttpResponse(response)
        except requests.Timeout as exc:
            raise ScraperTimeoutError(f"Timed out fetching {url}", cause=exc) from exc
        except requests.RequestException as exc:
            raise ScraperNetworkError(f"Network error fetching {url}", cause=exc) from exc
