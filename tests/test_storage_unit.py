from garys_nyc_events.storage import SQLiteEventStore


def test_schema_creation(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))

    store.init_schema()

    assert store.count_rows("runs") == 0
    assert store.count_rows("products") == 0
    assert store.count_rows("product_snapshots") == 0


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
                "date": "Tue Feb 17",
            }
        ],
    )

    assert run.status == "success"
    assert run.fetched_count == 1
    assert store.count_rows("runs") == 1
    assert store.count_rows("products") == 1
    assert store.count_rows("product_snapshots") == 1


def test_dedupe_upsert_by_url(tmp_path):
    db_path = tmp_path / "events.db"
    store = SQLiteEventStore(str(db_path))
    store.init_schema()

    event = {
        "title": "AI Summit",
        "url": "https://www.garysguide.com/events/1",
        "price": "$10",
        "date": "Tue Feb 17",
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
    )

    assert store.count_rows("runs") == 2
    assert store.count_rows("products") == 1
    assert store.count_rows("product_snapshots") == 2


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
    )

    latest = store.fetch_latest_run()
    assert run.status == "failure"
    assert latest is not None
    assert latest["status"] == "failure"
    assert latest["error"] == "timeout"
    assert latest["attempts"] == 3
    assert store.count_rows("product_snapshots") == 0
