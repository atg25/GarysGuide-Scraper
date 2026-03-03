import json

from garys_nyc_events.config import PipelineConfig
from garys_nyc_events.storage import SQLiteEventStore
from garys_nyc_events.tagger import GeminiTagger
from garys_nyc_events.runner_once import _run_scrape


class _Response:
    def __init__(self, payload, status_ok=True):
        self._payload = payload
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise RuntimeError("network")

    def json(self):
        return self._payload


class _Session:
    def __init__(self, response):
        self._response = response

    def post(self, *_args, **_kwargs):
        return self._response


def _gemini_payload(text: str):
    return {
        "candidates": [{"content": {"parts": [{"text": text}]}}],
    }


def test_tagger_returns_empty_list_when_no_api_key():
    tagger = GeminiTagger(api_key=None)
    assert tagger.tag_event({"title": "AI"}) == []


def test_tagger_returns_empty_list_on_network_failure():
    tagger = GeminiTagger(api_key="x", session=_Session(_Response({}, status_ok=False)))
    assert tagger.tag_event({"title": "AI"}) == []


def test_tagger_returns_empty_list_on_malformed_json():
    tagger = GeminiTagger(api_key="x", session=_Session(_Response(_gemini_payload("not json"))))
    assert tagger.tag_event({"title": "AI"}) == []


def test_tagger_returns_empty_list_on_non_list_json():
    text = json.dumps({"key": "value"})
    tagger = GeminiTagger(api_key="x", session=_Session(_Response(_gemini_payload(text))))
    assert tagger.tag_event({"title": "AI"}) == []


def test_tagger_parses_valid_response():
    text = json.dumps(["ai", "workshop", "free"])
    tagger = GeminiTagger(api_key="x", session=_Session(_Response(_gemini_payload(text))))
    assert tagger.tag_event({"title": "AI"}) == ["ai", "workshop", "free"]


def test_tagger_truncates_to_max_tags():
    text = json.dumps([str(index) for index in range(10)])
    tagger = GeminiTagger(api_key="x", session=_Session(_Response(_gemini_payload(text))), max_tags=5)
    assert len(tagger.tag_event({"title": "AI"})) == 5


def test_tagger_uses_fallback_env_var_name(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GEMNINI_API_KEY", "fallback-key")
    tagger = GeminiTagger()
    assert tagger.is_available() is True


def test_tag_events_adds_tags_key_to_all_events():
    text = json.dumps(["ai"])
    tagger = GeminiTagger(api_key="x", session=_Session(_Response(_gemini_payload(text))))
    events = [{"title": "A"}, {"title": "B"}]
    tagged = tagger.tag_events(events)
    assert all("tags" in event for event in tagged)


def test_tags_persisted_and_retrieved_from_db(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()
    store.persist_run(
        source="web",
        fetched_at="2026-02-17T00:00:00+00:00",
        search_term="AI",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[
            {
                "title": "AI Summit",
                "url": "https://www.garysguide.com/events/1",
                "price": "FREE",
                "date": "2026-02-27",
                "tags": ["ai", "free"],
            }
        ],
    )
    events = store.fetch_events()
    assert events[0]["tags"] == ["ai", "free"]


def test_tags_empty_list_stored_as_empty_json_array(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()
    store.persist_run(
        source="web",
        fetched_at="2026-02-17T00:00:00+00:00",
        search_term="AI",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[
            {
                "title": "AI Summit",
                "url": "https://www.garysguide.com/events/1",
                "price": "FREE",
                "date": "2026-02-27",
                "tags": [],
            }
        ],
    )
    events = store.fetch_events()
    assert events[0]["tags"] == []


def test_tags_column_survives_schema_migration(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()
    store.init_schema()
    events = store.fetch_events()
    assert events == []


def test_tagging_disabled_via_config_flag(monkeypatch):
    class _Scraper:
        def get_events(self):
            return [{"title": "AI", "description": "AI", "date": "2026-02-27"}]

    from garys_nyc_events import runner_once as runner

    monkeypatch.setattr(runner, "_default_scraper", lambda _cfg: _Scraper())

    cfg = PipelineConfig(scraper_search_term="", tagging_enabled=False)
    events = _run_scrape(cfg)
    assert events[0]["tags"] == []
