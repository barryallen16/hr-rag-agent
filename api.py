from fastapi import FastAPI
from pydantic import BaseModel

from agent.orchestrator import run_agentic_workflow
from database.relational import init_relational_db
from database.vector import init_vector_db

app = FastAPI(title="HR RAG Agent", version="0.1.0")


class QueryIn(BaseModel):
    query: str
    employee_id: str = "EMP101"


@app.on_event("startup")
def startup():
    init_relational_db()
    init_vector_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query(q: QueryIn):
    return run_agentic_workflow(q.query, employee_id=q.employee_id)