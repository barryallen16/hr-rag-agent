from database import vector as V


def test_search(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "VECTOR_DB_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr("config.VECTOR_DB_PATH", str(tmp_path / "chroma"))
    # reset cached collection
    V._collection = None
    V._client = None
    coll = V.init_vector_db()
    assert coll.count() >= 5
    r = V.vector_search_hr_policy("doctor's note sick leave")
    assert "Retrieved Policy" in r or "No highly" in r