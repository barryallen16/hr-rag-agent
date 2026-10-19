import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.orchestrator import run_agentic_workflow
from database.relational import init_relational_db
from database.vector import init_vector_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_relational_db()
    init_vector_db()
    yield


app = FastAPI(title="HR RAG Agent", version="0.1.0", lifespan=lifespan)
UI_DIR = Path(__file__).resolve().parent / "ui"
if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")

API_AUTH_KEY = os.getenv("API_AUTH_KEY", "")


def verify_key(x_api_key: str = Header(default="")):
    if API_AUTH_KEY and x_api_key != API_AUTH_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class QueryIn(BaseModel):
    query: str
    employee_id: str = "EMP101"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", dependencies=[Depends(verify_key)])
def query(q: QueryIn):
    return run_agentic_workflow(q.query, employee_id=q.employee_id)