from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


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

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    url TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    votes INTEGER,
    description TEXT,
    topics TEXT,
    price TEXT,
    event_date TEXT,
    observed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(run_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_fetched_at ON runs(fetched_at);
CREATE INDEX IF NOT EXISTS idx_products_canonical_key ON products(canonical_key);
CREATE INDEX IF NOT EXISTS idx_snapshots_run_id ON product_snapshots(run_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_product_id ON product_snapshots(product_id);
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
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def _canonical_key(self, event: Dict[str, str]) -> str:
        url = (event.get("url") or "").strip()
        title = (event.get("title") or "").strip().lower()
        if url:
            return f"url:{url}"
        return f"name:{title}"

    def _upsert_product(self, conn: sqlite3.Connection, event: Dict[str, str]) -> int:
        key = self._canonical_key(event)
        name = (event.get("title") or "").strip() or "Untitled"
        url = (event.get("url") or "").strip() or None

        conn.execute(
            """
            INSERT INTO products (canonical_key, name, url)
            VALUES (?, ?, ?)
            ON CONFLICT(canonical_key) DO UPDATE SET
                name=excluded.name,
                url=COALESCE(excluded.url, products.url),
                updated_at=CURRENT_TIMESTAMP
            """,
            (key, name, url),
        )

        row = conn.execute("SELECT id FROM products WHERE canonical_key = ?", (key,)).fetchone()
        if row is None:
            raise RuntimeError("Failed to resolve product id after upsert")
        return int(row["id"])

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
                product_id = self._upsert_product(conn, event)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO product_snapshots (
                        run_id,
                        product_id,
                        votes,
                        description,
                        topics,
                        price,
                        event_date,
                        observed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        product_id,
                        None,
                        event.get("title", ""),
                        search_term,
                        event.get("price", ""),
                        event.get("date", ""),
                        observed_at,
                    ),
                )

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
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
            return int(row["count"]) if row else 0
