"""
Content calendar — SQLite tracking for themes, verses, and engagement scores.
Warns when the same verse or theme was used in the last 14 days.
"""

import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = Path("content_calendar.db")
DEDUP_WINDOW_DAYS = 14


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL,
            theme           TEXT NOT NULL,
            verse           TEXT NOT NULL,
            engagement_score REAL,
            status          TEXT DEFAULT 'pending_review',
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


class ContentCalendar:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db = db_path
        with _get_conn() as conn:
            _ensure_schema(conn)

    def check_duplicates(self, theme: str, verse: str, days: int = DEDUP_WINDOW_DAYS) -> Optional[str]:
        """
        Returns a warning string if the same verse or theme was used recently,
        or None if clear to proceed.
        """
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        with _get_conn() as conn:
            _ensure_schema(conn)

            verse_row = conn.execute(
                "SELECT date FROM entries WHERE verse = ? AND date >= ? ORDER BY date DESC LIMIT 1",
                (verse, cutoff),
            ).fetchone()
            if verse_row:
                return (
                    f"Verse '{verse}' was already used on {verse_row['date']} "
                    f"(within the last {days} days)."
                )

            theme_row = conn.execute(
                "SELECT date FROM entries WHERE theme = ? AND date >= ? ORDER BY date DESC LIMIT 1",
                (theme, cutoff),
            ).fetchone()
            if theme_row:
                return (
                    f"Theme '{theme}' was already used on {theme_row['date']} "
                    f"(within the last {days} days)."
                )

        return None

    def record(self, date: str, theme: str, verse: str, status: str = "approved") -> int:
        """Insert a new entry. Returns the new row id."""
        with _get_conn() as conn:
            _ensure_schema(conn)
            cursor = conn.execute(
                "INSERT INTO entries (date, theme, verse, status) VALUES (?, ?, ?, ?)",
                (date, theme, verse, status),
            )
            conn.commit()
            row_id = cursor.lastrowid
            logger.info("Calendar entry created: id=%d date=%s theme=%s verse=%s", row_id, date, theme, verse)
            return row_id

    def update_engagement(self, date: str, score: float) -> None:
        """Update engagement score for a given date (fill in manually after posting)."""
        with _get_conn() as conn:
            _ensure_schema(conn)
            conn.execute(
                "UPDATE entries SET engagement_score = ? WHERE date = ?",
                (score, date),
            )
            conn.commit()
            logger.info("Engagement score updated: date=%s score=%.2f", date, score)

    def show_recent(self, limit: int = 20) -> list[dict]:
        """Return the most recent entries as a list of dicts."""
        with _get_conn() as conn:
            _ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM entries ORDER BY date DESC LIMIT ?",
                (limit,),
            ).fetchall()

        entries = [dict(row) for row in rows]
        if entries:
            col_widths = {k: max(len(k), max(len(str(r[k] or "")) for r in entries)) for k in entries[0]}
            header = "  ".join(k.ljust(col_widths[k]) for k in col_widths)
            separator = "  ".join("-" * col_widths[k] for k in col_widths)
            print(header)
            print(separator)
            for row in entries:
                print("  ".join(str(row[k] or "").ljust(col_widths[k]) for k in col_widths))
        else:
            print("No entries yet.")
        return entries

    def get_used_verses(self, days: int = 90) -> list[str]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        with _get_conn() as conn:
            _ensure_schema(conn)
            rows = conn.execute(
                "SELECT verse FROM entries WHERE date >= ?", (cutoff,)
            ).fetchall()
        return [r["verse"] for r in rows]
