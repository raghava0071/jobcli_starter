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


def cmd_search(args):
    rows = db.search_applications(query=args.q, limit=args.limit)
    _print_table(rows)


def cmd_delete(args):
    ok = db.delete_application(args.id)
    print("Deleted." if ok else f"No application with id={args.id}.")


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

    p_init = sub.add_parser("init", help="Initialize the database")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="Add a new application")
    p_add.add_argument("--company", required=True)
    p_add.add_argument("--role", required=True)
    p_add.add_argument(
        "--source", default=None, help="Where you found the job (LinkedIn, Indeed, referral...)"
    )
    p_add.add_argument(
        "--status", default="applied", help="applied|interview|offer|rejected|ghosted|withdrawn"
    )
    p_add.add_argument(
        "--applied-date", dest="applied_date", default=None, help="YYYY-MM-DD (defaults to today)"
    )
    p_add.add_argument("--notes", default=None)
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List applications")
    p_list.add_argument("--status", default=None)
    p_list.add_argument("--limit", type=int, default=None)
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", help="Search applications by text")
    p_search.add_argument(
        "--q", required=True, help="Search text (matches company, role, source, notes)"
    )
    p_search.add_argument("--limit", type=int, default=None)
    p_search.set_defaults(func=cmd_search)

    p_update = sub.add_parser("update", help="Update status/notes for a record")
    p_update.add_argument("--id", type=int, required=True, help="Application ID")
    p_update.add_argument("--status", required=True)
    p_update.add_argument("--notes", default=None)
    p_update.set_defaults(func=cmd_update)

    p_stats = sub.add_parser("stats", help="Show simple stats")
    p_stats.set_defaults(func=cmd_stats)

    p_export = sub.add_parser("export", help="Export all records to CSV")
    p_export.add_argument("--out", required=True, help="Output CSV path")
    p_export.set_defaults(func=cmd_export)

    p_delete = sub.add_parser("delete", help="Delete an application by ID")
    p_delete.add_argument("--id", type=int, required=True)
    p_delete.set_defaults(func=cmd_delete)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
