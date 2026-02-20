from typing import Dict, Iterable, List

from garys_nyc_events.http import RequestsHttpClient
from garys_nyc_events.protocols import EventScraper, EventStore, HttpClient
from garys_nyc_events.runner_once import run_once
from garys_nyc_events.scraper import GarysGuideScraper
from garys_nyc_events.storage import SQLiteEventStore
from garys_nyc_events.config import PipelineConfig
from tests.http_doubles import StubHttpClient, StubHttpResponse


class StubScraper:
    def get_events(self) -> List[Dict[str, str]]:
        return [{"title": "AI Event", "url": "https://www.garysguide.com/events/1", "price": "FREE", "date": "Wed"}]


class StubStore:
    def __init__(self) -> None:
        self.initialized = False
        self.persisted = False

    def init_schema(self) -> None:
        self.initialized = True

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
    ) -> object:
        self.persisted = True
        event_list = list(events)
        return type(
            "RunRecordLike",
            (),
            {
                "run_id": 1,
                "status": status,
                "fetched_count": len(event_list),
                "attempts": attempts,
                "error": error,
            },
        )()


def test_sqlite_store_satisfies_event_store_protocol(tmp_path):
    db_path = tmp_path / "events.db"
    assert isinstance(SQLiteEventStore(str(db_path)), EventStore)


def test_garys_guide_scraper_satisfies_event_scraper_protocol():
    assert isinstance(GarysGuideScraper(delay_seconds=0), EventScraper)


def test_requests_http_client_satisfies_http_client_protocol():
    assert isinstance(RequestsHttpClient(), HttpClient)


def test_stub_http_client_satisfies_http_client_protocol():
    assert isinstance(StubHttpClient([StubHttpResponse(text="ok")]), HttpClient)


def test_run_once_accepts_in_memory_stub_store(tmp_path):
    store = StubStore()
    cfg = PipelineConfig(db_path=str(tmp_path / "events.db"))

    summary = run_once(
        config=cfg,
        scrape_func=lambda _cfg: [
            {"title": "AI Event", "url": "https://www.garysguide.com/events/1", "price": "FREE", "date": "Wed"}
        ],
        store=store,
    )

    assert store.initialized is True
    assert store.persisted is True
    assert summary.fetched_count == 1


def test_run_once_accepts_stub_scraper(tmp_path):
    store = StubStore()
    cfg = PipelineConfig(db_path=str(tmp_path / "events.db"))
    scraper = StubScraper()

    summary = run_once(config=cfg, scrape_func=lambda _cfg: scraper.get_events(), store=store)
    assert summary.fetched_count == 1
