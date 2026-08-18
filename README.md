# Standalone-Data-RAG-Assistant
internship project for digital future

## Week 1 Project — Data Foundation Setup

A simple project covering the basics of working with data: reading/writing files, SQLite, and a basic REST API.

## Contents
- `file_utils.py` — Read and write CSV and JSON files
- `db.py` — Create and interact with a SQLite database (insert, select, group by)
- `main.py` — Basic REST API using FastAPI
- `data/sample.csv` — Sample cost data for testing

## How to Run

1. Activate the virtual environment:
```bash
.venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install fastapi uvicorn python-dotenv
```

3. Run the server:
```bash
uvicorn main:app --reload
```

4. Open in your browser:
- `http://127.0.0.1:8000/health` — check that the server is running
- `http://127.0.0.1:8000/costs` — view data from the costs table
- `http://127.0.0.1:8000/docs` — auto-generated interactive API docs
