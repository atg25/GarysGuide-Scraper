from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlsplit, urlunsplit

from .filters import filter_ai_events, filter_events_upcoming_week


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    search_term TEXT,
    record_limit INTEGER,
    status TEXT NOT NULL CHECK(status IN ('success', 'partial', 'failure')),
    fetched_count INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "all events" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    url TEXT,
    description TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    price TEXT,
    event_date TEXT,
    event_time TEXT,
    event_location TEXT,
    date_found TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weekly_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    all_event_id INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    url TEXT,
    description TEXT,
    tags TEXT,
    price TEXT,
    event_date TEXT,
    event_time TEXT,
    event_location TEXT,
    date_found TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(all_event_id) REFERENCES "all events"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runs_fetched_at ON runs(fetched_at);
CREATE INDEX IF NOT EXISTS idx_all_events_canonical_key ON "all events"(canonical_key);
CREATE INDEX IF NOT EXISTS idx_weekly_events_date ON weekly_events(event_date);
"""


@dataclass(frozen=True)
class RunRecord:
    run_id: int
    status: str
    fetched_count: int
    attempts: int
    error: str


class SQLiteEventStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON;")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def _normalize_url(self, url: str) -> str:
        cleaned = (url or "").strip()
        if not cleaned:
            return ""
        parsed = urlsplit(cleaned)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))

    def _canonical_key(self, event: Dict[str, str]) -> str:
        url = self._normalize_url(event.get("url") or "")
        title = (event.get("title") or "").strip().lower()
        if url:
            return f"url:{url}"
        return f"name:{title}"

    def _upsert_all_event(
        self,
        conn: sqlite3.Connection,
        event: Dict[str, str],
        *,
        date_found: str,
    ) -> int:
        key = self._canonical_key(event)
        name = (event.get("title") or "").strip() or "Untitled"
        url = self._normalize_url(event.get("url") or "") or None

        conn.execute(
            """
            INSERT INTO "all events" (
                canonical_key,
                name,
                url,
                description,
                tags,
                price,
                event_date,
                event_time,
                event_location,
                date_found
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_key) DO UPDATE SET
                name=excluded.name,
                url=COALESCE(excluded.url, "all events".url),
                description=excluded.description,
                tags=excluded.tags,
                price=excluded.price,
                event_date=excluded.event_date,
                event_time=excluded.event_time,
                event_location=excluded.event_location,
                date_found=excluded.date_found,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                key,
                name,
                url,
                event.get("description", ""),
                json.dumps(event.get("tags", []), ensure_ascii=False),
                event.get("price", ""),
                event.get("date", ""),
                event.get("time", ""),
                event.get("location", ""),
                date_found,
            ),
        )

        row = conn.execute('SELECT id FROM "all events" WHERE canonical_key = ?', (key,)).fetchone()
        if row is None:
            raise RuntimeError("Failed to resolve product id after upsert")
        return int(row["id"])

    def _refresh_weekly_events(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            '''
            SELECT
                id,
                name,
                url,
                description,
                tags,
                price,
                event_date,
                event_time,
                event_location,
                date_found
            FROM "all events"
            WHERE date(date_found) >= date('2026-02-27')
            '''
        ).fetchall()

        all_events = [
            {
                "id": row["id"],
                "title": row["name"] or "",
                "url": row["url"] or "",
                "description": row["description"] or "",
                "tags": json.loads(row["tags"] or "[]"),
                "price": row["price"] or "",
                "date": row["event_date"] or "",
                "time": row["event_time"] or "",
                "location": row["event_location"] or "",
                "date_found": row["date_found"] or "",
            }
            for row in rows
        ]

        weekly = filter_events_upcoming_week(all_events, today=date.today())

        conn.execute("DELETE FROM weekly_events")
        for event in weekly:
            conn.execute(
                """
                INSERT INTO weekly_events (
                    all_event_id,
                    name,
                    url,
                    description,
                    tags,
                    price,
                    event_date,
                    event_time,
                    event_location,
                    date_found
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(all_event_id) DO UPDATE SET
                    name=excluded.name,
                    url=excluded.url,
                    description=excluded.description,
                    tags=excluded.tags,
                    price=excluded.price,
                    event_date=excluded.event_date,
                    event_time=excluded.event_time,
                    event_location=excluded.event_location,
                    date_found=excluded.date_found
                """,
                (
                    event.get("id"),
                    event.get("title", ""),
                    event.get("url", ""),
                    event.get("description", ""),
                    json.dumps(event.get("tags", []), ensure_ascii=False),
                    event.get("price", ""),
                    event.get("date", ""),
                    event.get("time", ""),
                    event.get("location", ""),
                    event.get("date_found", datetime.now(timezone.utc).isoformat()),
                ),
            )

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
    ) -> RunRecord:
        event_list: List[Dict[str, str]] = list(events)
        with self._connect() as conn:
            conn.execute("BEGIN")
            cursor = conn.execute(
                """
                INSERT INTO runs (
                    source,
                    fetched_at,
                    search_term,
                    record_limit,
                    status,
                    fetched_count,
                    attempts,
                    error,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    source,
                    fetched_at,
                    search_term,
                    record_limit,
                    status,
                    len(event_list),
                    attempts,
                    error or "",
                ),
            )
            run_id = int(cursor.lastrowid)

            observed_at = datetime.now(timezone.utc).isoformat()
            for event in event_list:
                self._upsert_all_event(conn, event, date_found=observed_at)

            self._refresh_weekly_events(conn)

        return RunRecord(
            run_id=run_id,
            status=status,
            fetched_count=len(event_list),
            attempts=attempts,
            error=error or "",
        )

    def fetch_latest_run(self) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()

    def count_rows(self, table_name: str) -> int:
        aliases = {
            "all events": '"all events"',
            "all_events": '"all events"',
            "weekly_events": "weekly_events",
        }
        resolved = aliases.get(table_name, table_name)
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS count FROM {resolved}").fetchone()
            return int(row["count"]) if row else 0

    def fetch_events(self, *, limit: int = 0, ai_only: bool = False) -> List[Dict[str, str]]:
        query = """
            SELECT
                w.all_event_id AS id,
                w.name AS title,
                w.url AS url,
                w.description AS description,
                w.tags AS tags,
                w.price AS price,
                w.event_date AS date,
                w.event_time AS time,
                w.event_location AS location,
                '' AS topics,
                w.date_found AS date_found
            FROM weekly_events w
            ORDER BY w.event_date ASC, w.id ASC
        """
        params: List[object] = []
        if limit > 0:
            query += " LIMIT ?"
            params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        events = [
            {
                "id": row["id"],
                "title": row["title"] or "",
                "url": row["url"] or "",
                "description": row["description"] or "",
                "tags": json.loads(row["tags"] or "[]"),
                "price": row["price"] or "",
                "date": row["date"] or "",
                "time": row["time"] or "",
                "location": row["location"] or "",
                "topics": row["topics"] or "",
                "date_found": row["date_found"] or "",
            }
            for row in rows
        ]

        if ai_only:
            events = filter_ai_events(events)
        return events
