import json
import logging
import re
import sqlite3
import time
from pathlib import Path

from langchain_core.tools import tool
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------
# Logging: كل استدعاء أداة بينكتب بالشاشة وبملف tool_logs.log
# ---------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("tool_logs.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("tools")

# ---------------------------------------------------------------
# إعدادات
# ---------------------------------------------------------------
DB_PATH = "superstore.db"   # <-- بدّليه باسم ملف قاعدة البيانات الحقيقي
CHUNKS_PATH = "chunks.json"
MAX_ROWS = 50

# ---------------------------------------------------------------
# الأداة 1: search_documents (TF-IDF من الأسبوع 8)
# ---------------------------------------------------------------
with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    CHUNKS = json.load(f)

_vectorizer = TfidfVectorizer()
_matrix = _vectorizer.fit_transform([c["text"] for c in CHUNKS])


def retrieve_top_k(question, k=3):
    q_vec = _vectorizer.transform([question])
    sims = cosine_similarity(q_vec, _matrix)[0]
    idxs = sims.argsort()[::-1][:k]
    return [
        {"chunk": CHUNKS[i], "similarity_score": round(float(sims[i]), 4)}
        for i in idxs
    ]


@tool
def search_documents(question: str, k: int = 2) -> str:
    """Search the company documents (invoices, policies, FAQs, reports)
    and return the top-k most relevant chunks as JSON, each with its
    source document, document type, and similarity score.
    Use this for questions about policies, rules, invoices, or reports."""
    start = time.time()
    log.info(f"[search_documents] input: question={question!r}, k={k}")
    try:
        results = retrieve_top_k(question, k=k)
        output = [
            {
                "source": r["chunk"]["source_document"],
                "document_type": r["chunk"]["document_type"],
                "score": r["similarity_score"],
                "text": r["chunk"]["text"],
            }
            for r in results
        ]
        log.info(
            f"[search_documents] output: top={output[0]['source']} "
            f"score={output[0]['score']} ({time.time() - start:.2f}s)"
        )
        return json.dumps(output, ensure_ascii=False)
    except Exception as e:
        log.error(f"[search_documents] failed: {e}")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------
# الأداة 2: query_cost_table (SQLite من الأسبوع 6، SELECT فقط)
# ---------------------------------------------------------------
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum)\b",
    re.IGNORECASE,
)


def _is_safe_select(sql: str):
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        return False, "Only one statement is allowed."
    if not re.match(r"^(select|with)\b", s, re.IGNORECASE):
        return False, "Only SELECT queries are allowed."
    if FORBIDDEN.search(s):
        return False, "Query contains a forbidden keyword."
    return True, s


@tool
def query_cost_table(sql: str) -> str:
    """Run a read-only SQLite SELECT query on the Superstore sales database
    and return the rows as JSON (max 50 rows). Use this for numeric
    questions: totals, profits, margins, rankings, regions, categories.

    Tables/views (wrap names with spaces or hyphens in double quotes):
    - orders("Order ID","Order Date","Customer Name","Segment","Region",
      "Category","Sub-Category","Product Name","Sales","Quantity",
      "Discount","Profit",order_date_fixed)
    - category_group(Category, business_line)
    - category_summary(Category,total_sales,total_profit,overall_profit_margin)
    - subcategory_summary("Sub-Category",total_sales,total_profit,overall_profit_margin)
    - region_summary(Region,total_sales,total_profit,overall_profit_margin)
    Prefer the summary views when they answer the question."""
    start = time.time()
    log.info(f"[query_cost_table] input: sql={sql!r}")
    ok, result = _is_safe_select(sql)
    if not ok:
        log.warning(f"[query_cost_table] rejected: {result}")
        return json.dumps({"error": result})
    try:
        uri = Path(DB_PATH).resolve().as_uri() + "?mode=ro"  # قراءة فقط
        with sqlite3.connect(uri, uri=True) as conn:
            cur = conn.execute(result)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchmany(MAX_ROWS)
        log.info(
            f"[query_cost_table] output: {len(rows)} rows "
            f"({time.time() - start:.2f}s)"
        )
        return json.dumps({"columns": cols, "rows": rows}, ensure_ascii=False)
    except Exception as e:
        log.error(f"[query_cost_table] failed: {e}")
        return json.dumps({"error": str(e)})
    
    
import llm_functions as w9


@tool
def summarize_result(text: str) -> str:
    """Summarize a piece of text or a tool result (documents or SQL rows)
    into a short structured JSON with a summary and a key insight.
    Use this as the last step, after search_documents or query_cost_table."""
    start = time.time()
    log.info(f"[summarize_result] input: {len(text)} chars")
    try:
        result = w9.summarize_to_json(text)
        log.info(f"[summarize_result] output keys={list(result.keys())} "
                f"({time.time() - start:.2f}s)")
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        log.error(f"[summarize_result] failed: {e}")
        return json.dumps({"error": str(e), "fallback": True})