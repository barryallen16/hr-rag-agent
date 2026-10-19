import json

import pytest

from database import relational as R


@pytest.fixture
def db(tmp_path, monkeypatch):
    p = tmp_path / "t.db"
    monkeypatch.setattr("config.SQL_DB_PATH", str(p))
    monkeypatch.setattr(R, "SQL_DB_PATH", str(p))
    R.init_relational_db()
    return str(p)

def test_submit_leave_ok(db):
    r = json.loads(R.submit_leave_request("EMP101", "casual", "2026-06-10", 2))
    assert r["status"] == "success"
    assert r["new_balance"] == 6

def test_insufficient(db):
    r = json.loads(R.submit_leave_request("EMP103", "medical", "2026-06-10", 5))
    assert r["status"] == "error"

def test_bad_date(db):
    r = json.loads(R.submit_leave_request("EMP101", "casual", "10-06-2026", 1))
    assert r["status"] == "error"

def test_unknown_type(db):
    r = json.loads(R.submit_leave_request("EMP101", "vacation", "2026-06-10", 1))
    assert r["status"] == "error"