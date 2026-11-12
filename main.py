from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from db import create_connection, create_table, select_all
from file_utils import read_csv
from app import ask as assistant_ask

load_dotenv()

app = FastAPI(title="Data + RAG Assistant")

DB_NAME = os.getenv("DB_NAME", "costs.db")


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask_endpoint(req: AskRequest):
    """Answer a question about the sales data or the documents.
    Returns the route used, the SQL or document sources, and the answer."""
    return assistant_ask(req.question)


@app.get("/costs")
def get_all_costs():
    conn = create_connection(DB_NAME)
    create_table(conn)
    data = select_all(conn)
    conn.close()
    return {"data": data}
