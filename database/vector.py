import csv

from config import POLICIES_CSV_PATH, VECTOR_DB_PATH

_client = None
_collection = None


def _collection_handle():
    global _client, _collection
    import chromadb
    if _collection is None:
        _client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        _collection = _client.get_or_create_collection(name="hr_policies")
        if _collection.count() == 0:
            ids, metas, docs = [], [], []
            try:
                with open(POLICIES_CSV_PATH, newline="") as f:
                    for row in csv.DictReader(f):
                        ids.append(row["policy_id"])
                        metas.append({"topic": row["topic"]})
                        docs.append(row["policy_text"])
                _collection.add(documents=docs, metadatas=metas, ids=ids)
            except FileNotFoundError:
                print(f"Warning: {POLICIES_CSV_PATH} not found. Skipping vector data import.")
    return _collection


def init_vector_db():
    return _collection_handle()


def vector_search_hr_policy(query: str, n_results: int = 1) -> str:
    coll = _collection_handle()
    res = coll.query(query_texts=[query], n_results=n_results)
    docs = res.get("documents", [[]])[0]
    if docs:
        return "Retrieved Policy: " + docs[0]
    return "No highly relevant policy found. Advise user to contact HR."