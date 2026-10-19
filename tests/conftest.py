import pytest

from agent import orchestrator
from database import relational as R


@pytest.fixture(autouse=True)
def seeded_db(tmp_path, monkeypatch):
    p = str(tmp_path / "hr.db")
    monkeypatch.setattr(R, "SQL_DB_PATH", p)
    monkeypatch.setattr(orchestrator, "SQL_DB_PATH", p)
    R.init_relational_db()
    yield
