import pytest
from fastapi.testclient import TestClient

import api
from api import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_query_requires_key(client, monkeypatch):
    monkeypatch.setattr("api.API_AUTH_KEY", "secret123")
    r = client.post("/query", json={"query": "How many casual leaves?"})
    assert r.status_code == 401


def test_query_with_key(client, monkeypatch):
    monkeypatch.setattr("api.API_AUTH_KEY", "secret123")
    monkeypatch.setattr(api, "run_agentic_workflow", lambda q, employee_id="": {"tools": [], "answer": "ok"})
    r = client.post("/query", json={"query": "How many casual leaves?"}, headers={"X-API-Key": "secret123"})
    assert r.status_code == 200
    assert r.json()["answer"] == "ok"


def test_multi_turn_session(client, monkeypatch):
    monkeypatch.setattr("api.API_AUTH_KEY", "secret123")
    calls = []
    def mock_run(q, employee_id=""):
        calls.append({"q": q})
        return {"tools": [], "answer": f"response-{len(calls)}"}
    monkeypatch.setattr(api, "run_agentic_workflow", mock_run)

    r1 = client.post("/query", json={"query": "Q1", "employee_id": "EMP1"}, headers={"X-API-Key": "secret123"})
    assert r1.status_code == 200
    assert r1.json()["answer"] == "response-1"

    r2 = client.post("/query", json={"query": "Q2", "employee_id": "EMP1"}, headers={"X-API-Key": "secret123"})
    assert r2.status_code == 200
    assert r2.json()["answer"] == "response-2"

    # Session history persisted in SQLite via orchestrator
    assert len(calls) == 2
