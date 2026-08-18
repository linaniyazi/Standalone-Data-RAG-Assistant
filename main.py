from fastapi import FastAPI
from dotenv import load_dotenv
import os

from db import create_connection, create_table, select_all
from file_utils import read_csv

load_dotenv()

app = FastAPI()

DB_NAME = os.getenv("DB_NAME", "costs.db")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/costs")
def get_all_costs():
    conn = create_connection(DB_NAME)
    create_table(conn)
    data = select_all(conn)
    conn.close()
    return {"data": data}