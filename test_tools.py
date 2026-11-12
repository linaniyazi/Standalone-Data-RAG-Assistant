''' from week10_tools import search_documents

for q in ["What is the discount policy for furniture?",
        "What happens if a payment is late?",
        "Who needs to approve a 15% discount?"]:
    out = search_documents.invoke({"question": q, "k": 1})
    print(q, "->", out[:120], "\n")
    '''
    
from cmath import log
import json
from json import tool
import re
import sqlite3
from pathlib import Path
import time

DB_PATH = "superstore.db"   # <-- بدّليه باسم ملفك
MAX_ROWS = 50
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
    start =     time.time()
    log.info(f"[query_cost_table] input: sql={sql!r}")
    ok, result = _is_safe_select(sql)
    if not ok:
        log.warning(f"[query_cost_table] rejected: {result}")
        return json.dumps({"error": result})
    try:
        uri = Path(DB_PATH).resolve().as_uri() + "?mode=ro"   # قراءة فقط
        with sqlite3.connect(uri, uri=True) as conn:
            cur = conn.execute(result)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchmany(MAX_ROWS)
        log.info(f"[query_cost_table] output: {len(rows)} rows "
                f"({time.time()-start:.2f}s)")
        return json.dumps({"columns": cols, "rows": rows}, ensure_ascii=False)
    except Exception as e:
        log.error(f"[query_cost_table] failed: {e}")
        return json.dumps({"error": str(e)})
    
