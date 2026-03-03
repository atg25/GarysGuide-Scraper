from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class RunRecordLike(Protocol):
    @property
    def run_id(self) -> int:
        ...

    @property
    def status(self) -> str:
        ...

    @property
    def fetched_count(self) -> int:
        ...

    @property
    def attempts(self) -> int:
        ...

    @property
    def error(self) -> str:
        ...


@runtime_checkable
class EventScraper(Protocol):
    def get_events(self) -> List[Dict[str, str]]:
        ...


@runtime_checkable
class EventStore(Protocol):
    def init_schema(self) -> None:
        ...

    def persist_run(
        self,
        *,
        source: str,
        fetched_at: str,
        search_term: str,
        record_limit: int,
        status: str,
        attempts: int,
        error: str,
        events: Iterable[Dict[str, str]],
    ) -> RunRecordLike:
        ...

    def fetch_events(self, *, limit: int = 0, ai_only: bool = False) -> List[Dict[str, str]]:
        ...


@runtime_checkable
class HttpResponse(Protocol):
    @property
    def text(self) -> str:
        ...

    def raise_for_status(self) -> None:
        ...


@runtime_checkable
class HttpClient(Protocol):
    def get(
        self,
        url: str,
        *,
        headers: Dict[str, str],
        timeout: int,
    ) -> HttpResponse:
        ...
