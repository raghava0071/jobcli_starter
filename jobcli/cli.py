"""Command-line interface for jobcli."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__, db


def _print_table(rows):
    if not rows:
        print("No records found.")
        return
    # Simple fixed-width formatting
    headers = ["id", "company", "role", "status", "applied_date", "last_update", "source", "notes"]
    data = [
        [
            str(r.id),
            r.company,
            r.role,
            r.status,
            r.applied_date,
            r.last_update,
            str(r.source or ""),
            str(r.notes or ""),
        ]
        for r in rows
    ]
    widths = [max(len(h), *(len(row[i]) for row in data)) for i, h in enumerate(headers)]
    fmt = "  ".join("{:" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in data:
        print(fmt.format(*row))


def cmd_init(args):
    db.init_db()
    print("Database initialized.")


def cmd_add(args):
    app_id = db.add_application(
        company=args.company,
        role=args.role,
        source=args.source,
        status=args.status,
        applied_date=args.applied_date,
        notes=args.notes,
    )
    print(f"Added application with id={app_id}.")


def cmd_list(args):
    rows = db.list_applications(status=args.status, limit=args.limit)
    _print_table(rows)


def cmd_update(args):
    db.update_status(app_id=args.id, status=args.status, notes=args.notes)
    print(f"Updated application id={args.id}.")


def cmd_stats(args):
    s = db.stats()
    print("Total:", s["total"])
    print("Applied last 7 days:", s["applied_last_7_days"])
    print("By status:")
    for k, v in sorted(s["by_status"].items()):
        print(f"  {k}: {v}")


def cmd_export(args):
    out = Path(args.out)
    n = db.export_csv(out)
    print(f"Wrote {n} rows to {out}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jobcli", description="Track job applications from the terminal."
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="Initialize the database")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("add", help="Add a new application")
    s.add_argument("--company", required=True)
    s.add_argument("--role", required=True)
    s.add_argument(
        "--source", default=None, help="Where you found the job (LinkedIn, Indeed, referral...)"
    )
    s.add_argument(
        "--status", default="applied", help="applied|interview|offer|rejected|ghosted|withdrawn"
    )
    s.add_argument(
        "--applied-date", dest="applied_date", default=None, help="YYYY-MM-DD (defaults to today)"
    )
    s.add_argument("--notes", default=None)
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("list", help="List applications")
    s.add_argument("--status", default=None)
    s.add_argument("--limit", type=int, default=None)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("update", help="Update status/notes for a record")
    s.add_argument("--id", type=int, required=True, help="Application ID")
    s.add_argument("--status", required=True)
    s.add_argument("--notes", default=None)
    s.set_defaults(func=cmd_update)

    s = sub.add_parser("stats", help="Show simple stats")
    s.set_defaults(func=cmd_stats)

    s = sub.add_parser("export", help="Export all records to CSV")
    s.add_argument("--out", required=True, help="Output CSV path")
    s.set_defaults(func=cmd_export)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
