"""Database layer for jobcli (SQLite).

The database file defaults to ~/.jobcli/jobcli.db, but can be overridden
by setting the environment variable JOBCLI_DB_PATH (absolute path).
"""

from __future__ import annotations

import csv
import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".jobcli" / "jobcli.db"


def get_db_path() -> Path:
    """Return DB path, honoring JOBCLI_DB_PATH if set."""
    return Path(os.getenv("JOBCLI_DB_PATH", str(DEFAULT_DB_PATH)))


def _connect() -> sqlite3.Connection:
    """Create a SQLite connection and ensure parent directory exists."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


@dataclass
class Application:
    id: int
    company: str
    role: str
    source: str | None
    status: str
    applied_date: str
    last_update: str
    notes: str | None


def init_db() -> None:
    """Create the database schema if it does not already exist."""
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
    source: str | None = None,
    status: str = "applied",
    applied_date: str | None = None,
    notes: str | None = None,
) -> int:
    """Insert a new application and return its ID."""
    applied = applied_date or date.today().isoformat()
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO applications (
                company, role, source, status,
                applied_date, last_update, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (company, role, source, status, applied, now, notes),
        )
        return int(cur.lastrowid)


def list_applications(
    status: str | None = None,
    limit: int | None = None,
    since: str | None = None,
) -> list[Application]:
    """Fetch applications; optional filters: status, since (YYYY-MM-DD), and limit."""
    query = "SELECT * FROM applications"
    clauses: list[str] = []
    params: list[object] = []

    if status:
        clauses.append("status = ?")
        params.append(status)
    if since:
        clauses.append("applied_date >= ?")
        params.append(since)

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [Application(**dict(r)) for r in rows]


def update_application(app_id: int, status: str, notes: str | None = None) -> bool:
    """Update status (and notes if provided). Returns True if a row was updated."""
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        if notes is None:
            cur = conn.execute(
                "UPDATE applications SET status = ?, last_update = ? WHERE id = ?",
                (status, now, app_id),
            )
        else:
            cur = conn.execute(
                "UPDATE applications SET status = ?, notes = ?, last_update = ? WHERE id = ?",
                (status, notes, now, app_id),
            )
        return cur.rowcount > 0


def update_status(app_id: int, status: str, notes: str | None = None) -> bool:
    """Backward-compat wrapper for tests; delegates to update_application."""
    return update_application(app_id, status, notes)


def get_stats() -> dict:
    """Return total and counts by status."""
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        by_status_rows = conn.execute(
            "SELECT status, COUNT(*) as c FROM applications GROUP BY status"
        ).fetchall()
    return {"total": total, "by_status": {r["status"]: r["c"] for r in by_status_rows}}


def stats() -> dict:
    """Compatibility wrapper for tests; returns overall stats."""
    return get_stats()


def export_csv(out_path: str | Path) -> int:
    """Export all records to CSV. Returns the number of rows written."""
    out = Path(out_path)
    with _connect() as conn, out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["id", "company", "role", "source", "status", "applied_date", "last_update", "notes"]
        )
        rows = conn.execute("SELECT * FROM applications ORDER BY id").fetchall()
        for r in rows:
            writer.writerow(
                [
                    r["id"],
                    r["company"],
                    r["role"],
                    r["source"],
                    r["status"],
                    r["applied_date"],
                    r["last_update"],
                    r["notes"],
                ]
            )
    return len(rows)


def search_applications(query: str, limit: int | None = None) -> list[Application]:
    """Return rows where query matches company, role, source, or notes."""
    like = f"%{query}%"
    sql = """
        SELECT * FROM applications
        WHERE company LIKE ?
           OR role LIKE ?
           OR IFNULL(source, '') LIKE ?
           OR IFNULL(notes, '') LIKE ?
        ORDER BY id DESC
    """
    with _connect() as conn:
        rows = conn.execute(sql, (like, like, like, like)).fetchall()
    apps = [Application(**dict(r)) for r in rows]
    return apps[:limit] if limit else apps


def delete_application(app_id: int) -> bool:
    """Delete an application by id. Returns True if a row was removed."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        return cur.rowcount > 0


def summary_last_n_days(days: int = 7) -> dict:
    """Return counts for applications applied in the last N days (default 7)."""
    since_date = (date.today() - timedelta(days=days)).isoformat()
    with _connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE applied_date >= ?", (since_date,)
        ).fetchone()[0]
        by_status_rows = conn.execute(
            "SELECT status, COUNT(*) as c FROM applications WHERE applied_date >= ? GROUP BY status",
            (since_date,),
        ).fetchall()

    by_status = {r["status"]: r["c"] for r in by_status_rows}
    return {"since": since_date, "days": days, "total": total, "by_status": by_status}
