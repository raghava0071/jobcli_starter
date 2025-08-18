![CI](https://github.com/raghava0071/jobcli_starter/actions/workflows/ci.yml/badge.svg)

# jobcli — Job Application Tracker (CLI)

A simple, **beginner-friendly** Python command‑line tool to track your job applications using SQLite.
It includes tests, linting, pre-commit hooks, and GitHub Actions CI — perfect for your GitHub portfolio.

## Features
- Add, list, update job applications
- Quick stats (totals, by status, last 7 days)
- Export to CSV
- Zero external runtime dependencies (uses Python standard library)
- Dev tooling: pytest, black, ruff, pre-commit, CI

## Quickstart
```bash
# 1) Create & activate venv
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dev tools
pip install -r requirements-dev.txt

# 3) Run tests & linters
pytest -q
ruff check .
black --check .

# 4) Initialize your DB (stored at ~/.jobcli/jobcli.db by default)
python -m jobcli.cli init

# 5) Add an application
python -m jobcli.cli add --company "Acme Corp" --role "Data Analyst" --source "LinkedIn"

# 6) See your list
python -m jobcli.cli list

# 7) Update status
python -m jobcli.cli update --id 1 --status "interview" --notes "Phone screen booked"

# 8) Stats
python -m jobcli.cli stats

# 9) Export to CSV
python -m jobcli.cli export --out applications.csv
```
## CLI usage

```bash
jobcli init
jobcli add --company "Acme" --role "Data Analyst" --source "LinkedIn"
jobcli list
jobcli search --q "Analyst" --limit 5
jobcli update --id 1 --status interview --notes "Phone screen booked"
jobcli stats
jobcli export --out applications.csv


## CLI usage
```bash
jobcli init
jobcli add --company "Acme" --role "Data Analyst" --source "LinkedIn"
jobcli list
jobcli search --q "Analyst" --limit 5
jobcli update --id 1 --status interview --notes "Phone screen booked"
jobcli stats
jobcli export --out applications.csv


## Commands
- `init` — create the database if it doesn't exist
- `add` — add a new application
- `list` — list applications (filter by `--status` or limit by `--limit`)
- `update` — update status/notes for an application by ID
- `stats` — show totals and by-status breakdown
- `export` — export to CSV

## Dev scripts
```bash
make fmt     # Run black to format
make lint    # Run ruff
make test    # Run pytest
```

## Config / Paths
By default the database is stored at `~/.jobcli/jobcli.db`.
For testing or custom locations, set the environment variable `JOBCLI_DB_PATH` to an absolute file path.

## License
MIT
