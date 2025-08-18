"""Database layer for jobcli (SQLite).

The database file defaults to ~/.jobcli/jobcli.db, but can be overridden
by setting the environment variable JOBCLI_DB_PATH (absolute path).
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List, Optional

DEFAULT_DB_PATH = Path.home() / ".jobcli" / "jobcli.db"
DB_PATH = Path(os.getenv("JOBCLI_DB_PATH", str(DEFAULT_DB_PATH)))


@dataclass
class Application:
    id: int
    company: str
    role: str
    source: Optional[str]
    status: str
    applied_date: str
    last_update: str
    notes: Optional[str]


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                source TEXT,
                status TEXT NOT NULL,
                applied_date TEXT NOT NULL,
                last_update TEXT NOT NULL,
                notes TEXT
            )
            """
        )


def add_application(
    company: str,
    role: str,
    source: Optional[str] = None,
    status: str = "applied",
    applied_date: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """Insert a new application and return the new row id."""
    applied = applied_date or date.today().isoformat()
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO applications (company, role, source, status, applied_date, last_update, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (company, role, source, status, applied, now, notes),
        )
        return int(cur.lastrowid)


def list_applications(status: Optional[str] = None, limit: Optional[int] = None) -> List[Application]:
    """Fetch applications, optionally filtered by status and limited in count."""
    query = "SELECT * FROM applications"
    params: list = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [Application(**dict(r)) for r in rows]


def update_status(app_id: int, status: str, notes: Optional[str] = None) -> None:
    """Update status (and optionally notes) for a record by id."""
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        if notes is None:
            conn.execute(
                "UPDATE applications SET status = ?, last_update = ? WHERE id = ?",
                (status, now, app_id),
            )
        else:
            conn.execute(
                "UPDATE applications SET status = ?, last_update = ?, notes = ? WHERE id = ?",
                (status, now, notes, app_id),
            )


def export_csv(out_path: Path) -> int:
    """Export all applications to a CSV file and return the number of rows written."""
    import csv

    with _connect() as conn:
        rows = conn.execute("SELECT * FROM applications ORDER BY id ASC").fetchall()

    fieldnames = ["id", "company", "role", "source", "status", "applied_date", "last_update", "notes"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(dict(r))
    return len(rows)


def stats() -> dict:
    """Return basic stats: total, by status, applied_last_7_days."""
    from datetime import timedelta

    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        by_status = dict(
            conn.execute("SELECT status, COUNT(*) as c FROM applications GROUP BY status").fetchall()
        )

        seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
        last_7 = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE applied_date >= ?", (seven_days_ago,)
        ).fetchone()[0]

    # sqlite Row -> dict for by_status values
    by_status = {k: (v if isinstance(v, int) else v["c"]) for k, v in by_status.items()}
    return {"total": total, "by_status": by_status, "applied_last_7_days": last_7}
