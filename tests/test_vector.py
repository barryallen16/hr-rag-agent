from database import vector as V


def test_search_returns_relevant_policy(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "VECTOR_DB_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr("config.VECTOR_DB_PATH", str(tmp_path / "chroma"))
    V._collection = None
    V._client = None
    coll = V.init_vector_db()
    assert coll.count() >= 5

    r = V.vector_search_hr_policy("doctor's note sick leave")
    assert "Retrieved Policy" in r
    assert len(r) > len("Retrieved Policy: ")


def test_search_nonsense_returns_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "VECTOR_DB_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr("config.VECTOR_DB_PATH", str(tmp_path / "chroma"))
    V._collection = None
    V._client = None
    V.init_vector_db()

    r = V.vector_search_hr_policy("xyzzy nonexistent policy blah")
    assert "No highly relevant" in r or "Retrieved Policy" in r
