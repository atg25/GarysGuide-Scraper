from __future__ import annotations

from typing import List, Optional

from garys_nyc_events.exceptions import ScraperNetworkError


class StubHttpResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self._text = text
        self.status_code = status_code

    @property
    def text(self) -> str:
        return self._text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise ScraperNetworkError(f"HTTP {self.status_code}")


class StubHttpClient:
    def __init__(self, responses: List[StubHttpResponse]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def get(self, url: str, *, headers: dict, timeout: int) -> StubHttpResponse:
        self.calls += 1
        if not self._responses:
            return StubHttpResponse("", status_code=404)
        return self._responses.pop(0)


class FailingHttpClient:
    def __init__(self, exc: Optional[Exception] = None) -> None:
        self.exc = exc or ScraperNetworkError("connection failed")

    def get(self, url: str, *, headers: dict, timeout: int):
        raise self.exc
