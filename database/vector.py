import chromadb
import csv
from config import VECTOR_DB_PATH, POLICIES_CSV_PATH

def init_vector_db():
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = chroma_client.get_or_create_collection(name="hr_policies")
    
    if collection.count() == 0:
        ids, metadatas, documents = [], [], []
        try:
            with open(POLICIES_CSV_PATH, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    ids.append(row['policy_id'])
                    metadatas.append({"topic": row['topic']})
                    documents.append(row['policy_text'])
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
        except FileNotFoundError:
            print(f"Warning: {POLICIES_CSV_PATH} not found. Skipping vector data import.")
            
    return collection

def vector_search_hr_policy(query: str) -> str:
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = chroma_client.get_or_create_collection(name="hr_policies")
    
    results = collection.query(
        query_texts=[query],
        n_results=1
    )
    if results['documents'] and results['documents'][0]:
        return f"Retrieved Policy: {results['documents'][0][0]}"
    return "No highly relevant policy found. Advise user to contact HR."