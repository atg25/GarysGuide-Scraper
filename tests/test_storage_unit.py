from datetime import date

import sqlite3

from garys_nyc_events.storage import SQLiteEventStore


def test_schema_creation(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))

    store.init_schema()

    assert store.count_rows("runs") == 0
    assert store.count_rows("all events") == 0
    assert store.count_rows("weekly_events") == 0


def test_successful_write_and_snapshot(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    run = store.persist_run(
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
            }
        ],
        today=date(2026, 2, 26),
    )

    assert run.status == "success"
    assert run.fetched_count == 1
    assert store.count_rows("runs") == 1
    assert store.count_rows("all events") == 1
    assert store.count_rows("weekly_events") == 1


def test_dedupe_upsert_by_url(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    event = {
        "title": "AI Summit",
        "url": "https://www.garysguide.com/events/1",
        "price": "$10",
        "date": "2026-02-27",
    }

    store.persist_run(
        source="web",
        fetched_at="2026-02-17T00:00:00+00:00",
        search_term="AI",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[event],
        today=date(2026, 2, 26),
    )

    store.persist_run(
        source="web",
        fetched_at="2026-02-17T06:00:00+00:00",
        search_term="AI",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[event],
        today=date(2026, 2, 26),
    )

    assert store.count_rows("runs") == 2
    assert store.count_rows("all events") == 1
    assert store.count_rows("weekly_events") == 1


def test_failed_run_persistence(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    run = store.persist_run(
        source="web",
        fetched_at="2026-02-17T00:00:00+00:00",
        search_term="",
        record_limit=0,
        status="failure",
        attempts=3,
        error="timeout",
        events=[],
        today=date(2026, 2, 26),
    )

    latest = store.fetch_latest_run()
    assert run.status == "failure"
    assert latest is not None
    assert latest["status"] == "failure"
    assert latest["error"] == "timeout"
    assert latest["attempts"] == 3
    assert store.count_rows("weekly_events") == 0


def test_schema_includes_time_and_location_columns(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    import sqlite3

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("PRAGMA table_info(weekly_events)").fetchall()
    finally:
        conn.close()

    names = {row[1] for row in rows}
    assert "event_time" in names
    assert "event_location" in names


def test_url_normalization_strips_query_params(tmp_path):
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
                "url": "https://www.garysguide.com/events/1?ref=email",
                "price": "FREE",
                "date": "2026-02-27",
            }
        ],
        today=date(2026, 2, 26),
    )
    store.persist_run(
        source="web",
        fetched_at="2026-02-17T01:00:00+00:00",
        search_term="AI",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[
            {
                "title": "AI Summit",
                "url": "https://www.garysguide.com/events/1?ref=social",
                "price": "FREE",
                "date": "2026-02-27",
            }
        ],
        today=date(2026, 2, 26),
    )

    assert store.count_rows("all events") == 1
    assert store.count_rows("weekly_events") == 1


def test_url_normalization_strips_fragment(tmp_path):
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
                "url": "https://www.garysguide.com/events/1#top",
                "price": "FREE",
                "date": "2026-02-27",
            }
        ],
        today=date(2026, 2, 26),
    )
    store.persist_run(
        source="web",
        fetched_at="2026-02-17T01:00:00+00:00",
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
            }
        ],
        today=date(2026, 2, 26),
    )

    assert store.count_rows("all events") == 1
    assert store.count_rows("weekly_events") == 1


def test_ten_runs_same_five_events_still_five_rows(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    events = [
        {
            "title": f"AI Event {index}",
            "url": f"https://www.garysguide.com/events/{index}",
            "price": "FREE",
            "date": "2026-02-27",
        }
        for index in range(5)
    ]

    for run_index in range(10):
        store.persist_run(
            source="web",
            fetched_at=f"2026-02-17T{run_index:02d}:00:00+00:00",
            search_term="AI",
            record_limit=10,
            status="success",
            attempts=1,
            error="",
            events=events,
            today=date(2026, 2, 26),
        )

    assert store.count_rows("all events") == 5
    assert store.count_rows("weekly_events") == 5


def test_fetch_events_returns_no_duplicates(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    for run_index in range(5):
        store.persist_run(
            source="web",
            fetched_at=f"2026-02-17T{run_index:02d}:00:00+00:00",
            search_term="AI",
            record_limit=10,
            status="success",
            attempts=1,
            error="",
            events=[
                {
                    "title": "AI One",
                    "url": "https://www.garysguide.com/events/1",
                    "price": "FREE",
                    "date": "2026-02-27",
                    "description": "AI talk",
                },
                {
                    "title": "AI Two",
                    "url": "https://www.garysguide.com/events/2",
                    "price": "FREE",
                    "date": "2026-02-27",
                    "description": "Machine learning workshop",
                },
            ],
            today=date(2026, 2, 26),
        )

    events = store.fetch_events()
    assert len(events) == 2
    assert len({event["url"] for event in events}) == 2


def test_fetch_events_ai_only_filters_correctly(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    store.persist_run(
        source="web",
        fetched_at="2026-02-17T00:00:00+00:00",
        search_term="",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[
            {
                "title": "NYC AI Summit",
                "url": "https://www.garysguide.com/events/1",
                "price": "FREE",
                "date": "2026-02-27",
                "description": "AI builders",
            },
            {
                "title": "ML Workshop",
                "url": "https://www.garysguide.com/events/2",
                "price": "FREE",
                "date": "2026-02-27",
                "description": "machine learning hands-on",
            },
            {
                "title": "Cooking Club",
                "url": "https://www.garysguide.com/events/3",
                "price": "FREE",
                "date": "2026-02-27",
                "description": "food meetup",
            },
        ],
        today=date(2026, 2, 26),
    )

    ai_events = store.fetch_events(ai_only=True)
    assert len(ai_events) == 2


def test_fetch_events_ai_only_returns_empty_for_no_matches(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    store.persist_run(
        source="web",
        fetched_at="2026-02-17T00:00:00+00:00",
        search_term="",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[
            {
                "title": "Cooking Club",
                "url": "https://www.garysguide.com/events/3",
                "price": "FREE",
                "date": "2026-02-27",
                "description": "food meetup",
            },
        ],
        today=date(2026, 2, 26),
    )

    assert store.fetch_events(ai_only=True) == []


def test_refresh_weekly_ignores_date_found_cutoff(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    store.persist_run(
        source="web",
        fetched_at="2026-02-17T00:00:00+00:00",
        search_term="",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[
            {
                "title": "AI Near-term",
                "url": "https://www.garysguide.com/events/10",
                "price": "FREE",
                "date": "2026-03-02",
                "description": "ai meetup",
            },
        ],
        today=date(2026, 2, 26),
    )

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            'UPDATE "all events" SET date_found = ?', ("1999-01-01T00:00:00+00:00",)
        )
        conn.commit()
    finally:
        conn.close()

    store.persist_run(
        source="web",
        fetched_at="2026-02-18T00:00:00+00:00",
        search_term="",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[],
        today=date(2026, 2, 26),
    )

    events = store.fetch_events(limit=0, ai_only=False)
    assert len(events) == 1
    assert events[0]["title"] == "AI Near-term"
