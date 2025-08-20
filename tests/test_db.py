from datetime import date, timedelta

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


def test_delete(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setenv("JOBCLI_DB_PATH", str(test_db))

    db.init_db()
    app_id = db.add_application(company="DeleteMe", role="Analyst")
    assert app_id >= 1

    ok = db.delete_application(app_id)
    assert ok is True

    rows = db.list_applications()
    assert len(rows) == 0


def test_list_since(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setenv("JOBCLI_DB_PATH", str(test_db))

    import jobcli.db as db

    db.init_db()

    older = (date.today() - timedelta(days=10)).isoformat()
    recent = (date.today() - timedelta(days=2)).isoformat()

    db.add_application(company="OldCo", role="Analyst", applied_date=older)
    db.add_application(company="NewCo", role="Engineer", applied_date=recent)

    since = (date.today() - timedelta(days=7)).isoformat()
    rows = db.list_applications(since=since)
    assert len(rows) == 1
    assert rows[0].company == "NewCo"


def test_summary_last_7(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setenv("JOBCLI_DB_PATH", str(test_db))

    import jobcli.db as db

    db.init_db()

    older = (date.today() - timedelta(days=9)).isoformat()
    recent = (date.today() - timedelta(days=1)).isoformat()

    db.add_application(company="OldCo", role="Analyst", applied_date=older, status="applied")
    db.add_application(company="NewCo1", role="Eng", applied_date=recent, status="applied")
    db.add_application(company="NewCo2", role="Eng", applied_date=recent, status="interview")

    s = db.summary_last_n_days(7)
    assert s["total"] == 2
    assert s["by_status"]["applied"] == 1
    assert s["by_status"]["interview"] == 1
