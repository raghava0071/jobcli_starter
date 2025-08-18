import os
from pathlib import Path

import jobcli.db as db


def test_happy_flow(tmp_path, monkeypatch):
    # Use a temporary DB for testing
    test_db = tmp_path / "test.db"
    monkeypatch.setenv("JOBCLI_DB_PATH", str(test_db))

    db.init_db()
    app_id = db.add_application(company="Acme", role="Analyst", source="LinkedIn")
    assert isinstance(app_id, int) and app_id >= 1

    rows = db.list_applications()
    assert len(rows) == 1
    assert rows[0].company == "Acme"

    db.update_status(app_id, "interview", notes="Phone screen done")
    rows2 = db.list_applications()
    assert rows2[0].status == "interview"
    assert "Phone screen" in (rows2[0].notes or "")

    s = db.stats()
    assert s["total"] == 1
    assert s["by_status"]["interview"] == 1

    out_csv = tmp_path / "out.csv"
    n = db.export_csv(out_csv)
    assert n == 1
    assert out_csv.exists()
